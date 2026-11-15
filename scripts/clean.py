# AI-assisted: generated with Claude (Anthropic)
"""Adım 22: temizle ve birleştir.

Arşiv dosyaları (regions.json -> archive) ve API parçaları (data/raw/<bölge>/<KAYNAK>/)
veri sözleşmesindeki A. tespit tablosuna çevrilir:
  data/processed/<bölge>/detections.parquet
Özet: data/processed/<bölge>/clean_summary.json ve ekrana tablo.

Hiçbir satır filtre yüzünden silinmez; işaret sütunları eklenir (sözleşme K4).
keep = Orta filtre (adım 28, docs/filters.md, kod: scripts/filters.py).
Silinen tek şey tekrarlardır (aynı uydu+gün için SP varsa NRT; aynı tespit iki kez).

Kullanım: python scripts/clean.py --region turkiye
"""
import json
from datetime import date

import numpy as np
import pandas as pd

from common import DATA_PROCESSED, DATA_RAW, ROOT, load_region, region_parser
from filters import MASK_CELL, MASK_MIN_DAYS, MASK_R_MODIS, MASK_R_VIIRS, build_mask, in_mask

SAT_MAP = {"Terra": "Terra", "Aqua": "Aqua", "T": "Terra", "A": "Aqua",
           "N": "SNPP", "SNPP": "SNPP", "N20": "NOAA20", "NOAA20": "NOAA20"}
# Arşiv VIIRS dosyasında instrument = 'SNPP' yazıyor; sensör uydudan çıkarılır.
SENSOR_OF = {"Terra": "MODIS", "Aqua": "MODIS", "SNPP": "VIIRS", "NOAA20": "VIIRS"}
SNPP_LAST = pd.Timestamp("2026-10-31")    # K1: S-NPP bu tarihe kadar
NOAA20_FIRST = pd.Timestamp("2026-11-01")  # K1: NOAA-20 bu tarihten itibaren
SNPP_FIRST_MONTH = pd.Timestamp("2012-02-01")  # K2: Ocak 2012 MODIS'ten ('M')
MODIS_V61_FROM = pd.Timestamp("2023-01-01")    # arşivde sürüm etiketi 6.03 -> 61.03


# ---------- okuma ----------

def read_raw(path, source, origin):
    df = pd.read_csv(path, dtype=str)
    if df.empty:
        return df
    df["source"] = source
    df["origin"] = origin
    return df


def load_all(region):
    frames = []
    arch = region.get("archive", {})
    for src in ("MODIS_SP", "VIIRS_SNPP_SP"):
        if src in arch:
            frames.append(read_raw(DATA_RAW / arch[src], src, "archive"))
    api_root = DATA_RAW / region["name"]
    files = 0
    for folder in sorted(p for p in api_root.iterdir() if p.is_dir()):
        for f in sorted(folder.glob("*.csv")):
            files += 1
            frames.append(read_raw(f, folder.name, "api"))
    frames = [f for f in frames if not f.empty]
    raw = pd.concat(frames, ignore_index=True)
    return raw, files


# ---------- ülke maskesi ----------

def load_polygons(mask, bbox=None):
    """'country:<ISO3>' -> data/boundaries/<ISO3>.geojson (tek ülke).
    'land:<dosya>'   -> data/boundaries/<dosya>.geojson (Natural Earth kara), yalnızca kutuya değen halkalar."""
    kind, name = mask.split(":", 1)
    g = json.loads((ROOT / "data" / "boundaries" / f"{name}.geojson").read_text(encoding="utf-8"))
    polys = []
    for feat in (g["features"] if kind == "land" else g["features"][:1]):
        geom = feat["geometry"]
        polys += geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    if bbox is not None:
        def touches(poly):
            r = np.asarray(poly[0])
            return not (r[:, 0].max() < bbox["west"] or r[:, 0].min() > bbox["east"]
                        or r[:, 1].max() < bbox["south"] or r[:, 1].min() > bbox["north"])
        polys = [p for p in polys if touches(p)]
    return polys


