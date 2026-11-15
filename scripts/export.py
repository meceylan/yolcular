# AI-assisted: generated with Claude (Anthropic)
"""Adım 24 / 29 / 33: web verisi (veri sözleşmesi C bölümü).

Kipler:
  --mode harmonized (varsayılan, adım 33) -> web/data/  (sayfanın okuduğu sürüm)
      `h` = uyumlu değer (VIIRS S-NPP eşdeğeri), data/processed/<bölge>/harmonized_daily.parquet
      toplamı (katsayı harmonize.py'de uygulanmış). `m`, `v` filtreli ham sayılar.
      Ek alanlar: `h_lo`, `h_hi`, `out_of_range` (harmonized_monthly.csv, adım 31).
  --mode filtered  adım 28 filtresi, uyumlaştırma yok -> web/data_filtered/
  --mode raw       filtre yok, yalnızca ülke sınırı (s0 sürümü) -> web/data_raw/
monthly.json'da `gap_days`: serinin o ayki uydusunun veri vermediği gün sayısı.

Kullanım: python scripts/export.py --region turkiye [--mode harmonized|filtered|raw] [--out KLASÖR]
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from common import DATA_PROCESSED, ROOT, load_region, region_parser
from filters import FILTER_TEXT, gap_days_by_month

OUT_DIRS = {"harmonized": ROOT / "web" / "data", "filtered": ROOT / "web" / "data_filtered",
            "raw": ROOT / "web" / "data_raw"}
GAP_KEY = {"M": "MODIS", "V": "SNPP", "N": "NOAA20"}
SNPP_FIRST_MONTH = "2012-02"
NOAA20_FIRST_MONTH = "2026-11"
ACK = ("We acknowledge the use of data and/or imagery from NASA's Fire Information for "
       "Resource Management System (FIRMS) (https://earthdata.nasa.gov/firms), part of "
       "NASA's Land, Atmosphere Near real-time Capability for Earth observations (LANCE) "
       "(https://earthdata.nasa.gov/lance) and NASA's Earth Science Data and Information System (ESDIS).")
GRID_MAX_BYTES = 5_000_000


def src_of(month):
    if month < SNPP_FIRST_MONTH:
        return "M"
    if month < NOAA20_FIRST_MONTH:
        return "V"
    return "N"


def load(region, mode):
    row_ok = "in_country" if mode == "raw" else "keep"
    cols = ["acq_date", "latitude", "longitude", "sensor", "satellite", "in_series", row_ok]
    df = pd.read_parquet(DATA_PROCESSED / region["name"] / "detections.parquet", columns=cols)
    df = df[df[row_ok]]
    dt = pd.to_datetime(df["acq_date"])
    df["month"] = dt.dt.strftime("%Y-%m")
    df["year"] = dt.dt.year
    df["mon"] = dt.dt.month
    df["day"] = dt.dt.day
    df["date"] = dt
    # Kim hangi seriye sayılır: MODIS hepsi; VIIRS yalnızca in_series (S-NPP→NOAA-20 geçişi).
    df["is_m"] = df["sensor"] == "MODIS"
    df["is_v"] = (df["sensor"] == "VIIRS") & df["in_series"]
    return df[df["is_m"] | df["is_v"]]


def h_raw(m, v):
    """v0: uyumlu değer yok; VIIRS varsa VIIRS, yoksa MODIS (ham)."""
    return float(v) if v is not None else float(m)


def build_monthly(df, first_month, data_through):
    last = data_through.strftime("%Y-%m")
    months = pd.period_range(first_month, last, freq="M").strftime("%Y-%m").tolist()
    upto = df[df["date"] <= data_through]
    m = upto[upto["is_m"]].groupby("month").size()
    v = upto[upto["is_v"]].groupby("month").size()
    partial_last = data_through != (data_through + pd.offsets.MonthEnd(0))

    gaps = {k: gap_days_by_month(g) for k, g in GAP_KEY.items()}
    out = {"months": months, "src": [], "partial": [], "h": [], "m": [], "v": [], "gap_days": []}
    for mo in months:
        s = src_of(mo)
        out["gap_days"].append(int(gaps[s].get(mo, 0)))
        mv = int(m.get(mo, 0))
        vv = None if s == "M" else int(v.get(mo, 0))
        out["src"].append(s)
        out["partial"].append(bool(partial_last and mo == last))
        out["m"].append(mv)
        out["v"].append(vv)
        out["h"].append(h_raw(mv, vv))

    if partial_last:
        D = data_through.day
        cal_month = data_through.month
        sub = upto[(upto["mon"] == cal_month) & (upto["day"] <= D)]
        years = [y for y in range(int(first_month[:4]), data_through.year + 1)
                 if f"{y}-{cal_month:02d}" >= first_month]
        mm = sub[sub["is_m"]].groupby("year").size()
        vv_ = sub[sub["is_v"]].groupby("year").size()
        mtd = {"month": last, "through_day": D, "years": years, "src": [], "h": [], "m": [], "v": []}
        for y in years:
            s = src_of(f"{y}-{cal_month:02d}")
            a = int(mm.get(y, 0))
            b = None if s == "M" else int(vv_.get(y, 0))
            mtd["src"].append(s)
            mtd["m"].append(a)
            mtd["v"].append(b)
            mtd["h"].append(h_raw(a, b))
        out["mtd"] = mtd
    return out


def build_grid(df, monthly, cell, data_through):
    months = monthly["months"]
    midx = {m: i for i, m in enumerate(months)}
    upto = df[df["date"] <= data_through].copy()
    upto["i"] = np.floor((upto["latitude"] + 90) / cell).astype(int)
    upto["j"] = np.floor((upto["longitude"] + 180) / cell).astype(int)

    def cells_from(frame, key, index_of, src_for):
        g = frame.groupby(["i", "j", key]).agg(m=("is_m", "sum"), v=("is_v", "sum")).reset_index()
        cells = {}
        for r in g.itertuples(index=False):
            k = getattr(r, key)
            if k not in index_of:
                continue
            s = src_for(k)
            mv, vv = int(r.m), (None if s == "M" else int(r.v))
            if mv == 0 and not vv:
                continue
            cells.setdefault((r.i, r.j), []).append([index_of[k], h_raw(mv, vv), mv, vv])
        return [{"i": int(i), "j": int(j), "d": sorted(d)} for (i, j), d in sorted(cells.items())]

    grid = {"cell_deg": cell, "months": months,
            "cells": cells_from(upto, "month", midx, src_of)}
    if "mtd" in monthly:
        mt = monthly["mtd"]
        cal = int(mt["month"][5:])
        sub = upto[(upto["mon"] == cal) & (upto["day"] <= mt["through_day"])]
        yidx = {y: i for i, y in enumerate(mt["years"])}
        grid["mtd"] = {"month": mt["month"], "through_day": mt["through_day"], "years": mt["years"],
                       "cells": cells_from(sub, "year", yidx, lambda y: src_of(f"{y}-{cal:02d}"))}
    return grid


# ---------- uyumlu seri (adım 33) ----------

def load_harmonized(region, data_through):
    base = DATA_PROCESSED / region["name"]
    hd = pd.read_parquet(base / "harmonized_daily.parquet")
    hd["date"] = pd.to_datetime(hd["acq_date"])
    hd = hd[hd["date"] <= data_through].copy()
    hd["month"] = hd["date"].dt.strftime("%Y-%m")
    hm = pd.read_csv(base / "harmonized_monthly.csv").set_index("ym")
    coef = json.loads((base / "coefficients.json").read_text(encoding="utf-8"))
    return hd, hm, coef


def _factors(hm, ym):
    """Belirsizlik çarpanları (h_lo/h, h_hi/h) ve aralık dışı işareti, harmonized_monthly.csv'den."""
    if ym not in hm.index or not hm.at[ym, "h"]:
        return 1.0, 1.0, False
    r = hm.loc[ym]
    return float(r["h_lo"] / r["h"]), float(r["h_hi"] / r["h"]), bool(r["out_of_range"])


