# Dönüşüm katsayıları (adım 31)

Tarih: 14 Kasım 2026. Betik: `scripts/harmonize.py --region turkiye`. Sayılar: `docs/harmonize_stats.json`. Katsayılar: `docs/coefficients.json` (kopyası `data/processed/turkiye/coefficients.json`).
Ara çıktılar (git'e girmez): `data/processed/turkiye/harmonized_daily.parquet` (hücre × gün: `h`, `m`, `v`, `src`) ve `harmonized_monthly.csv` (ülke × ay, belirsizlik aralığı ve işaretlerle).

## Yöntem (tek paragraf)
MODIS ve VIIRS S-NPP 2012'den beri aynı yangınlara birlikte bakıyor. İkisinin birlikte ve MODIS uydularının yörüngesi bozulmadan çalıştığı 2012–2022 yıllarında, uydu kesintisi olan günleri çıkarıp her takvim ayı için iki sayıyı topladık: o ayda VIIRS'in toplam tespiti ve MODIS'in toplam tespiti. Birincinin ikinciye bölümü o ayın katsayısıdır (örneğin Eylül için 4,16: Eylül aylarında VIIRS, MODIS'in gördüğünün 4,16 katını görmüş). VIIRS'in olmadığı dönemde (Temmuz 2002 – Ocak 2012) her hücredeki MODIS sayısını o ayın katsayısıyla çarparak "VIIRS görseydi kaç tespit olurdu" tahminini elde ediyoruz. Şubat 2012'den sonra VIIRS'in kendi sayısı kullanılıyor, hiçbir düzeltme yapılmıyor. Kasım 2026'dan itibaren S-NPP yerine geçen NOAA-20'nin sayısı, iki uydunun birlikte çalıştığı 2023–2025'ten hesaplanan tek bir katsayıyla (0,986) çarpılıyor. 2012 öncesi değerler ölçüm değil tahmindir.

## MODIS → VIIRS S-NPP katsayıları
Toplamların oranı (ΣVIIRS / ΣMODIS), 2012–2022, kesinti günleri hariç:

| Oca | Şub | Mar | Nis | May | Haz | Tem | Ağu | Eyl | Eki | Kas | Ara |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 3,31 | 3,24 | 3,73 | 4,48 | 2,69 | 1,98 | 3,16 | 3,91 | 4,16 | 3,69 | 2,62 | 3,13 |

Katsayı bölgeye özeldir (Türkiye). Seviye 2–4 bölgeleri için aynı betik kendi katsayılarını hesaplar.

### Neden bu model? (bir yılı dışarıda bırakarak sınama)
Her seferinde bir yıl kenara ayrıldı, katsayı kalan yıllardan hesaplandı ve ayrılan yılın VIIRS sayısı MODIS'ten tahmin edildi.

| Model | Aylık hata (ağırlıklı) | Yıllık hata (ortalama / en kötü) | 2023–2025 sınaması (toplam) |
|---|---|---|---|
| A: tek sabit (3,25) | %24,6 | %6,0 / %10,6 | +%4,0 |
| **B: aya göre (seçilen)** | **%11,8** | **%4,6 / %11,3** | **+%1,5** |
| C: ay + gündüz/gece ayrı | %14,2 | %6,7 / %23,6 | +%7,4 |
| D: ay + alt bölge | %12,3 | %6,0 / %15,8 | +%5,2 |

- Aya göre katsayı, sabit katsayının aylık hatasını yarıya indiriyor.
- **Gündüz/gece ayrımı kötüleştiriyor:** kışın MODIS gece tespiti neredeyse yok (Aralık: 11 yılda 8 tespit), gece katsayıları 30–80 gibi anlamsız değerlere çıkıyor. Adım 30'daki öneri sınamayı geçemedi, kullanılmadı.
- **Alt bölge ayrımı** alt bölge düzeyindeki hatayı biraz düşürüyor (%20,2 → %17,6) ama ülke toplamını iyileştirmiyor ve yeni yıllarda daha kötü. Basit olan seçildi.

Sınamada yıllık tahmin ve gerçek (model B):

| Yıl | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Hata | +%1,0 | −%0,5 | −%2,4 | +%10,0 | −%1,2 | −%2,7 | +%2,1 | −%6,0 | −%11,3 | +%8,8 | +%4,5 |