def points_in_polygons_sorted(lon, lat, polys):
    """points_in_polygons ile aynı kural (çift-tek, delikler dahil); büyük kara poligonları için hızlı:
    noktalar enleme göre sıralanır, her kenar yalnızca kendi enlem aralığındaki noktalara bakar."""
    lon, lat = np.asarray(lon, float), np.asarray(lat, float)
    order = np.argsort(lat, kind="stable")
    ys, xs = lat[order], lon[order]
    lo_y, hi_y = ys.min() if len(ys) else 0, ys.max() if len(ys) else 0
    inside = np.zeros(len(lon), dtype=bool)
    for poly in polys:
        c = np.zeros(len(ys), dtype=bool)
        for ring in poly:
            r = np.asarray(ring, float)
            x1, y1, x2, y2 = r[:-1, 0], r[:-1, 1], r[1:, 0], r[1:, 1]
            ymin, ymax = np.minimum(y1, y2), np.maximum(y1, y2)
            use = (ymax > lo_y) & (ymin <= hi_y) & (y1 != y2)
            # (y1 > y) != (y2 > y)  <=>  ymin <= y < ymax
            a = np.searchsorted(ys, ymin[use], side="left")
            b = np.searchsorted(ys, ymax[use], side="left")
            for k, s, e in zip(np.where(use)[0], a, b):
                if s == e:
                    continue
                yy = ys[s:e]
                xc = x1[k] + (yy - y1[k]) * (x2[k] - x1[k]) / (y2[k] - y1[k])
                c[s:e] ^= xs[s:e] < xc
        inside |= c
    out = np.zeros(len(lon), dtype=bool)
    out[order] = inside
    return out


def points_in_polygons(lon, lat, polys):
    """Çift-tek (ray casting) kuralı; delikler (iç halkalar) de sayılır."""
    inside = np.zeros(len(lon), dtype=bool)
    for poly in polys:
        ring0 = np.asarray(poly[0])
        bb = ((lon >= ring0[:, 0].min()) & (lon <= ring0[:, 0].max()) &
              (lat >= ring0[:, 1].min()) & (lat <= ring0[:, 1].max()))
        if not bb.any():
            continue
        x, y = lon[bb], lat[bb]
        c = np.zeros(len(x), dtype=bool)
        for ring in poly:
            r = np.asarray(ring)
            x1, y1 = r[:-1, 0], r[:-1, 1]
            x2, y2 = r[1:, 0], r[1:, 1]
            for k in range(len(x1)):
                cond = (y1[k] > y) != (y2[k] > y)
                if not cond.any():
                    continue
                xc = x1[k] + (y[cond] - y1[k]) * (x2[k] - x1[k]) / (y2[k] - y1[k])
                hit = np.zeros(len(x), dtype=bool)
                hit[cond] = x[cond] < xc
                c ^= hit
        inside[np.where(bb)[0][c]] = True
    return inside


# ---------- sözleşmeye çevirme ----------

def to_contract(raw):
    out = pd.DataFrame()
    out["acq_date"] = pd.to_datetime(raw["acq_date"]).dt.date
    out["acq_time"] = raw["acq_time"].str.strip().str.zfill(4)
    out["latitude"] = raw["latitude"].astype(float)
    out["longitude"] = raw["longitude"].astype(float)
    out["satellite"] = raw["satellite"].map(SAT_MAP)  # N21 ve bilinmeyen -> NaN
    out["sensor"] = out["satellite"].map(SENSOR_OF)
    out["confidence_raw"] = raw["confidence"].astype(str)
    conf_num = pd.to_numeric(raw["confidence"], errors="coerce")
    cls = pd.Series(pd.NA, index=raw.index, dtype="object")
    is_modis = out["sensor"] == "MODIS"
    cls[is_modis] = pd.cut(conf_num[is_modis], [-1, 29, 79, 100],
                           labels=["low", "nominal", "high"]).astype(str)
    cls[~is_modis] = raw.loc[~is_modis, "confidence"].str.lower().map(
        {"l": "low", "n": "nominal", "h": "high"})
    out["confidence_class"] = cls
    frp = pd.to_numeric(raw["frp"], errors="coerce")
    out["frp"] = frp.where(frp > 0)
    out["daynight"] = raw["daynight"]
    out["type"] = pd.to_numeric(raw.get("type"), errors="coerce").astype("Int64")
    # Parlaklık: arşiv VIIRS dosyası da 'brightness'/'bright_t31' adlarını kullanıyor.
    mir = raw["bright_ti4"] if "bright_ti4" in raw else pd.Series(np.nan, index=raw.index)
    tir = raw["bright_ti5"] if "bright_ti5" in raw else pd.Series(np.nan, index=raw.index)
    out["bright_mir"] = pd.to_numeric(mir.fillna(raw["brightness"]), errors="coerce")
    out["bright_tir"] = pd.to_numeric(tir.fillna(raw["bright_t31"]), errors="coerce")
    out["scan"] = pd.to_numeric(raw["scan"], errors="coerce")
    out["track"] = pd.to_numeric(raw["track"], errors="coerce")
    out["source"] = raw["source"]
    out["is_nrt"] = raw["source"].str.endswith("_NRT")
    # Yeni alanlar (sözleşmeye eklenebilir alanlar)
    out["origin"] = raw["origin"]
    out["version"] = raw["version"].astype(str)
    return out


