# Veri boşlukları

Adım 23'teki veri kontrol raporunda bu günler işaretlenir; adım 30–31'de (örtüşme ve katsayı) bu günler hesaba katılmaz.

## 1. MODIS: NASA'nın resmî uyarısı
Kaynak: FIRMS indirme README'si (https://firms.modaps.eosdis.nasa.gov/download/Readme.txt), "IMPORTANT" bölümü.

| Dönem | Durum | Bizim dönemimizde mi? |
|---|---|---|
| 2001 Haziran sonu – Temmuz başı | Veri eksik | Hayır (dönem 2002-07'de başlıyor) |
| 2002 boyunca | Dağınık eksik günler | **Evet** (2002-07 – 2002-12) |
| 2007 Ağustos ortasından itibaren | Bir kısmı eksik | **Evet** |
| 21 Nisan 2009 | Günün bir kısmı eksik | **Evet** |
| 22 Nisan 2009 | Tamamen eksik | **Evet** |

README ayrıca veri setinde hatalı veri de bulunabileceğini belirtiyor.
2002 ve 2007'deki eksik günlerin tam listesi verilmiyor; 2002–2011 MODIS API ile çekildikten sonra (adım 21) tespitsiz günler adım 23'te listelenecek.

## 2. VIIRS S-NPP: arşiv verisinden çıkan boşluklar (resmî değil, bizim tespitimiz)
Türkiye arşivinde yaz aylarında (yangın mevsimi) hiç tespit olmayan ardışık günler. Yazın birden çok gün sıfır tespit olması uydu kesintisine işaret eder.

| Dönem | Gün |
|---|---|
| 2022-07-27 – 2022-08-10 | 15 |
| 2024-05-30 – 2024-06-03 | 5 |
| 2024-07-10 – 2024-07-15 | 6 |
| 2024-07-25 – 2024-07-28 | 4 |
| 2024-09-26 | 1 |
| 2025-07-06 – 2025-07-07 | 2 |

- Aynı günlerde MODIS'te tespit var, yani gerçekten yangın yok demek değil, VIIRS verisi yok demek.
- 2022 yazında VIIRS yıllık sayısının düşük çıkmasının (26 567) bir nedeni bu 15 günlük boşluk.
- **VIIRS S-NPP 2 Kasım 2026'da veri üretmeyi bıraktı** (adım 15). 1 Kasım 2026'dan itibaren NOAA-20 kullanılıyor (adım 18 kararı).

## 2b. Adım 23'te bulunan ek boşluklar (bizim tespitimiz)
| Uydu | Dönem | Gün | Not |
|---|---|---|---|
| Aqua (MODIS) | 2002-07-30 – 2002-08-07 | 9 | O günlerde yalnızca Terra var |
| Aqua (MODIS) | 2020-08-30 – 2020-09-02 | 4 | O günlerde yalnızca Terra var |
| Terra + Aqua | 2014-09-28 – 2014-09-29 | 2 | İkisi birden tespitsiz |
| VIIRS S-NPP | 2026-06-01 – 2026-06-02 | 2 | |
| VIIRS S-NPP | 2026-07-11 – 2026-07-16 | 6 | |

- MODIS 2002 (Tem–Eki) ve 2007 (15 Ağu – 31 Eki) dönemlerinde tümüyle tespitsiz gün bulunmadı; NASA'nın sözünü ettiği eksikler gün içi parçalar olabilir, sayımdan görülemiyor.
- 21–22 Nisan 2009'da toplam 6 tespit var; seriye etkisi yok.
- Ayrıntı: `docs/data_report.md`.

## 3. Kışın tespitsiz günler (boşluk değil)
2012–2025 boyunca MODIS'te 655, VIIRS'te 70 gün tespitsiz. MODIS'teki günlerin çoğu Kasım–Mayıs arasında; kışın yangın azlığından kaynaklanıyor, veri boşluğu sayılmaz.