### Aqua ve Terra geçiş saati kayması
- Kayma 2023'te başlıyor (adım 30). Katsayı **yalnızca 2012–2022'den** hesaplandı; kaymış yıllar katsayıya girmiyor.
- MODIS'ten tahmin edilen dönem (2002–2011) de yörüngenin sabit olduğu dönem, yani katsayı uygulandığı dönemle aynı koşullarda ölçüldü.
- Etkisi küçük: katsayı 2012–2025'in tamamından hesaplansaydı 2002–2011 toplamı yalnızca %0,1 değişirdi. Kaymış yıllar (2023–2025) bağımsız sınama olarak kullanıldı: toplam hata +%1,5 (yıllara göre +%0,2, +%1,8, +%2,6). Hata her yıl aynı yönde ve büyüyor: MODIS giderek daha az görüyor. 2026'da bu daha da belirgin (adım 28).
- **Sonuç:** 2023 sonrasının MODIS sayıları katsayı için kullanılmamalı ve 2026 sonrasında "MODIS'ten VIIRS tahmini" yapılmamalı. Seride buna gerek de yok: 2012'den sonra değerler doğrudan VIIRS'ten geliyor.

## NOAA-20 → S-NPP katsayısı
2023–2025, iki uydunun da veri verdiği günler: S-NPP 82 280, NOAA-20 83 478 tespit.

| | k (S-NPP / NOAA-20) |
|---|---|
| **Tek sabit (seçilen)** | **0,986** |
| Yıllara göre | 0,981 / 0,956 / 1,033 |
| Aylara göre | 0,85 (Kasım) – 1,10 (Haziran) |

- İki uydu neredeyse aynı sayıyor (fark %1,4). Aylık katsayı sınamada hatayı yalnızca %7,7'den %7,4'e indiriyor; tek sabit seçildi.
- **Kasım için not:** Kasım aylarında NOAA-20, S-NPP'den belirgin fazla saymış (k = 0,85). Üç yıllık veriyle bunun kalıcı olup olmadığı söylenemez. Kasım 2026'nın uyumlu değeri (1–13 Kasım: 483) aylık katsayıyla yaklaşık %13 daha düşük (~418) çıkardı.

## Belirsizlik
Sınamada her ay için "gerçek / tahmin" oranına bakıldı.

| | Gerçek değer tahminin kaç katı |
|---|---|
| Ayların %68'i | 0,85 – 1,34 |
| Ayların %90'ı | 0,68 – 1,70 |
| Yıllık toplamda | ortalama ±%5, en kötü ±%11 |
| NOAA-20 ayları (%68) | 0,93 – 1,08 |

- Tek bir ayın tahmini ±%15–35 oynayabilir; yıllık toplam çok daha güvenilir.
- Bu aralıklar `harmonized_monthly.csv` içinde `h_lo` ve `h_hi` olarak yazıldı. Resmî bir güven aralığı değil, sınamadaki dağılımın özeti.
- **Tek hücrenin tek ayı için tahmin kabadır** (adım 30: logaritmik korelasyon 0,73) ve MODIS'in sıfır gösterdiği hücre sıfır kalır. Sayfada 2012 öncesi için küçük dikdörtgen seçimleri bu yüzden dikkatle yorumlanmalı.

### Etkinlik düzeyi: yoğun aylarda fazla tahmin
Sınamada aylar, o takvim ayının olağan düzeyine göre gruplandı:

| Ayın MODIS sayısı (o ayın medyanına göre) | Ay sayısı | Gerçek / tahmin |
|---|---|---|
| Yarısından az | 13 | 1,38 |
| Olağan (0,5–1,5 kat) | 81 | 1,05 |
| Yoğun (1,5–2,5 kat) | 30 | 0,94 |
| Çok yoğun (2,5 katından fazla) | 7 | 0,85 |

