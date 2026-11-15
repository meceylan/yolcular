# AI-assisted: generated with Claude (Anthropic)
"""Ortak yardımcılar: proje yolları, MAP_KEY okuma, bölge ayarları.

MAP_KEY yalnızca FIRMS_MAP_KEY ortam değişkeninden okunur. Değişken yoksa
proje kökündeki .env dosyası ortama yüklenir. Anahtar hiçbir zaman yazdırılmaz.
"""
import json
import os
import sys
from pathlib import Path

# Windows konsolunda Türkçe karakter ve oklar hata vermesin.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
REGIONS_FILE = ROOT / "data" / "regions.json"
DOCS = ROOT / "docs"

FIRMS_BASE = "https://firms.modaps.eosdis.nasa.gov"


def _load_dotenv():
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def get_map_key():
    if not os.environ.get("FIRMS_MAP_KEY"):
        _load_dotenv()
    key = os.environ.get("FIRMS_MAP_KEY")
    if not key:
        sys.exit("HATA: FIRMS_MAP_KEY bulunamadı (.env ya da ortam değişkeni).")
    return key


def redact(text, key):
    """Hata mesajlarında anahtarın görünmemesi için."""
    return str(text).replace(key, "***") if key else str(text)


def region_parser(description):
    """Tüm betiklerin ortak komut satırı: --region <ad>."""
    import argparse
    p = argparse.ArgumentParser(description=description)
    p.add_argument("--region", required=True, help="data/regions.json içindeki bölge adı, ör. turkiye")
    return p


def load_region(name):
    regions = json.loads(REGIONS_FILE.read_text(encoding="utf-8"))
    for r in regions["regions"]:
        if r["name"] == name:
            return r
    names = ", ".join(r["name"] for r in regions["regions"])
    sys.exit(f"HATA: '{name}' bölgesi yok. Mevcut bölgeler: {names}")