def find_k_n20(coef):
    return float(coef["noaa20_to_snpp"]["k_constant"])


def apply_harmonized(region, monthly, data_through):
    hd, hm, coef = load_harmonized(region, data_through)
    h_by_month = hd.groupby("month")["h"].sum()
    monthly["h"], monthly["h_lo"], monthly["h_hi"], monthly["out_of_range"] = [], [], [], []
    for ym in monthly["months"]:
        h = round(float(h_by_month.get(ym, 0.0)), 1)
        lo, hi, oor = _factors(hm, ym)
        monthly["h"].append(h)
        monthly["h_lo"].append(round(h * lo, 1))
        monthly["h_hi"].append(round(h * hi, 1))
        monthly["out_of_range"].append(oor)
    if "mtd" in monthly:
        mt = monthly["mtd"]
        cal, D = int(mt["month"][5:]), mt["through_day"]
        sub = hd[(hd["date"].dt.month == cal) & (hd["date"].dt.day <= D)]
        h_by_year = sub.groupby(sub["date"].dt.year)["h"].sum()
        mt["h"], mt["h_lo"], mt["h_hi"] = [], [], []
        for y in mt["years"]:
            h = round(float(h_by_year.get(y, 0.0)), 1)
            lo, hi, _ = _factors(hm, f"{y}-{cal:02d}")
            mt["h"].append(h)
            mt["h_lo"].append(round(h * lo, 1))
            mt["h_hi"].append(round(h * hi, 1))
    return find_k_n20(coef)


