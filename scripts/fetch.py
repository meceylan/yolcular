# AI-assisted: generated with Claude (Anthropic)
"""Adım 20: FIRMS API'den ham CSV indirme.

Kullanım:
  python scripts/fetch.py --region turkiye --sensor MODIS --start 2002-07-01 --end 2011-12-31
  python scripts/fetch.py --region turkiye --preset s1     (Seviye 1 için gereken her şey)
  python scripts/fetch.py --region balkanlar --preset s2   (Seviye 2: arşiv sonrası boşluk + NOAA-20)
  python scripts/fetch.py --region se_australia --preset s3   (Seviye 3 biyom kutuları, s2 ile aynı kural)

- Tarihler 5 günlük parçalara bölünür (API sınırı, veri sözleşmesi K0).
- Her parça için kaynak otomatik seçilir: standart kalite (SP) varsa SP, yoksa NRT.
- Dosyalar: data/raw/<bölge>/<KAYNAK>/<başlangıç>_<gün>d.csv
- Tekrar çalışınca yalnızca eksik ya da henüz tamamlanmamış (NRT'nin son günleri) parçaları indirir.
- İşlem sınırı (10 dakikada 5000) aşılmasın diye sayaç kontrol edilir, gerekirse beklenir.
"""
import io
import sys
import time
from datetime import date, timedelta

import pandas as pd
import requests

from common import DATA_RAW, FIRMS_BASE, get_map_key, load_region, redact, region_parser

CHUNK_DAYS = 5
SENSORS = {  # sensör -> (SP kaynağı, NRT kaynağı)
    "MODIS": ("MODIS_SP", "MODIS_NRT"),
    "SNPP": ("VIIRS_SNPP_SP", "VIIRS_SNPP_NRT"),
    "NOAA20": ("VIIRS_NOAA20_SP", "VIIRS_NOAA20_NRT"),
}
TODAY = date.today().isoformat()
# Seviye 1 işleri (2012-2025 MODIS ve S-NPP arşivde hazır, burada yok).
PRESETS = {
    "s1": [
        ("MODIS", "2002-07-01", "2011-12-31"),   # uzun seri, 2012 öncesi
        ("MODIS", "2026-01-01", TODAY),          # bu ay karşılaştırması
        ("SNPP", "2026-01-01", "2026-10-31"),    # S-NPP 31 Ekim 2026'ya kadar (K1)
        ("NOAA20", "2023-01-01", "2025-12-31"),  # k_N20 katsayısı için örtüşme
        ("NOAA20", "2026-01-01", TODAY),         # 1 Kasım 2026'dan itibaren seri
    ],
    # Seviye 2 (balkanlar, kafkasya, dogu_akdeniz): 2002-2025 MODIS ve 2012-2025 S-NPP
    # arşiv talebinden gelir; burada yalnızca arşivden sonraki boşluk ve NOAA-20.
    "s2": [
        ("MODIS", "2026-01-01", TODAY),
        ("SNPP", "2026-01-01", "2026-10-31"),    # S-NPP 31 Ekim 2026'ya kadar (K1)
        ("NOAA20", "2023-01-01", "2025-12-31"),  # bölgeye özgü k_N20 için örtüşme
        ("NOAA20", "2026-01-01", TODAY),         # 1 Kasım 2026'dan itibaren seri
    ],
    # Seviye 3 biyom kutuları (se_australia, california, amazon_arc): s2 ile aynı kural.
    "s3": [
        ("MODIS", "2026-01-01", TODAY),
        ("SNPP", "2026-01-01", "2026-10-31"),
        ("NOAA20", "2023-01-01", "2025-12-31"),
        ("NOAA20", "2026-01-01", TODAY),
    ],
}
LIMIT_SAFE = 4000          # 5000'lik sınırın altında kal
CHECK_EVERY = 25           # kaç istekte bir sayaç sorulsun


def d(s):
    return date.fromisoformat(s)


def availability(key):
    r = requests.get(f"{FIRMS_BASE}/api/data_availability/csv/{key}/all", timeout=60)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    return {row.data_id: (d(row.min_date), d(row.max_date)) for row in df.itertuples()}


def plan_chunks(sensor, start, end, avail):
    """(kaynak, parça başı, gün sayısı, tamam_mı) listesi."""
    sp, nrt = SENSORS[sensor]
    sp_min, sp_max = avail[sp]
    nrt_min, nrt_max = avail.get(nrt, (None, None))
    segments = []
    a, b = max(start, sp_min), min(end, sp_max)
    if a <= b:
        segments.append((sp, a, b, sp_max))
    if nrt_min:
        a, b = max(start, sp_max + timedelta(days=1), nrt_min), min(end, nrt_max)
        if a <= b:
            segments.append((nrt, a, b, nrt_max))
    chunks = []
    for src, a, b, src_max in segments:
        cur = a
        while cur <= b:
            days = min(CHUNK_DAYS, (b - cur).days + 1)
            last = cur + timedelta(days=days - 1)
            # NRT'de kaynağın son günü henüz dolmamış olabilir: o parçayı "tamamlanmamış" say,
            # sonraki çalıştırmada yeniden indirilsin. SP verisi değişmez.
            complete = src.endswith("_SP") or last < src_max
            chunks.append((src, cur, days, complete))
            cur += timedelta(days=CHUNK_DAYS)
    return chunks


