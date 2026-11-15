# Seviye 2: bölge kutuları ve FIRMS Archive Download talepleri

Karar (14 Kasım 2026): S2 üç bölgeyle gider: balkanlar, kafkasya, dogu_akdeniz. orta_dogu kapsam dışı (gelecek çalışma, bölüm 5).
Durum: kutular adım 48'de (OPUS) regions.json'a yazılır; henüz kod yok.
Satır sayıları: 14 Kasım 2026 API örneği (2025'in her ayının 15'i, günlük satır sayısı × 365). Belirsizlik ±%30.

## 1. Bölge kutuları (W, S, E, N; 0,25° ızgaraya oturur)

| Bölge | İçerdiği ülkeler | W | S | E | N | MODIS satır/yıl | VIIRS satır/yıl |
|---|---|---|---|---|---|---|---|
| balkanlar | Yunanistan, Bulgaristan (+ Balkanlar) | 19.0 | 34.5 | 29.5 | 44.5 | 6 000 | 29 800 |
| kafkasya | Gürcistan, Ermenistan, Azerbaycan, Nahçıvan | 40.0 | 38.25 | 50.5 | 43.75 | 7 400 | 23 300 |
| dogu_akdeniz | Kıbrıs, Lübnan, İsrail, Ürdün, Suriye kıyısı | 30.0 | 29.0 | 36.5 | 36.0 | 3 700 | 16 700 |

Kutular birbirini ve Türkiye kutusunu kısmen örter (ör. Trakya Balkanlar'da, doğu Anadolu Kafkasya'da). Her bölge kendi klasörüne iner ve kendi içinde sayılır, sorun değil.

## 2. Arşiv talepleri (toplam 6)

Hepsi CSV. Tarih aralıkları: MODIS 2002-07-01 → 2025-12-31; VIIRS S-NPP 2012-01-01 → 2025-12-31 (gerçek başlangıç 20 Ocak 2012). Her talep tek parça, en fazla ~420 000 satır (Türkiye VIIRS dosyamız 605 609 satırdı ve sorunsuz geldi). Formun resmî bir sınır sayısı yok; "çok büyük" derse aralığı ikiye böl.

| # | Bölge | Ürün | Tarih aralığı | Kutu (W, S, E, N) | Beklenen satır |
|---|---|---|---|---|---|
| 1 | balkanlar | MODIS | 2002-07-01 → 2025-12-31 | 19.0, 34.5, 29.5, 44.5 | 141 000 |
| 2 | balkanlar | VIIRS S-NPP | 2012-01-01 → 2025-12-31 | 19.0, 34.5, 29.5, 44.5 | 417 000 |
| 3 | kafkasya | MODIS | 2002-07-01 → 2025-12-31 | 40.0, 38.25, 50.5, 43.75 | 174 000 |
| 4 | kafkasya | VIIRS S-NPP | 2012-01-01 → 2025-12-31 | 40.0, 38.25, 50.5, 43.75 | 326 000 |
| 5 | dogu_akdeniz | MODIS | 2002-07-01 → 2025-12-31 | 30.0, 29.0, 36.5, 36.0 | 86 000 |
| 6 | dogu_akdeniz | VIIRS S-NPP | 2012-01-01 → 2025-12-31 | 30.0, 29.0, 36.5, 36.0 | 234 000 |

Toplam yaklaşık 0,4 milyon MODIS + 1,0 milyon VIIRS satırı, ~110 MB CSV.

## 3. Form alanları (her talep için)
1. FIRMS Archive Download sayfası → "Create New Request".
2. Area of interest: Custom Area (dikdörtgen). Koordinat girişi yoksa haritada yaklaşık çiz ve formun gösterdiği köşe değerlerini not et; biraz geniş çizmek zarar vermez (clean.py kutuya göre keser).
3. Date Range: tablodaki başlangıç ve bitiş.
4. Source: MODIS C6.1 ya da SUOMI NPP VIIRS C2 (tabloya göre).
5. Format: CSV. Submit. Gelen e-postadaki zip'i `data/raw/archive/` altında kendi klasörüne aç (adım 14'teki gibi).
6. Her taleple ilgili (talep no, bölge, ürün, tarih aralığı) bir satır tut; Claude `docs/archive_files.md` ve regions.json'a bunlardan kaydeder.

## 4. Boşluğu API ile kapatma
Arşivi 2025-12-31'de bitiriyoruz (Türkiye'deki düzenle aynı: temizleme betiği değişmez). Arşiv gerçekte S-NPP için 2026-07-31'e, MODIS için 2026-08-31'e kadar uzanıyor, ama 2026'yı API tamamlar.
2026-01-01'den bugüne MODIS, S-NPP (31 Ekim'e kadar) ve NOAA-20 (2023-01-01'den bugüne, k_N20 örtüşmesi için): `python scripts/fetch.py --region <bölge> --preset s2`. s2 ön ayarı henüz yok, adım 48'de OPUS ekleyecek; bölge başına yaklaşık 410 istek, üç bölge için yaklaşık 1 230.

## 5. Kapsam dışı, gelecek çalışma: orta_dogu
Suriye, Irak, İran (W 36.5, S 25.0, E 63.5, N 39.75) bu hackathonda yapılmıyor. Sebep: yaklaşık 78 bin MODIS ve 473 bin VIIRS satır/yıl, çoğu petrol ve gaz meşalesi; 27 arşiv talebi (indirme için dört dikey dilim: 36.5–42.5, 42.5–49.5, 49.5–56.5, 56.5–63.5) ve adım 50'deki sabit kaynak ayıklaması gerekirdi. Sayfada ve README'de "gelecek çalışma" olarak yazılır.
