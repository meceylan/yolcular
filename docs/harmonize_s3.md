# Biyom kutuları: katsayılar ve kararlar (adım 81)

Tarih: 15 Kasım 2026. Kutular (5° × 5°, kara maskeli): `se_australia`, `california`, `amazon_arc`.
Yöntem Seviye 2 ile aynı, değiştirilmedi (`docs/harmonize_s2.md`, `docs/harmonize.md`): her takvim ayı için katsayı = ΣVIIRS S-NPP / ΣMODIS, 2012–2022, kesinti günleri çıkarılmış; bir yılı dışarıda bırakarak sınama; 2023–2025 bağımsız sınama.
Komutlar: `python scripts/harmonize.py --region <kutu>`, `python scripts/validate_s2.py --tag s3 se_australia california amazon_arc`, `python scripts/export.py --region <kutu>`.
Çıktılar: `data/processed/<kutu>/` (git'e girmez), `docs/coefficients_<kutu>.json`, `docs/harmonize_stats_<kutu>.json`, `web/data/<kutu>/`. Doğrulama: `docs/validation_s3.md`.

## Sonuç tablosu

| Kutu | Genel oran | Aylık hata | Yıllık hata (ort. / en kötü) | 2023–2025 sapma | Belirsizlik (ayların %68'i) | Karar |
|---|---|---|---|---|---|---|
| Güneydoğu Avustralya | 5,12 | %14,6 | %12,1 / %36,0 (2012) | +%8,2 | 0,76–1,35 | **deneysel** |
| Kaliforniya | 4,30 | %10,2 | %7,3 / %18,4 (2016) | %0,0 | 0,80–1,22 | **normal** |
| Amazon yayı | 3,84 | %6,8 | %2,5 / %10,0 (2021) | −%0,3 | 0,69–1,23 | **normal** |
| Türkiye (karşılaştırma) | 3,25 | %11,8 | %4,6 / %11,3 | +%1,5 | 0,85–1,34 | |

Karar eşiği: yıllık hata ortalaması ≤ %8 normal; %8–20 deneysel; > %20 ya da 2023–2025 sapması ±%20'yi aşarsa eklenmez.

- **Güneydoğu Avustralya: deneysel.** Yıllık hata ortalaması %12,1 (eşik %8–20), çünkü yangının az olduğu yıllarda (2012: +%36, 2021: +%33) tahmin belirgin fazla kalıyor.
- **Kaliforniya: normal.** Yıllık hata ortalaması %7,3 ve 2023–2025 toplamı tam tutuyor.
- **Amazon yayı: normal.** Yıllık hata ortalaması %2,5; dört bölgenin en iyisi, çünkü MODIS verisi çok ve yangın tipi yıldan yıla aynı.

## Katsayılar (MODIS → VIIRS S-NPP)

| Ay | Oca | Şub | Mar | Nis | May | Haz | Tem | Ağu | Eyl | Eki | Kas | Ara |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Güneydoğu Avustralya | 5,57 | 5,43 | 5,04 | 4,19 | 3,66 | 4,24 | 6,06 | 6,16 | 5,48 | 6,43 | 5,96 | 5,77 |
| Kaliforniya | 3,42 | 2,64 | 2,63 | 3,07 | 3,72 | 3,72 | 3,76 | 4,51 | 4,75 | 4,41 | 3,26 | 3,76 |
| Amazon yayı | 1,42 | 0,81 | 0,28 | 1,05 | 2,84 | 3,48 | 3,79 | 4,36 | 4,10 | 4,13 | 3,46 | 2,30 |

- **Amazon'da yağışlı mevsim katsayıları 1'in altında** (Şubat 0,81; Mart 0,28): bu aylarda MODIS, VIIRS'ten fazla tespit veriyor. Bu MODIS tespitleri neredeyse tamamı gündüz, dağınık ve tekrar etmiyor; VIIRS'in görmediği bu tespitler büyük olasılıkla yanlış alarm. Katsayı bunu ülke toplamında düzeltiyor ve etkisi küçük (Ocak–Nisan, yıllık toplamın yaklaşık %1'i).

## NOAA-20 çarpanı
Ortak 0,986 kuralı korundu. Kutuların kendi oranları (aynı yönde, S-NPP / NOAA-20): Avustralya 1,038, Kaliforniya 1,001, Amazon 1,022 (girdi dosyasındaki 0,963 / 0,999 / 0,979 bunların tersidir).
**Fark hata payı içinde:** ortak çarpan Kasım 2026 sonrası değerleri Avustralya'da yaklaşık %5, Amazon'da %3,5, Kaliforniya'da %1,5 düşük verir; aynı uyduların aylık oynaması ise ±%7–19 (ayların %68'i için 0,91–1,19). Avustralya'daki %5 üç yılda da aynı yönde olduğu için rastlantı değil, küçük ama sistematik bir eksik sayımdır.

## Aralık ve işaretler
Türkiye ile aynı biçim (`h_lo`, `h_hi`, `out_of_range`, `gap_days`). Sınanmış aralık dışı aylar:
- Güneydoğu Avustralya: 2003-02 (1,7 kat), 2004-05, 2004-06, 2005-06, 2006-05, 2006-06 (5,9 kat), 2011-06 ve iki küçük ay.
- Kaliforniya: **2008-06 (8,3 kat;** Haziran 2008 yıldırım yangınları), 2008-07 ve iki küçük ay.
- Amazon yayı: 28 ay; 2002–2007'nin neredeyse bütün kuru mevsimleri (örneğin 2004-07: 5,1 kat, 2004-09: 1,5 kat). O yıllarda yangın, kalibrasyon döneminde görülen her yıldan fazla. Sınamada yoğun aylarda fazla tahmin eğilimi görülmedi (gerçek / tahmin 1,01–1,16), ama aralık yine de geniş tutuldu.

## Başka bölgelerle çakışma
Yok. Üç kutu üç ayrı kıtada; birbirleriyle de, Türkiye ve Seviye 2 kutularıyla da kesişmiyor. Seviye 2'deki "Türkiye toprakları için Türkiye görünümü" kuralı bu kutular için gerekmiyor. Web verisine `overlaps_turkiye` alanı eklendi; sayfa kesişme notunu yalnızca gerçekten kesişen kutularda gösteriyor.

## Web
- Üç kutu `web/data/` altına yazıldı ve bölge listesine eklendi (liste `index.json`'dan okunuyor).
- Güneydoğu Avustralya listede "(experimental)" ile görünüyor; bandında kendi notu var: "in quiet fire years the estimate can be about a third too high".
- Kod değişikliği küçük: `export.py` (2 alan), `app.js` (4 satır: deneysel notu bölgeye göre, kesişme notu koşullu), `index.html` (Hakkında tablosuna 3 satır, Regions paragrafına 3 cümle).