def add_flags(df, region, polys):
    dt = pd.to_datetime(df["acq_date"])
    # 1) Ülke sınırı: arşiv zaten FIRMS ülke sınırıyla kesilmiş -> True kabul edilir.
    #    API (kutu) verisi Natural Earth sınırıyla kesilir.
    df["in_country"] = True
    if polys is not None and region["mask"].startswith("land:"):
        # Kutu bölgesi: arşiv de kutu olarak geldi, tüm satırlar kara poligonlarıyla test edilir.
        df["in_country"] = points_in_polygons_sorted(df["longitude"].to_numpy(), df["latitude"].to_numpy(), polys)
    elif polys is not None:
        api = (df["origin"] == "api").to_numpy()
        df.loc[api, "in_country"] = points_in_polygons(
            df.loc[api, "longitude"].to_numpy(), df.loc[api, "latitude"].to_numpy(), polys)
    # 2) Uydu geçiş kuralı (K1, K2): bu satır uyumlu serinin VIIRS ayağına girer mi?
    sat = df["satellite"]
    df["in_series"] = True
    df.loc[(sat == "SNPP") & ((dt > SNPP_LAST) | (dt < SNPP_FIRST_MONTH)), "in_series"] = False
    df.loc[(sat == "NOAA20") & (dt < NOAA20_FIRST), "in_series"] = False  # yalnızca k_N20 için
    # 3) MODIS sürüm etiketi değişimi
    df["modis_v61_label"] = (df["sensor"] == "MODIS") & df["version"].str.startswith("61")
    # 4) Adım 28 için bilgi işaretleri (henüz keep'e girmez)
    df["flag_low_conf"] = df["confidence_class"] == "low"
    df["flag_static"] = df["type"].isin([1, 2]).fillna(False).astype(bool)
    df["flag_offshore"] = (df["type"] == 3).fillna(False).astype(bool)
    df["flag_no_type"] = df["type"].isna()
    df["flag_bad_value"] = df["frp"].isna() | (df["bright_tir"] <= 0)
    # 5) NRT konum maskesi (adım 28): type alanı olmayan satırlar için.
    sp = df[df["type"].notna()]
    mask_cells = build_mask(sp)
    df["flag_mask"] = False
    nt = df["type"].isna().to_numpy()
    df.loc[nt, "flag_mask"] = in_mask(df.loc[nt], mask_cells)
    # keep (K4, Orta filtre): sınır içi ve hiçbir filtre işareti yok.
    df["keep"] = (df["in_country"].astype(bool) & ~df["flag_static"] & ~df["flag_offshore"]
                  & ~df["flag_low_conf"].fillna(False).astype(bool) & ~df["flag_mask"])
    return df, mask_cells


def dedupe(df):
    n0 = len(df)
    # Aynı uydu ve gün için SP varsa NRT atılır.
    sp_days = set(map(tuple, df.loc[~df["is_nrt"], ["satellite", "acq_date"]].drop_duplicates().to_numpy()))
    nrt_dup = df["is_nrt"] & pd.Series(
        [(s, d) in sp_days for s, d in zip(df["satellite"], df["acq_date"])], index=df.index)
    df = df[~nrt_dup]
    n1 = len(df)
    # Aynı tespit iki kez: arşiv önce gelsin.
    df = df.sort_values("origin").drop_duplicates(
        ["satellite", "acq_date", "acq_time", "latitude", "longitude"], keep="first")
    return df, n0 - n1, n1 - len(df)


