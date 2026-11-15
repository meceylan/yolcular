# Veri sözleşmesi (adım 18)

**Durum: ONAYLANDI (14 Kasım 2026).** Sonraki her betik ve sayfa bu biçime uyar. Dayanak: `docs/columns.md`, `docs/data_availability.md`.

Zincir: ham CSV (`data/raw`) → **A. tespit tablosu** → **B. ızgara tablosu** → **C. web JSON** (`web/data`).

## Kararlar (onaylandı)

### K0. Dönem
- Uyumlu seri **Temmuz 2002 – Aralık 2025** (Terra ve Aqua'nın birlikte çalıştığı ilk aydan itibaren), ayrıca "bu ay" karşılaştırması için 2026.
- **MODIS verisi 2002-07'den, VIIRS verisi 2012'den** itibaren çekilir.
- 2002-07 – 2011-12 MODIS verisi API ile çekilir (arşiv talebi yalnızca 2012–2025'i kapsıyor). **API tek istekte en fazla 5 gün veriyor** (14 Kasım 2026'da denendi: 10 gün reddedildi), bu yüzden parçalar 5 günlüktür.

### K1. VIIRS uydusu ve 2 Kasım 2026 sonrası
- Referans seri **VIIRS S-NPP**'dir (2012'den beri var, MODIS ile en uzun örtüşme).
- **Geçiş ay sınırında yapılır:** 31 Ekim 2026'ya kadar S-NPP, **1 Kasım 2026'dan itibaren NOAA-20**. S-NPP'nin 1–2 Kasım 2026 verisi kullanılmaz (bir ayın içinde iki uydu karışmasın diye).
- NOAA-20 sayıları **S-NPP eşdeğerine çevrilir**: `k_N20` katsayısı, iki uydunun birlikte çalıştığı 2023–2025 yıllarından, MODIS katsayısıyla aynı yöntemle (bölge ve ay bazında) hesaplanır. Örnek haftalarda iki uydu arasındaki fark ±%15 idi.
- Seride her ayın hangi kaynaktan geldiği açıkça yazılır (aşağıda `src`). NOAA-20'den gelen aylar sayfada "tahmin" olarak işaretlenir.
- NOAA-20, geçiş tarihinden önceki aylarda seriye girmez; 2023–2025 verisi yalnızca katsayı için indirilir.
- Reddedilen seçenekler: (a) 2018'den itibaren tümüyle NOAA-20 kullanmak: referans seriyi ortasından böler; (b) Kasım 2026'yı yalnızca MODIS'ten tahmin etmek: elde gerçek VIIRS ölçümü varken daha zayıf.

### K2. Uyumlu değerin tanımı
Uyumlu seri = **"VIIRS S-NPP eşdeğeri yangın tespiti sayısı"** (filtrelenmiş, gündüz + gece). Ayın kaynağı `src`:

| `src` | Ne zaman | Değer |
|---|---|---|
| `V` | Şubat 2012 – Ekim 2026 | S-NPP sayısı (ölçüm) |
| `N` | Kasım 2026 ve sonrası | NOAA-20 sayısı × `k_N20` (tahmin) |
| `M` | Temmuz 2002 – Ocak 2012 | MODIS sayısı × MODIS katsayısı (tahmin) |

Ocak 2012 `M`'dir, çünkü S-NPP 20 Ocak'ta başlıyor. `M` ve `N` ayları sayfada, takvimde ve indirilen CSV'de **"tahmin"** olarak işaretlenir; yalnızca `V` ayları ölçümdür. MODIS katsayısı 2012–2025 örtüşme döneminden hesaplanır ve 2002–2011'e uygulanır.

### K3. Tarih ve yarım ay
- Tüm tarihler **UTC**'dir (FIRMS'in verdiği gibi); yerel saate çevrilmez.
- Sayfada varsayılan "bu ay" = **son tamamlanmış ay**.
- Medyan = aynı takvim ayının, seçili yıl dışındaki tüm yıllardaki değerlerinin medyanı.
- İçinde bulunulan yarım ay `partial` olarak işaretlenir ve sayfada **"kısmi ay"** etiketiyle gösterilir. Yüzde karşılaştırması onun için de verilir, ama **yalnızca ayın aynı günleri üzerinden**: verinin ulaştığı gün `D` ise, kısmi ayın 1–`D` toplamı, önceki her yılın aynı ayının 1–`D` toplamlarının medyanıyla karşılaştırılır. Bunun için gereken "aynı günler" değerleri JSON'da `mtd` bloğunda hazır gelir (aşağıda).
- Kısmi ayın takvim hücresi 1–`D` toplamını gösterir; tam aylarla aynı renk skalasında yorumlanmaması için etiketlidir.