class Limiter:
    def __init__(self, key):
        self.key, self.n = key, 0

    def tick(self):
        self.n += 1
        if self.n % CHECK_EVERY:
            return
        while True:
            try:
                st = requests.get(f"{FIRMS_BASE}/mapserver/mapkey_status/",
                                  params={"MAP_KEY": self.key}, timeout=30).json()
                used = int(st.get("current_transactions", 0))
            except Exception:
                used = 0
            if used < LIMIT_SAFE:
                return
            print(f"  işlem sınırına yakın ({used}/5000), 60 sn bekleniyor...")
            time.sleep(60)


def fetch_chunk(key, region, src, start, days):
    b = region["bbox"]
    area = f"{b['west']},{b['south']},{b['east']},{b['north']}"
    url = f"{FIRMS_BASE}/api/area/csv/{key}/{src}/{area}/{days}/{start.isoformat()}"
    last_err = None
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=180)
            txt = r.text
            if r.status_code == 200 and (txt.startswith("latitude") or not txt.strip()):
                return txt
            last_err = f"HTTP {r.status_code}: {txt[:200]}"
            if "limit" in txt.lower():
                print("  işlem sınırı aşıldı, 120 sn bekleniyor...")
                time.sleep(120)
                continue
        except Exception as e:
            last_err = e
        time.sleep(5 * (attempt + 1))
    raise RuntimeError(redact(last_err, key))


def run_job(key, region, sensor, start, end, avail, limiter):
    chunks = plan_chunks(sensor, d(start), d(end), avail)
    done = skipped = rows = 0
    failed = []
    for src, cs, days, complete in chunks:
        folder = DATA_RAW / region["name"] / src
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{cs.isoformat()}_{days}d.csv"
        if path.exists() and complete:
            skipped += 1
            continue
        try:
            txt = fetch_chunk(key, region, src, cs, days)
        except Exception as e:
            failed.append(f"{src} {cs}: {e}")
            continue
        limiter.tick()
        tmp = path.with_suffix(".part")
        tmp.write_text(txt, encoding="utf-8")
        tmp.replace(path)
        # Aynı başlangıçlı daha kısa eski parçaları sil (NRT'de gün uzadıkça).
        for old in folder.glob(f"{cs.isoformat()}_*d.csv"):
            if old != path:
                old.unlink()
        done += 1
        rows += max(txt.count("\n") - 1, 0)
        if done % 50 == 0:
            print(f"  {done} parça indirildi...")
    print(f"{sensor} {start}→{end}: {done} indirildi ({rows} satır), {skipped} zaten vardı, "
          f"{len(failed)} hata")
    for f in failed[:10]:
        print("  HATA:", f)
    return len(failed)


def main():
    p = region_parser("FIRMS ham veri indirme")
    p.add_argument("--sensor", choices=SENSORS)
    p.add_argument("--start", help="YYYY-AA-GG")
    p.add_argument("--end", help="YYYY-AA-GG (varsayılan bugün)")
    p.add_argument("--preset", choices=PRESETS)
    p.add_argument("--dry-run", action="store_true", help="İndirmeden yalnızca planı göster")
    a = p.parse_args()

    region = load_region(a.region)
    if a.preset:
        jobs = PRESETS[a.preset]
    elif a.sensor and a.start:
        jobs = [(a.sensor, a.start, a.end or TODAY)]
    else:
        p.error("--preset ya da --sensor ve --start gerekli")

    key = get_map_key()
    try:
        avail = availability(key)
    except Exception as e:
        sys.exit("HATA (data_availability): " + redact(e, key))

    if a.dry_run:
        for sensor, s, e in jobs:
            ch = plan_chunks(sensor, d(s), d(e), avail)
            srcs = sorted({c[0] for c in ch})
            print(f"{sensor} {s}→{e}: {len(ch)} parça, kaynaklar: {', '.join(srcs)}")
        return

    limiter = Limiter(key)
    errors = sum(run_job(key, region, sensor, s, e, avail, limiter) for sensor, s, e in jobs)
    if errors:
        sys.exit(f"{errors} parça indirilemedi. Betiği tekrar çalıştırın; yalnızca eksikler indirilir.")
    print("Bitti.")


if __name__ == "__main__":
    main()