def main():
    a = region_parser("Temizle ve birleştir (adım 22)").parse_args()
    region = load_region(a.region)
    raw, nfiles = load_all(region)
    print(f"Okunan: {len(raw)} satır ({nfiles} API dosyası + arşiv)")

    df = to_contract(raw)
    unknown_sat = int(df["satellite"].isna().sum())
    df = df[df["satellite"].notna()]
    df, nrt_dropped, dup_dropped = dedupe(df)
    early_dropped = 0
    if region.get("modis_first_date"):
        early = (df["sensor"] == "MODIS") & (pd.to_datetime(df["acq_date"]) < pd.Timestamp(region["modis_first_date"]))
        early_dropped = int(early.sum())
        df = df[~early]

    polys = load_polygons(region["mask"], region["bbox"]) if region.get("mask") else None
    df, mask_cells = add_flags(df, region, polys)

    # Sınır uyumu kontrolü: arşiv noktalarının kaçı Natural Earth sınırının içinde?
    arch = df["origin"] == "archive"
    arch_in = None
    if polys is not None and arch.any() and region["mask"].startswith("land:"):
        arch_in = float(df.loc[arch, "in_country"].mean())
    elif polys is not None and arch.any():
        arch_in = float(points_in_polygons(df.loc[arch, "longitude"].to_numpy(),
                                           df.loc[arch, "latitude"].to_numpy(), polys).mean())

    df = df.sort_values(["acq_date", "acq_time", "satellite"]).reset_index(drop=True)
    out_dir = DATA_PROCESSED / region["name"]
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_dir / "detections.parquet", index=False)
    (out_dir / "static_mask.json").write_text(json.dumps({
        "generated": date.today().isoformat(),
        "rule": "0.01 deg cells with archived type 2/3 detections on >= min_days distinct days; "
                "VIIRS: own cell, MODIS: own cell + 8 neighbours (docs/filters.md section 4)",
        "cell_deg": MASK_CELL, "min_days": MASK_MIN_DAYS,
        "r_viirs": MASK_R_VIIRS, "r_modis": MASK_R_MODIS,
        "cell_id": "floor(lat/cell_deg)*100000 + floor((lon+180)/cell_deg)",
        "cells": [int(c) for c in mask_cells],
    }), encoding="utf-8")

    # Özet
    df["year"] = pd.to_datetime(df["acq_date"]).dt.year
    by_src = (df.groupby(["source", "origin"])
              .agg(rows=("keep", "size"), in_country=("in_country", "sum"),
                   first=("acq_date", "min"), last=("acq_date", "max")).reset_index())
    by_year = df[df["keep"]].pivot_table(index="year", columns="satellite", values="keep",
                                         aggfunc="size", fill_value=0)
    inc = df["in_country"]
    flags = {c: int(df.loc[inc, c].fillna(False).astype(bool).sum()) for c in
             ["flag_low_conf", "flag_static", "flag_offshore", "flag_no_type", "flag_mask",
              "flag_bad_value", "modis_v61_label"]}
    series = df[df["keep"]].groupby(["satellite", "in_series"]).size().unstack(fill_value=0)
    summary = {
        "generated": date.today().isoformat(),
        "rows_read": int(len(raw)), "unknown_satellite_dropped": unknown_sat,
        "nrt_dropped_sp_exists": int(nrt_dropped), "duplicates_dropped": int(dup_dropped),
        "modis_before_first_date_dropped": early_dropped,
        "rows_out": int(len(df)), "rows_keep": int(df["keep"].sum()),
        "archive_points_inside_natural_earth_border": arch_in,
        "by_source": json.loads(by_src.to_json(orient="records", date_format="iso")),
        "by_year_keep": {str(k): v for k, v in by_year.to_dict(orient="index").items()},
        "flags_among_in_country": flags, "static_mask_cells": int(len(mask_cells)),
        "in_series_by_satellite": {k: {str(kk): int(vv) for kk, vv in v.items()}
                                   for k, v in series.to_dict(orient="index").items()},
    }
    (out_dir / "clean_summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False),
                                                encoding="utf-8")
    print(by_src.to_string(index=False))
    print("\nYıllık (keep=True):\n" + by_year.to_string())
    print("\nİşaretler (sınır içinde):", flags, "| maske hücresi:", len(mask_cells))
    print("Seri işareti:\n" + series.to_string())
    print(f"\nTekrar atılan: NRT {nrt_dropped}, kopya {dup_dropped}; bilinmeyen uydu {unknown_sat}; erken MODIS {early_dropped}")
    print(f"Arşiv noktalarının Natural Earth sınırı içinde kalma oranı: {arch_in:.4f}" if arch_in else "")
    print(f"Yazıldı: {out_dir / 'detections.parquet'} ({len(df)} satır, keep {int(df['keep'].sum())})")


if __name__ == "__main__":
    main()
