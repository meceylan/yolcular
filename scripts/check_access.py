# AI-assisted: generated with Claude (Anthropic)
"""Adım 15: FIRMS veri erişim testi.

MAP_KEY durumunu ve data_availability listesini çeker, sonucu
docs/data_availability.csv dosyasına yazar ve ekrana özet basar.
"""
import io
import sys

import pandas as pd
import requests

from common import DOCS, FIRMS_BASE, get_map_key, redact


def main():
    key = get_map_key()
    try:
        st = requests.get(f"{FIRMS_BASE}/mapserver/mapkey_status/",
                          params={"MAP_KEY": key}, timeout=60)
        st.raise_for_status()
        status = st.json()
        print("MAP_KEY durumu:", {k: v for k, v in status.items() if k != "map_key"})

        r = requests.get(f"{FIRMS_BASE}/api/data_availability/csv/{key}/all", timeout=60)
        r.raise_for_status()
    except Exception as e:  # anahtar sızmasın
        sys.exit("HATA: " + redact(e, key))

    df = pd.read_csv(io.StringIO(r.text))
    out = DOCS / "data_availability.csv"
    df.to_csv(out, index=False)
    print(df.to_string(index=False))
    print(f"\nKaydedildi: {out.relative_to(DOCS.parent)}")


if __name__ == "__main__":
    main()
