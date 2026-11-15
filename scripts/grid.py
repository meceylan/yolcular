# AI-assisted: generated with Claude (Anthropic)
"""Adım 29: ortak ızgara ve günlük sayım (veri sözleşmesi B bölümü).

Yalnızca keep=true tespitler (adım 28 Orta filtresi) dünyaya sabit ızgara hücrelerine atanır:
  i = floor((enlem + 90) / cell_deg), j = floor((boylam + 180) / cell_deg)
cell_deg data/regions.json'dan gelir (Türkiye: 0,25°).
Çıktı: data/processed/<bölge>/grid_daily.parquet  (hücre × gün × uydu)
       data/processed/<bölge>/grid_summary.json

Kullanım: python scripts/grid.py --region turkiye
"""
import json
from datetime import date

import numpy as np
import pandas as pd

from common import DATA_PROCESSED, load_region, region_parser


def assign_cells(lat, lon, cell):
    i = np.floor((np.asarray(lat) + 90) / cell).astype(np.int32)
    j = np.floor((np.asarray(lon) + 180) / cell).astype(np.int32)
    return i, j


def main():
    a = region_parser("Ortak ızgara ve günlük sayım (adım 29)").parse_args()
    region = load_region(a.region)
    cell = float(region["cell_deg"])
    src = DATA_PROCESSED / region["name"] / "detections.parquet"
    cols = ["acq_date", "latitude", "longitude", "sensor", "satellite", "daynight", "frp", "keep"]
    df = pd.read_parquet(src, columns=cols)
    df = df[df["keep"]].copy()
    df["i"], df["j"] = assign_cells(df["latitude"], df["longitude"], cell)
    df["is_day"] = (df["daynight"] == "D").astype(np.int32)
    df["is_night"] = (df["daynight"] == "N").astype(np.int32)

    g = (df.groupby(["acq_date", "i", "j", "sensor", "satellite"], observed=True)
           .agg(count=("keep", "size"), count_day=("is_day", "sum"),
                count_night=("is_night", "sum"), frp_sum=("frp", "sum"))
           .reset_index())
    g["count"] = g["count"].astype(np.int32)
    g["count_day"] = g["count_day"].astype(np.int32)
    g["count_night"] = g["count_night"].astype(np.int32)
    g["frp_sum"] = g["frp_sum"].round(2)
    g = g.sort_values(["acq_date", "satellite", "i", "j"]).reset_index(drop=True)

    out_dir = DATA_PROCESSED / region["name"]
    g.to_parquet(out_dir / "grid_daily.parquet", index=False)

    # Kontroller
    assert int(g["count"].sum()) == len(df), "ızgara toplamı tespit sayısına eşit değil"
    assert (g["count_day"] + g["count_night"] == g["count"]).all(), "gündüz+gece != toplam"
    b = region["bbox"]
    i_lo, j_lo = assign_cells([b["south"]], [b["west"]], cell)
    i_hi, j_hi = assign_cells([b["north"]], [b["east"]], cell)
    inside = g["i"].between(i_lo[0], i_hi[0]) & g["j"].between(j_lo[0], j_hi[0])
    assert inside.all(), "kutu dışında hücre var"

    g["year"] = pd.to_datetime(g["acq_date"]).dt.year
    by_sat = g.groupby("satellite").agg(rows=("count", "size"), detections=("count", "sum"),
                                        cells=("i", "size")).astype(int)
    by_sat["cells"] = [int(g[g.satellite == s][["i", "j"]].drop_duplicates().shape[0]) for s in by_sat.index]
    yearly = g.pivot_table(index="year", columns="satellite", values="count", aggfunc="sum", fill_value=0)
    summary = {
        "generated": date.today().isoformat(),
        "region": region["name"], "cell_deg": cell,
        "rows": int(len(g)), "detections": int(g["count"].sum()),
        "cells_used": int(g[["i", "j"]].drop_duplicates().shape[0]),
        "cells_in_bbox": int((i_hi[0] - i_lo[0] + 1) * (j_hi[0] - j_lo[0] + 1)),
        "first_date": str(g["acq_date"].min()), "last_date": str(g["acq_date"].max()),
        "by_satellite": {s: {k: int(v) for k, v in r.items()} for s, r in by_sat.to_dict(orient="index").items()},
        "yearly_detections": {str(y): {k: int(v) for k, v in r.items()} for y, r in yearly.to_dict(orient="index").items()},
    }
    (out_dir / "grid_summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")

    print(f"Izgara {cell}°: {len(g)} satır (hücre × gün × uydu), {summary['detections']} tespit, "
          f"{summary['cells_used']} / {summary['cells_in_bbox']} hücre kullanılıyor")
    print(by_sat.to_string())
    print(f"Yazıldı: {out_dir / 'grid_daily.parquet'}")


if __name__ == "__main__":
    main()