Yoğun aylarda tahmin %6–15 fazla, sakin aylarda %38 eksik kalıyor (adım 23'teki "oran etkinlik düzeyine bağlı" bulgusunun karşılığı). Doğrusal yöntem bunu düzeltmiyor; düzeltmek, hücrelerin toplanabilirliğini bozardı.

### Sınanmış aralığın dışındaki aylar
Bir ay, MODIS sayısı kalibrasyon yıllarında (2012–2022) aynı takvim ayında görülen en yüksek değeri aşıyorsa "sınanmış aralık dışı" sayılır. Bu aylar `out_of_range` olarak işaretlendi ve daha geniş aralık (0,68–1,70) verildi.

| Ay | MODIS | Sınanmış en yüksek | Kat |
|---|---|---|---|
| 2009-08 | 4 025 | 2 116 | 1,90 |
| 2009-09 | 4 867 | 3 610 | 1,35 |
| 2009-10 | 4 170 | 2 052 | 2,03 |
| 2010-08 | 2 775 | 2 116 | 1,31 |
| 2011-08 | 2 901 | 2 116 | 1,37 |
| 2011-09 | 5 452 | 3 610 | 1,51 |
| 2011-10 | 3 536 | 2 052 | 1,72 |
| 2006-08 | 2 251 | 2 116 | 1,06 |
| 2011-12 | 777 | 774 | 1,00 |

- Bu aylar için katsayı hiç sınanmadığı düzeyde kullanılıyor. Yukarıdaki tabloya göre **büyük olasılıkla fazla tahmin** (en az %15). 2009 ve 2011'in yıllık uyumlu toplamları (65 656 ve 61 117) bu yüzden üst sınır gibi okunmalı; aralıkları 47 000–106 000 ve 44 000–100 000.
- Alt bölge düzeyinde aşım daha büyük: İç Anadolu 2009-08, 2009-10, 2011-08, 2011-10'da sınanmış en yüksek düzeyin 3,2–3,6 katı; Çukurova 2003–2009 Haziran aylarında 1,7–5,1 katı (o yıllarda Çukurova'da hasat yangını bugünkünden çok daha fazla). Tam liste `docs/coefficients.json` içinde (`out_of_tested_range_zone_months`).

## Uyumlu seri (yıllık)
| Yıl | Uyumlu | Kaynak | Ham MODIS | Ham VIIRS |
|---|---|---|---|---|
| 2002 (Tem–Ara) | 19 603 | MODIS × katsayı | 5 279 | |
| 2003 | 21 135 | MODIS × katsayı | 6 757 | |
| 2004 | 24 404 | MODIS × katsayı | 6 997 | |
| 2005 | 24 654 | MODIS × katsayı | 7 297 | |
| 2006 | 28 890 | MODIS × katsayı | 8 460 | |
| 2007 | 26 493 | MODIS × katsayı | 7 816 | |
| 2008 | 17 212 | MODIS × katsayı | 5 231 | |
| 2009 | 65 656 | MODIS × katsayı (aralık dışı aylar var) | 18 488 | |
| 2010 | 42 387 | MODIS × katsayı (aralık dışı ay var) | 12 513 | |
| 2011 | 61 117 | MODIS × katsayı (aralık dışı aylar var) | 17 153 | |
| 2012 | 21 541 | Ocak MODIS, sonrası VIIRS | 6 226 | 21 389 |
| 2013 | 35 142 | VIIRS | 10 440 | 35 142 |
| 2014 | 19 556 | VIIRS | 5 897 | 19 556 |
| 2015 | 49 675 | VIIRS | 16 584 | 49 675 |
| 2016 | 41 475 | VIIRS | 12 507 | 41 475 |
| 2017 | 27 886 | VIIRS | 8 446 | 27 886 |
| 2018 | 22 725 | VIIRS | 7 114 | 22 725 |
| 2019 | 25 850 | VIIRS | 7 426 | 25 850 |
| 2020 | 28 831 | VIIRS | 7 869 | 28 831 |
| 2021 | 26 873 | VIIRS | 9 005 | 26 873 |
| 2022 | 14 204 | VIIRS | 4 873 | 14 204 |
| 2023 | 25 795 | VIIRS | 7 986 | 25 795 |
| 2024 | 32 070 | VIIRS | 10 809 | 32 070 |
| 2025 | 24 415 | VIIRS | 8 138 | 24 415 |
| 2026 (13 Kas'a kadar) | 19 721 | VIIRS; Kasım NOAA-20 × 0,986 | 6 726 | 19 728 |

## Adım 33 (OPUS) için
- `export.py` uyumlu veriyi `harmonized_daily.parquet` dosyasından okuyabilir: `h`, `m`, `v` sütunlarını aya (ve `mtd` için güne) göre toplamak yeterli; katsayı zaten uygulanmış.
- `meta.json` → `viirs_switch.k_n20 = 0.986`, `harmonized = true`.
- Öneri (sözleşmeye ek alan, var olanlar değişmez): `monthly.json` içine `h_lo`, `h_hi` ve `out_of_range` dizileri; sayfa tahmin aylarında aralığı, aralık dışı aylarda "sınanmamış düzey, büyük olasılıkla fazla tahmin" notunu göstersin. Değerler `harmonized_monthly.csv` içinde hazır.