def apply_harmonized_grid(region, grid, data_through):
    hd, _, _ = load_harmonized(region, data_through)
    midx = {m: i for i, m in enumerate(grid["months"])}
    hc = hd.groupby(["i", "j", "month"])["h"].sum()
    lookup = {(int(i), int(j), midx[m]): v for (i, j, m), v in hc.items() if m in midx}
    for c in grid["cells"]:
        for d in c["d"]:
            d[1] = round(float(lookup.get((c["i"], c["j"], d[0]), 0.0)), 1)
    if "mtd" in grid:
        mt = grid["mtd"]
        cal, D = int(mt["month"][5:]), mt["through_day"]
        sub = hd[(hd["date"].dt.month == cal) & (hd["date"].dt.day <= D)]
        yidx = {y: i for i, y in enumerate(mt["years"])}
        hy = sub.groupby(["i", "j", sub["date"].dt.year])["h"].sum()
        ly = {(int(i), int(j), yidx[y]): v for (i, j, y), v in hy.items() if y in yidx}
        for c in mt["cells"]:
            for d in c["d"]:
                d[1] = round(float(ly.get((c["i"], c["j"], d[0]), 0.0)), 1)


def _overlaps(a, b):
    return a["west"] < b["east"] and a["east"] > b["west"] and a["south"] < b["north"] and a["north"] > b["south"]


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    txt = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    path.write_text(txt, encoding="utf-8")
    return len(txt.encode("utf-8"))