### K4. Filtreler silmez, işaretler
Tespit tablosunda hiçbir satır filtre yüzünden silinmez; `keep` sütunu işaretlenir. Filtre kuralı (adım 28, onaylandı, `docs/filters.md`): `keep = in_country` ve `flag_static`, `flag_offshore`, `flag_low_conf`, `flag_mask` işaretlerinin hiçbiri yok. `flag_mask`, `type` alanı olmayan NRT satırları için arşivdeki sabit kaynak konumlarından üretilen maskedir. Izgara ve web verisi yalnızca `keep = true` satırlardan üretilir.

### K5. Izgara
Hücreler bölgeye değil dünyaya sabitlenir; böylece Seviye 2–4 bölgeleri aynı hücreleri paylaşır:
`i = floor((enlem + 90) / cell_deg)`, `j = floor((boylam + 180) / cell_deg)`. Hücrenin güneybatı köşesi: `(i × cell_deg − 90, j × cell_deg − 180)`. `cell_deg` bölge ayar dosyasından gelir (S1–S2: 0,25; S3: 0,5; S4: 1).

## A. Tespit tablosu
Dosya: `data/processed/{region}/detections.parquet` (git'e girmez). Bir satır = bir tespit. Üreten: `clean.py`.

| Sütun | Tür | Açıklama | MODIS kaynağı | VIIRS kaynağı |
|---|---|---|---|---|
| `acq_date` | tarih | UTC gün | `acq_date` | `acq_date` |
| `acq_time` | metin, 4 hane | UTC `HHMM`, başa sıfır eklenir | `acq_time` | `acq_time` |
| `latitude`, `longitude` | ondalık | WGS84 | aynı | aynı |
| `sensor` | metin | `MODIS` / `VIIRS` | `instrument` | `instrument` |
| `satellite` | metin | `Terra`, `Aqua`, `SNPP`, `NOAA20` | `Terra`/`Aqua` | `N`→`SNPP`, `N20`→`NOAA20` |
| `confidence_raw` | metin | Kaynaktaki değer | `0`–`100` | `l`/`n`/`h` |
| `confidence_class` | metin | `low` / `nominal` / `high` | 0–29 / 30–79 / 80–100 | `l` / `n` / `h` |
| `frp` | ondalık | MW; 0 ya da eksikse boş | `frp` | `frp` |
| `daynight` | metin | `D` / `N` | `daynight` | `daynight` |
| `type` | tam sayı, boş olabilir | 0 yangın, 1 yanardağ, 2 sabit kara, 3 deniz; NRT'de boş | `type` | `type` |
| `bright_mir` | ondalık | ~4 µm parlaklık sıcaklığı, K | `brightness` | `bright_ti4` |
| `bright_tir` | ondalık | ~11 µm parlaklık sıcaklığı, K | `bright_t31` | `bright_ti5` |
| `scan`, `track` | ondalık | Piksel boyutu, km | aynı | aynı |
| `source` | metin | FIRMS kaynak adı, ör. `VIIRS_SNPP_SP` | | |
| `is_nrt` | mantıksal | NRT kaynağından mı | | |
| `keep` | mantıksal | Filtreden geçti mi (adım 28'e kadar hep `true`) | | |

Kurallar:
- Tekrar anahtarı: `satellite, acq_date, acq_time, latitude, longitude`.
- Aynı uydu ve gün için hem SP hem NRT varsa yalnızca SP tutulur.
- `confidence_class` eşlemesi FIRMS tanımına dayanan başlangıç değeridir; hangi sınıfların tutulacağı adım 28'in kararıdır.
- `NOAA21` ve diğer kaynaklar tabloya girmez.

Eklenen alanlar (adım 22, 14 Kasım 2026; var olan alanlar değişmedi):

| Sütun | Tür | Açıklama |
|---|---|---|
| `origin` | metin | `archive` (FIRMS Archive Download) / `api` |
| `version` | metin | Kaynaktaki sürüm etiketi (`6.03`, `61.03`, `6.1NRT`, `2`, `2.0NRT`) |
| `in_country` | mantıksal | Bölge ülke sınırı içinde mi. Arşiv satırları FIRMS sınırıyla zaten kesilmiş: `true`. API satırları Natural Earth sınırıyla (`data/boundaries/<ISO>.geojson`) test edilir. Kutu bölgelerinde (`mask: land:ne_10m_land`, Seviye 2) tüm satırlar Natural Earth 1:10m kara poligonlarıyla test edilir: `true` = karada |
| `in_series` | mantıksal | Uyumlu serinin VIIRS/MODIS ayağına girer mi (K1–K2): S-NPP 2012-02-01 – 2026-10-31, NOAA-20 2026-11-01'den itibaren; diğer NOAA-20 satırları yalnızca `k_N20` için. MODIS hep `true` |
| `modis_v61_label` | mantıksal | MODIS satırının sürüm etiketi `61.x` mi (arşivde 2023'ten itibaren; 2022 ve öncesi `6.03`) |
| `flag_low_conf` | mantıksal | `confidence_class = low` |
| `flag_static` | mantıksal | `type` 1 ya da 2 (yanardağ / sabit kara kaynağı) |
| `flag_offshore` | mantıksal | `type = 3` |
| `flag_no_type` | mantıksal | `type` yok (NRT) |
| `flag_bad_value` | mantıksal | `frp` boş/0 ya da `bright_tir <= 0` |

`keep` adım 28 kararıyla belirlenir (K4). Yeni sütun: `flag_mask` (mantıksal; NRT satırı sabit kaynak maskesindeki bir hücreye düşüyor). Maske dosyası: `data/processed/{region}/static_mask.json`.

## B. Izgara tablosu
Dosya: `data/processed/{region}/grid_daily.parquet`. Bir satır = hücre × gün × uydu. Yalnızca `keep = true`. Üreten: adım 29.

| Sütun | Açıklama |
|---|---|
| `acq_date` | UTC gün |
| `i`, `j` | Hücre indisleri (K5) |
| `sensor`, `satellite` | A'daki gibi |
| `count` | Tespit sayısı |
| `count_day`, `count_night` | Gündüz ve gece ayrımı |
| `frp_sum` | FRP toplamı, MW |

Katsayılar: `data/processed/{region}/coefficients.json` (MODIS→S-NPP ve NOAA-20→S-NPP; ay bazında; adım 31).

## C. Web JSON
Sayfa yalnızca bu dosyaları okur. Anahtar ve ham veri burada bulunmaz. Üreten: `export.py`.

Klasörler (adım 33): `web/data/` sayfanın okuduğu uyumlu sürüm (`export.py --mode harmonized`, varsayılan). `web/data_filtered/` adım 28 filtresiyle üretilmiş, uyumlaştırılmamış ara sürüm (`--mode filtered`). `--mode raw` filtresiz s0 sürümünü `web/data_raw/`'a yazar. Aynı biçim; sayfa yalnızca `web/data/` okur.

### `web/data/index.json`
```json
{
  "generated": "2026-11-14T15:00:00Z",
  "regions": [ { "id": "turkiye", "name": "Türkiye", "name_en": "Türkiye", "level": 1 } ]
}
```

### `web/data/{region}/meta.json`
```json
{
  "id": "turkiye",
  "bbox": { "south": 35.8, "north": 42.2, "west": 25.6, "east": 44.9 },
  "cell_deg": 0.25,
  "harmonized": true,
  "unit": "VIIRS S-NPP equivalent fire detections",
  "first_month": "2002-07",
  "last_complete_month": "2026-10",
  "data_through": "2026-11-13",
  "viirs_switch": { "from": "SNPP", "to": "NOAA20", "date": "2026-11-01", "k_n20": 1.0 },
  "filters": "docs/filters.md özeti (tek cümle, İngilizce)",
  "acknowledgment": "NASA FIRMS teşekkür metni (İngilizce)"
}
```
`harmonized: false` ise (adım 24, ham v0) `h` değerleri ham sayıdır ve sayfa "ham veri" uyarısı gösterir.

### `web/data/{region}/monthly.json` (bölge toplamı; takvimin ilk çizimi)
```json
{
  "months":  ["2002-07", "...", "2012-02", "...", "2026-11"],
  "src":     ["M", "...", "V", "...", "N"],
  "partial": [false, "...", false, "...", true],
  "h": [412.0, "...", 388, "...", 95.5],
  "m": [61, "...", 70, "...", 14],
  "v": [null, "...", 388, "...", 97],
  "mtd": {
    "month": "2026-11",
    "through_day": 13,
    "years": [2002, 2003, "...", 2026],
    "src":   ["M", "M", "...", "N"],
    "h": [120.5, 98.0, "...", 95.5],
    "m": [18, 15, "...", 14],
    "v": [null, null, "...", 97]
  }
}
```
**Ek alan (adım 28 kararı):** `"gap_days": [0, 0, 10, "..."]`, `months` ile aynı uzunlukta: o ayda serinin kaynağı olan uydunun veri vermediği gün sayısı (liste: `docs/data_gaps.md`). Sayfa `gap_days ≥ 3` olan aylara işaret koyar ve açıklama gösterir; değer düzeltilmez. MODIS aylarında (`src = M`) Terra ya da Aqua'dan yalnızca birinin eksik olduğu günler de sayılır.

**Ek alanlar (adım 33, uyumlu seri):** `h_lo`, `h_hi` (sayı dizileri, `months` ile aynı uzunlukta): uyumlu değerin olası aralığı (adım 31 sınamasındaki dağılım; `V` aylarında `h` ile aynı). `out_of_range` (mantıksal dizi): MODIS düzeyi kalibrasyonda sınanmış en yüksek değerin üstünde, büyük olasılıkla fazla tahmin, aralık geniş. `mtd` bloğunda da `h_lo`, `h_hi` bulunur. Kaynak: `data/processed/{region}/harmonized_daily.parquet` (değer) ve `harmonized_monthly.csv` (aralık çarpanları ve işaret).

`mtd` ("aynı günler") yalnızca son ay kısmi ise bulunur: `month` ayının takvim ayı için, listedeki her yılın 1–`through_day` günlerinin toplamı. Son yılın değeri kısmi ayın kendisidir; sayfa onu diğer yılların medyanıyla karşılaştırır. `src` ve katsayı, o yılın o ayındaki kuralla aynıdır.
Dizilerin hepsi `months` ile aynı uzunlukta ve sırada. `h` uyumlu değer (1 ondalık), `m` ham MODIS sayısı, `v` ham VIIRS sayısı (o ayın uydusundan; yoksa `null`).

### `web/data/{region}/grid.json` (dikdörtgen seçimi için)
```json
{
  "cell_deg": 0.25,
  "months": ["2002-07", "..."],
  "cells": [
    { "i": 504, "j": 822, "d": [[0, 3.5, 1, null], [120, 12, 2, 12]] }
  ],
  "mtd": {
    "month": "2026-11", "through_day": 13, "years": [2002, "...", 2026],
    "cells": [ { "i": 504, "j": 822, "d": [[0, 1.5, 1, null], [24, 4, 1, 4]] } ]
  }
}
```
- `d` içindeki her kayıt: `[ay indisi, h, m, v]`. Yalnızca en az bir değeri sıfırdan farklı olan aylar yazılır; yazılmayan ay = 0.
- Hiç tespiti olmayan hücre dosyada yer almaz.
- `mtd.cells` aynı biçimdedir, yalnızca ilk sayı ay indisi değil `mtd.years` içindeki yıl indisidir. Dikdörtgen seçiminde kısmi ay karşılaştırması bu hücrelerin toplamından hesaplanır.
- Seçilen dikdörtgenin değeri = merkezi dikdörtgenin içinde kalan hücrelerin toplamı. Medyan ve yüzde fark tarayıcıda bu toplamdan hesaplanır.
- Uygulama (adım 34): dikdörtgen bölge kutusuna kırpılır; haritada sayılan hücrelerin sınırına oturtulmuş hali gösterilir. Seçimde `h_lo`/`h_hi`, o ayın ülke düzeyindeki aralık oranıyla (`h_lo/h`, `h_hi/h`) çarpılır; `out_of_range` yalnızca bölgenin tamamı seçiliyken gösterilir (alt alan için bilinmiyor).
- Dosya 5 MB'ı aşarsa yıllara bölünür (`grid_2012.json` ...); alanlar aynı kalır.

### İndirilen CSV (sayfa üretir)
Sütunlar: `region_or_bbox, year, month, fires_harmonized, modis_raw, viirs_raw, source, estimate, partial, through_day, gap_days, median_same_month, pct_diff`. Başlıklar İngilizce. `source`: `VIIRS S-NPP`, `VIIRS NOAA-20 (scaled)`, `MODIS (scaled)`. `estimate`: `V` dışındaki aylarda `yes`. Kısmi ay satırında `through_day` doludur ve medyan ile yüzde fark aynı günler üzerindendir; tam aylarda `through_day` boştur.

## Değişiklik kuralı
Onaydan sonra bu dosyadaki alan adları ve anlamları değişmez. Yeni alan eklenebilir; var olan alan kaldırılmaz ya da yeniden adlandırılmaz. Değişiklik gerekiyorsa önce bu dosya güncellenir, sonra kod.
