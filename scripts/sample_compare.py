# AI-assisted: generated with Claude (Anthropic)
"""Adım 16: MODIS ve VIIRS için 1 haftalık örnek indirir ve alanları karşılaştırır.

Örnekler data/raw/sample/ altına kaydedilir (git'e girmez). Özet ekrana ve
docs/sample_summary.json dosyasına yazılır.
"""
import io
import json
import sys
from datetime import date, timedelta

import pandas as pd
import requests

from common import DATA_RAW, DOCS, FIRMS_BASE, get_map_key, redact

BBOX = "25.6,35.8,44.9,42.2"  # batı,güney,doğu,kuzey (Türkiye)
WEEKS = {
    "SP": (date(2025, 8, 1), ["MODIS_SP", "VIIRS_SNPP_SP", "VIIRS_NOAA20_SP"]),
    "NRT": (date(2026, 10, 20), ["MODIS_NRT", "VIIRS_SNPP_NRT", "VIIRS_NOAA20_NRT"]),
}
CHUNKS = [(0, 5), (5, 2)]  # 7 gün = 5 + 2


def fetch(key, source, start):
    out = DATA_RAW / "sample" / f"{source}_{start.isoformat()}_7d.csv"
    if out.exists():
        return pd.read_csv(out, dtype={"acq_time": str})
    parts = []
    for offset, n in CHUNKS:
        d = start + timedelta(days=offset)
        url = f"{FIRMS_BASE}/api/area/csv/{key}/{source}/{BBOX}/{n}/{d.isoformat()}"
        try:
            r = requests.get(url, timeout=120)
            r.raise_for_status()
        except Exception as e:
            sys.exit("HATA: " + redact(e, key))
        text = r.text
        if "latitude" not in text.splitlines()[0]:
            sys.exit(f"HATA: {source} beklenmeyen yanıt: " + redact(text[:200], key))
        parts.append(pd.read_csv(io.StringIO(text), dtype={"acq_time": str}))
    df = pd.concat(parts, ignore_index=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    return df


def vc(s):
    return {str(k): int(v) for k, v in s.value_counts(dropna=False).sort_index().items()}


def describe(df):
    info = {"rows": int(len(df)), "columns": list(df.columns),
            "dtypes": {c: str(t) for c, t in df.dtypes.items()}}
    if not len(df):
        return info
    for c in ["satellite", "instrument", "version", "daynight", "type"]:
        if c in df.columns:
            info[c] = vc(df[c])
    conf = df["confidence"]
    if pd.api.types.is_numeric_dtype(conf):
        info["confidence"] = {"min": float(conf.min()), "median": float(conf.median()),
                              "max": float(conf.max()),
                              "lt30": int((conf < 30).sum()),
                              "30to79": int(((conf >= 30) & (conf < 80)).sum()),
                              "ge80": int((conf >= 80).sum())}
    else:
        info["confidence"] = vc(conf)
    for c in ["frp", "scan", "track", "brightness", "bright_t31", "bright_ti4", "bright_ti5"]:
        if c in df.columns:
            info[c] = {"min": float(df[c].min()), "median": float(df[c].median()),
                       "max": float(df[c].max())}
    t = df["acq_time"].astype(str).str.zfill(4)
    hour = t.str[:2].astype(int)
    info["acq_time_examples"] = t.head(3).tolist()
    info["utc_hour_by_daynight"] = {
        dn: vc(hour[df["daynight"] == dn]) for dn in sorted(df["daynight"].dropna().unique())}
    if "satellite" in df.columns:
        info["utc_hour_by_satellite"] = {
            str(s): vc(hour[df["satellite"] == s]) for s in sorted(df["satellite"].dropna().unique())}
    info["dates"] = [str(df["acq_date"].min()), str(df["acq_date"].max())]
    info["lat_decimals"] = int(df["latitude"].astype(str).str.split(".").str[1].str.len().max())
    return info


def main():
    key = get_map_key()
    summary = {}
    for label, (start, sources) in WEEKS.items():
        for src in sources:
            df = fetch(key, src, start)
            summary[src] = describe(df)
            print(f"{src}: {len(df)} satır")
    (DOCS / "sample_summary.json").write_text(
        json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
