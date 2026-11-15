# AI-assisted: generated with Claude (Anthropic)
"""Seviye 2: harmonizasyon girdi özeti (katsayı HESAPLAMAZ, karar adım 51'de).

Her bölge için grid_daily.parquet'ten, harmonize.py/overlap.py ile aynı kurallarla:
  - 2012-02 – 2022-12 takvim ayı başına ΣMODIS (Terra+Aqua) ve ΣVIIRS S-NPP, kesinti günleri çıkarılmış, ham oran
  - 2023–2025 bağımsız sınama için ay ay ΣMODIS ve ΣS-NPP
  - 2023–2025 NOAA-20 / S-NPP örtüşme oranı (S-NPP kesinti günleri çıkarılmış)
Çıktı: docs/s2_overlap_input.md
Kullanım: python scripts/s2_overlap_input.py [--tag s3] balkanlar kafkasya dogu_akdeniz
"""
import json
import sys
from datetime import date

import pandas as pd

from common import DATA_PROCESSED, DOCS, load_region
from overlap import OVERLAP_START, STABLE_LAST, gap_dates

MONTHS = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]


def load(region):
    g = pd.read_parquet(DATA_PROCESSED / region["name"] / "grid_daily.parquet",
                        columns=["acq_date", "satellite", "count"])
    g["acq_date"] = g.acq_date.astype(str)
    g["y"], g["mo"] = g.acq_date.str[:4].astype(int), g.acq_date.str[5:7].astype(int)
    return g


def modis_viirs(g, a, b):
    x = g[(g.acq_date >= a) & (g.acq_date <= b) & g.satellite.isin(["Terra", "Aqua", "SNPP"])]
    x = x[~x.acq_date.isin(gap_dates())]
    x = x.assign(s=x.satellite.map({"Terra": "MODIS", "Aqua": "MODIS", "SNPP": "VIIRS"}))
    return x


def fmt(n):
    return f"{int(n):,}".replace(",", " ")


def section(name, g, tur_ratio):
    out = []
    cal = modis_viirs(g, OVERLAP_START, f"{STABLE_LAST}-12-31")
    t = cal.pivot_table(index="mo", columns="s", values="count", aggfunc="sum", fill_value=0)
    t["ratio"] = t.VIIRS / t.MODIS
    out.append(f"### {name}\n\n**2012-02 – {STABLE_LAST}-12, takvim ayı toplamları (kesinti günleri çıkarılmış)**\n")
    out.append("| Ay | ΣMODIS | ΣVIIRS S-NPP | Ham oran V/M | Türkiye oranı |\n|---|---|---|---|---|")
    for mo, r in t.iterrows():
        tr = tur_ratio.get(mo)
        out.append(f"| {MONTHS[mo - 1]} | {fmt(r.MODIS)} | {fmt(r.VIIRS)} | {r.ratio:.2f} | "
                   f"{'' if tr is None else f'{tr:.2f}'} |")
    tot = t[["MODIS", "VIIRS"]].sum()
    out.append(f"| **Toplam** | {fmt(tot.MODIS)} | {fmt(tot.VIIRS)} | {tot.VIIRS / tot.MODIS:.2f} | "
               f"{tur_ratio.get('all', float('nan')):.2f} |\n")

    test = modis_viirs(g, "2023-01-01", "2025-12-31")
    tt = test.pivot_table(index=["y", "mo"], columns="s", values="count", aggfunc="sum", fill_value=0)
    out.append("**2023–2025 bağımsız sınama için aylık toplamlar (kesinti günleri çıkarılmış)**\n")
    out.append("| Ay | " + " | ".join(f"{y} M | {y} V" for y in (2023, 2024, 2025)) + " |")
    out.append("|---|" + "---|" * 6)
    for mo in range(1, 13):
        cells = []
        for y in (2023, 2024, 2025):
            r = tt.loc[(y, mo)] if (y, mo) in tt.index else None
            cells += [fmt(r.MODIS) if r is not None else "0", fmt(r.VIIRS) if r is not None else "0"]
        out.append(f"| {MONTHS[mo - 1]} | " + " | ".join(cells) + " |")
    yt = tt.groupby(level=0).sum()
    out.append("| **Yıl** | " + " | ".join(f"{fmt(yt.loc[y].MODIS)} | {fmt(yt.loc[y].VIIRS)}" for y in yt.index) + " |\n")

    n = g[g.satellite.isin(["SNPP", "NOAA20"]) & (g.acq_date >= "2023-01-01") & (g.acq_date <= "2025-12-31")]
    n = n[~n.acq_date.isin(gap_dates(("SNPP",)))]
    ny = n.pivot_table(index="y", columns="satellite", values="count", aggfunc="sum", fill_value=0)
    out.append("**NOAA-20 / S-NPP örtüşmesi, 2023–2025 (S-NPP kesinti günleri çıkarılmış)**\n")
    out.append("| Yıl | ΣNOAA-20 | ΣS-NPP | Oran N20/SNPP |\n|---|---|---|---|")
    for y, r in ny.iterrows():
        out.append(f"| {y} | {fmt(r.NOAA20)} | {fmt(r.SNPP)} | {r.NOAA20 / r.SNPP:.3f} |")
    s = ny.sum()
    out.append(f"| **2023–2025** | {fmt(s.NOAA20)} | {fmt(s.SNPP)} | {s.NOAA20 / s.SNPP:.3f} |\n")
    return "\n".join(out), {"ratio_2012_2022": round(float(tot.VIIRS / tot.MODIS), 3),
                            "n20_snpp_2023_2025": round(float(s.NOAA20 / s.SNPP), 3)}