def main():
    p = region_parser("Web verisi üret (adım 24/29)")
    p.add_argument("--mode", choices=OUT_DIRS, default="harmonized")
    p.add_argument("--out", help="Çıktı klasörü (varsayılan: kipe göre web/data, web/data_filtered, web/data_raw)")
    a = p.parse_args()
    region = load_region(a.region)
    df = load(region, a.mode)
    web_data = Path(a.out) if a.out else OUT_DIRS[a.mode]
    raw = a.mode == "raw"

    # Verinin ulaştığı son gün: MODIS ve seri VIIRS'in ikisinin de olduğu son gün.
    data_through = min(df.loc[df["is_m"], "date"].max(), df.loc[df["is_v"], "date"].max())
    # Bugün henüz bitmedi (NRT gün içinde dolar): en geç dün.
    data_through = min(data_through, pd.Timestamp(datetime.now(timezone.utc).date()) - pd.Timedelta(days=1))
    monthly = build_monthly(df, region["first_month"], data_through)
    harm = a.mode == "harmonized"
    k_n20 = None
    if harm:
        k_n20 = apply_harmonized(region, monthly, data_through)
    last_complete = (data_through + pd.offsets.MonthEnd(0) == data_through)
    last_complete_month = (data_through.strftime("%Y-%m") if last_complete
                           else (data_through.to_period("M") - 1).strftime("%Y-%m"))

    out = web_data / region["name"]
    meta = {
        "id": region["name"],
        "name": region.get("name_tr", region["name"]),
        "name_en": region.get("name_en", region["name"]),
        "bbox": region["bbox"],
        "cell_deg": region["cell_deg"],
        "harmonized": harm,
        "unit": ("VIIRS S-NPP equivalent fire detections" if harm else
                 "Raw fire detections (VIIRS where available, otherwise MODIS); not harmonized" if raw else
                 "Filtered fire detections (VIIRS where available, otherwise MODIS); not harmonized"),
        "first_month": region["first_month"],
        "last_complete_month": last_complete_month,
        "data_through": data_through.strftime("%Y-%m-%d"),
        "viirs_switch": {"from": "SNPP", "to": "NOAA20", "date": "2026-11-01", "k_n20": k_n20},
        "filters": ("No quality filters yet: all detections inside the national border are counted, including static industrial sources and low-confidence detections."
                    if raw else FILTER_TEXT),
        "acknowledgment": ACK,
        # Seviye 2: kalite etiketi (regions.json harmonize.quality) ve kutu bölgesi notu
        "quality": (region.get("harmonize") or {}).get("quality", "standard"),
        "level": region["level"],
        "box_region": str(region.get("mask", "")).startswith("land:"),
        # Biyom kutuları (adım 81): bölgeye özel deneysel notu ve Türkiye ile kesişme
        "quality_note": (region.get("harmonize") or {}).get("quality_note"),
        "overlaps_turkiye": region["name"] != "turkiye" and _overlaps(region["bbox"], load_region("turkiye")["bbox"]),
    }
    sizes = {
        "meta.json": write_json(out / "meta.json", meta),
        "monthly.json": write_json(out / "monthly.json", monthly),
    }
    grid = build_grid(df, monthly, region["cell_deg"], data_through)
    if harm:
        apply_harmonized_grid(region, grid, data_through)
    sizes["grid.json"] = write_json(out / "grid.json", grid)
    if sizes["grid.json"] > GRID_MAX_BYTES:
        print(f"UYARI: grid.json {sizes['grid.json']/1e6:.1f} MB, sözleşmeye göre yıllara bölünmeli.")

    # index.json: var olanı koru, bu bölgeyi güncelle
    idx_path = web_data / "index.json"
    idx = json.loads(idx_path.read_text(encoding="utf-8")) if idx_path.exists() else {"regions": []}
    idx["regions"] = [r for r in idx["regions"] if r["id"] != region["name"]]
    idx["regions"].append({"id": region["name"], "name": meta["name"], "name_en": meta["name_en"],
                           "level": region["level"], "quality": meta["quality"]})
    order = {"turkiye": 0, "balkanlar": 1, "kafkasya": 2, "dogu_akdeniz": 3}
    idx["regions"].sort(key=lambda r: (order.get(r["id"], 9), r["id"]))
    idx["generated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    sizes["index.json"] = write_json(idx_path, idx)

    print(f"Kip: {a.mode} -> {web_data}")
    print(f"Veri sonu: {meta['data_through']}, son tam ay: {last_complete_month}, "
          f"{len(monthly['months'])} ay, {len(grid['cells'])} hücre")
    for k, v in sizes.items():
        print(f"  {k}: {v/1024:.0f} KB")


if __name__ == "__main__":
    main()
