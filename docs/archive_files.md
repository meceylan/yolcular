# Arşiv dosyaları (FIRMS Archive Download, adım 14)

Konum: `data/raw/archive/` (git'e girmez). Zip'ler aynı adlı klasörlere açıldı.
Talep: Türkiye ülke sınırı (kutu değil), 2012–2025, CSV.

| Dosya | Sensör | Kalite | Satır | İlk tarih | Son tarih | Boyut |
|---|---|---|---|---|---|---|
| `DL_FIRE_M-C61_846928/fire_archive_M-C61_846928.csv` | MODIS (Terra 69 397 + Aqua 69 124) | Standart (archive, MCD14ML) | 138 521 | 2012-01-03 | 2025-12-29 | 10,8 MB |
| `DL_FIRE_SV-C2_846929/fire_archive_SV-C2_846929.csv` | VIIRS S-NPP 375 m | Standart (archive, VNP14IMGTML) | 605 609 | 2012-01-20 | 2025-12-31 | 48,6 MB |

- **İki dosya da standart kalite (archive).** `fire_nrt_*` (geçici/NRT) dosyası yok; dönem 2025 sonunda bittiği için gerek de yok.
- Her zip'te bir `Readme.txt` var; yalnızca çevrimiçi README'ye link veriyor. Tam metin https://firms.modaps.eosdis.nasa.gov/download/Readme.txt adresinden okundu (eksik veri uyarısı: `docs/data_gaps.md`, atıf ve disclaimer: `docs/references.md`).
- Sütunlar iki dosyada aynı: latitude, longitude, brightness, scan, track, acq_date, acq_time, satellite, instrument, confidence, version, bright_t31, frp, daynight, type. `type` alanı dolu (0 = vejetasyon yangını, 2 = diğer sabit kaynak, 3 = açık deniz).
- Koordinatlar: enlem 35,82–42,07, boylam 25,69–44,80, Seviye 1 kutusunun içinde. Dosya ülke sınırıyla kesildiği için kutunun içindeki komşu ülke noktaları (Yunan adaları, Suriye, Irak, Bulgaristan, Gürcistan, Ermenistan, İran kenarları) **yok**. API ile kutudan çekilen veriyle (2002–2011 MODIS, 2026) karşılaştırırken aynı ülke maskesi uygulanmalı (adım 22).

## Yıllık satır sayıları

| Yıl | MODIS | VIIRS S-NPP |
|---|---|---|
| 2012 | 7 119 | 35 462 |
| 2013 | 11 528 | 52 089 |
| 2014 | 6 829 | 33 276 |
| 2015 | 18 095 | 66 801 |
| 2016 | 13 599 | 57 581 |
| 2017 | 9 607 | 43 688 |
| 2018 | 8 112 | 37 316 |
| 2019 | 8 355 | 39 859 |
| 2020 | 8 855 | 44 396 |
| 2021 | 10 063 | 42 993 |
| 2022 | 5 703 | 26 567 |
| 2023 | 9 067 | 39 155 |
| 2024 | 12 090 | 47 005 |
| 2025 | 9 499 | 39 421 |

## Dikkat (adım 22/28 için)
- **MODIS `version` alanı karışık:** 2012–2022 satırları `6.03`, 2023–2025 satırları `61.03`. Zip adı C6.1 diyor; 2022/2023 sınırında sürüm etiketi değişiyor. Uyumlaştırmada 2023'te kırılma var mı kontrol edilmeli (FABLE, adım 30/32).
- VIIRS `version` hepsi `2` (Collection 2).
- `type` dağılımı: MODIS 0: 127 915, 2: 10 455, 3: 151. VIIRS 0: 445 576, 2: 155 148, 3: 4 885.