def main():
    args = sys.argv[1:]
    tag = "s2"
    if args and args[0] == "--tag":
        tag, args = args[1], args[2:]
    names = args
    tg = load(load_region("turkiye"))
    tt = modis_viirs(tg, OVERLAP_START, f"{STABLE_LAST}-12-31").pivot_table(
        index="mo", columns="s", values="count", aggfunc="sum")
    tur = (tt.VIIRS / tt.MODIS).to_dict()
    tur["all"] = tt.VIIRS.sum() / tt.MODIS.sum()
    parts, short = [], {}
    for nme in names:
        r = load_region(nme)
        text, s = section(f"{nme} ({r['name_en']})", load(r), tur)
        parts.append(text)
        short[nme] = s
    head = f"""# Seviye {tag[1:]}: harmonizasyon girdi özeti

Üretildi: {date.today().isoformat()} (`python scripts/s2_overlap_input.py --tag {tag} {' '.join(names)}`).
Bu dosya yalnızca girdidir: katsayı seçilmedi, harmonize.py çalıştırılmadı (katsayı kararı FABLE'da).

Kurallar Türkiye ile aynı: yalnızca `keep = true` (Orta filtre), 0,25° dünya-sabit ızgara, kesinti günleri
(`scripts/filters.py` GAPS, S-NPP ve MODIS) çıkarılmış. Kalibrasyon dönemi 2012-02 – {STABLE_LAST}-12 (yörünge sabit).
Ham oran = ΣVIIRS / ΣMODIS (Türkiye'deki "toplamların oranı" yöntemi). Türkiye sütunu karşılaştırma içindir.

| Bölge | Ham oran 2012–2022 (tüm yıl) | NOAA-20 / S-NPP 2023–2025 |
|---|---|---|
""" + "\n".join(f"| {k} | {v['ratio_2012_2022']:.2f} | {v['n20_snpp_2023_2025']:.3f} |" for k, v in short.items()) + \
        f"\n| turkiye (karşılaştırma) | {tur['all']:.2f} | 0.986 (seçilen k_N20) |\n\n"
    (DOCS / f"{tag}_overlap_input.md").write_text(head + "\n".join(parts), encoding="utf-8")
    print(json.dumps(short, ensure_ascii=False))


if __name__ == "__main__":
    main()
