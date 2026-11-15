# AI-assisted: generated with Claude (Anthropic)
"""Adım 17: veri boyutu ölçümü.

1) Türkiye: arşiv dosyalarından gerçek yıllık satır sayısı ve bayt/satır.
2) Seviye 2-4: 2025'in her ayının 15'inde 1 günlük API örneği alınır,
   aynı örnek Türkiye kutusu için de alınır; Türkiye'nin gerçek yıllık sayısı
   ile örnek tahmini arasındaki oran diğer bölgelere kalibrasyon olarak uygulanır.
Sonuç: docs/size_estimate.csv (ham ölçümler) ve ekrana özet.
"""
import io
import math
import time
from pathlib import Path

import pandas as pd
import requests

from common import DATA_RAW, DOCS, FIRMS_BASE, get_map_key, redact

# Taslak kutular (batı, güney, doğu, kuzey). Kesin S2 kutuları adım 48'de onaylanır.
AREAS = {
    "turkiye_kutu": (25.6, 35.8, 44.9, 42.2, 0.25),
    "balkanlar": (13.0, 39.0, 30.0, 47.0, 0.25),
    "kafkasya": (38.0, 38.0, 51.0, 44.0, 0.25),
    "orta_dogu": (34.0, 12.0, 63.0, 38.0, 0.25),
    "dogu_akdeniz": (22.0, 29.0, 36.0, 37.5, 0.25),
    "S3_avrupa_akdeniz_kafrika": (-25.0, 15.0, 45.0, 72.0, 0.5),
    "S4_dunya": (-180.0, -90.0, 180.0, 90.0, 1.0),
}
SOURCES = {"MODIS": "MODIS_SP", "VIIRS": "VIIRS_SNPP_SP"}
DATES = [f"2025-{m:02d}-15" for m in range(1, 13)]
ARCHIVE = {
    "MODIS": "DL_FIRE_M-C61_846928/fire_archive_M-C61_846928.csv",
    "VIIRS": "DL_FIRE_SV-C2_846929/fire_archive_SV-C2_846929.csv",
}


def fetch_count(key, source, box, date):
    w, s, e, n = box[:4]
    area = "world" if (w, s, e, n) == (-180.0, -90.0, 180.0, 90.0) else f"{w},{s},{e},{n}"
    url = f"{FIRMS_BASE}/api/area/csv/{key}/{source}/{area}/1/{date}"
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=180)
            r.raise_for_status()
            txt = r.text.strip()
            if not txt or "\n" not in txt and not txt.startswith("latitude"):
                raise RuntimeError("Beklenmeyen yanıt: " + txt[:200])
            df = pd.read_csv(io.StringIO(txt))
            return len(df)
        except Exception as ex:  # anahtar sızmasın
            print("  tekrar:", redact(ex, key)[:200])
            time.sleep(5)
    return None


def main():
    key = get_map_key()

    # 1) Türkiye arşivi
    arch = {}
    for sensor, rel in ARCHIVE.items():
        f = DATA_RAW / "archive" / rel
        d = pd.read_csv(f, usecols=["acq_date"])
        yearly = pd.to_datetime(d.acq_date).dt.year.value_counts()
        arch[sensor] = {"rows_per_year": yearly.mean(), "bytes_per_row": f.stat().st_size / len(d),
                        "rows_2025": yearly.get(2025)}
    print("Arşiv:", arch)

    # 2) API örnekleri
    rows = []
    for name, box in AREAS.items():
        for sensor, src in SOURCES.items():
            for dt in DATES:
                n = fetch_count(key, src, box, dt)
                rows.append({"area": name, "sensor": sensor, "date": dt, "rows": n})
                print(f"{name:28s} {sensor:5s} {dt} {n}")
    raw = pd.DataFrame(rows)
    raw.to_csv(DOCS / "size_estimate_samples.csv", index=False)

    # 3) Kalibrasyon ve tablo
    sample_year = raw.groupby(["area", "sensor"]).rows.mean() * 365
    out = []
    for name, box in AREAS.items():
        w, s, e, n, cell = box
        ncell = math.ceil((e - w) / cell) * math.ceil((n - s) / cell)
        for sensor in SOURCES:
            cal = arch[sensor]["rows_2025"] / sample_year[("turkiye_kutu", sensor)]
            est = sample_year[(name, sensor)]
            out.append({
                "area": name, "sensor": sensor, "cell_deg": cell, "cells": ncell,
                "sample_rows_per_year": round(est),
                "calibrated_rows_per_year": round(est * cal),
                "raw_MB_per_year": round(est * cal * arch[sensor]["bytes_per_row"] / 1e6, 1),
            })
    tab = pd.DataFrame(out)
    tab.to_csv(DOCS / "size_estimate.csv", index=False)
    print(tab.to_string(index=False))


if __name__ == "__main__":
    main()
