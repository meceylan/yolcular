# AI-assisted: generated with Claude (Anthropic)
"""Adım 28 filtre kararının koddaki tek kaynağı (docs/filters.md).

- Orta filtre: type 1/2/3 ve düşük güven (MODIS < 30, VIIRS 'l') çıkar.
- NRT için konum maskesi: arşivdeki type 2/3 tespitlerinin en az 3 ayrı günde görüldüğü
  0,01° hücreler. VIIRS yalnızca kendi hücresi, MODIS kendi hücresi + 8 komşu.
- Veri boşlukları (docs/data_gaps.md): ayda kaç gün serinin uydusu veri vermemiş.
Maske üretimi scripts/filter_options.py'deki build_mask / in_mask ile aynıdır.
"""
import numpy as np
import pandas as pd

MASK_CELL = 0.01      # derece (~1 km)
MASK_MIN_DAYS = 3
MASK_R_VIIRS = 0      # komşu halka sayısı
MASK_R_MODIS = 1

FILTER_TEXT = ("Detections flagged as static sources or offshore, and low-confidence detections, "
               "are removed; for recent near-real-time data a location mask built from archived "
               "static sources is used.")

# Seri kaynağının veri vermediği günler (docs/data_gaps.md 2 ve 2b).
GAPS = {
    "SNPP": [("2022-07-27", "2022-08-10"), ("2024-05-30", "2024-06-03"), ("2024-07-10", "2024-07-15"),
             ("2024-07-25", "2024-07-28"), ("2024-09-26", "2024-09-26"), ("2025-07-06", "2025-07-07"),
             ("2026-06-01", "2026-06-02"), ("2026-07-11", "2026-07-16")],
    "NOAA20": [],
    # MODIS: Terra ya da Aqua'dan biri (ya da ikisi) eksik
    "MODIS": [("2002-07-01", "2002-07-03"), ("2002-07-30", "2002-08-07"), ("2020-08-30", "2020-09-02"), ("2014-09-28", "2014-09-29")],
}
GAP_FLAG_MIN = 3  # sayfa bu ve üstünü işaretler


def cell_ids(lat, lon):
    lat, lon = np.asarray(lat), np.asarray(lon)
    return (np.floor(lat / MASK_CELL).astype(np.int64) * 100000
            + np.floor((lon + 180) / MASK_CELL).astype(np.int64))


def neighbours(ids, r):
    ids = np.asarray(ids, dtype=np.int64)
    out = set()
    for di in range(-r, r + 1):
        for dj in range(-r, r + 1):
            out.update((ids + di * 100000 + dj).tolist())
    return out


def build_mask(df):
    """df: SP satırları (type dolu), 'acq_date', 'type', 'latitude', 'longitude'."""
    s = df[df["type"].isin([2, 3])]
    cells = cell_ids(s["latitude"].to_numpy(), s["longitude"].to_numpy())
    days = pd.Series(s["acq_date"].to_numpy(), index=cells).groupby(level=0).nunique()
    return np.sort(days[days >= MASK_MIN_DAYS].index.to_numpy())


def in_mask(df, mask_cells):
    c = cell_ids(df["latitude"].to_numpy(), df["longitude"].to_numpy())
    mv = neighbours(mask_cells, MASK_R_VIIRS)
    mm = neighbours(mask_cells, MASK_R_MODIS)
    is_v = (df["sensor"] == "VIIRS").to_numpy()
    hit_v = np.fromiter((x in mv for x in c), bool, len(c))
    hit_m = np.fromiter((x in mm for x in c), bool, len(c))
    return np.where(is_v, hit_v, hit_m)


def gap_days_by_month(src_key):
    """{'YYYY-MM': gün sayısı} — src_key: 'SNPP', 'NOAA20' ya da 'MODIS'."""
    out = {}
    for a, b in GAPS[src_key]:
        for day in pd.date_range(a, b):
            k = day.strftime("%Y-%m")
            out[k] = out.get(k, 0) + 1
    return out
