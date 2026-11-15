# Seviye 2: harmonizasyon kararları (adım 50)

Tarih: 14 Kasım 2026. Bölgeler: `balkanlar`, `kafkasya`, `dogu_akdeniz`. Yöntem Türkiye ile aynı (`docs/harmonize.md`): katsayı = ΣVIIRS S-NPP / ΣMODIS, 2012–2022 (yörünge sabit), kesinti günleri çıkarılmış, bir yılı dışarıda bırakarak sınama, 2023–2025 bağımsız sınama.
Betikler: `scripts/s2_decide.py` (seçeneklerin sınaması → `docs/s2_stats.json`), `scripts/harmonize.py --region <bölge>` (seri), `scripts/validate_s2.py` (doğrulama). Bölge ayarları `data/regions.json` içinde `harmonize` alanında.
Çıktılar (git'e girmez): `data/processed/<bölge>/coefficients.json`, `harmonized_daily.parquet`, `harmonized_monthly.csv`. Belge kopyaları: `docs/coefficients_<bölge>.json`, `docs/harmonize_stats_<bölge>.json`.

## Kararlar (özet)

| | Balkanlar | Kafkasya | Doğu Akdeniz | Türkiye (karşılaştırma) |
|---|---|---|---|---|
| Katsayı | kendi, aylık (12) | kendi, aylık (12) | kendi, aylık ama yıllık orana çekilmiş | kendi, aylık (12) |
| Genel oran | 3,65 | 3,87 | 7,07 | 3,25 |
| Aylık hata (sınama) | %8,7 | %12,0 | %23,7 | %11,8 |
| Yıllık hata: ortalama / en kötü | %3,1 / %5,2 | %5,5 / %16,6 | %15,4 / %43,6 | %4,6 / %11,3 |
| 2023–2025 sınaması (toplam) | +%3,8 | +%0,7 | +%18,7 | +%1,5 |
| Belirsizlik (ayların %68'i, gerçek / tahmin) | 0,88–1,27 | 0,87–1,24 | 0,87–1,69 | 0,85–1,34 |
| NOAA-20 katsayısı | 0,986 | 0,986 | 0,986 | 0,986 |
| Karar | yayınla | yayınla | **"deneysel (kaba tahmin)" etiketiyle yayınla** (kullanıcı onayladı) | |

## 1. Kimin katsayısı?
**Karar: her bölge kendi katsayısını kullanır.** Bir yılı dışarıda bırakarak sınamada aylık hata (ağırlıklı):

| Seçenek (parametre sayısı) | Balkanlar | Kafkasya | Doğu Akdeniz |
|---|---|---|---|
| Kendi, aylık (12) | **%8,7** | **%12,0** | %23,9 |
| Kendi, mevsimlik (4) | %9,3 | %14,3 | %24,8 |
| Kendi, tek sabit (1) | %10,3 | %14,2 | %27,5 |
| Kendi, aylık, yıllık orana çekilmiş (λ = 300) | %8,7 | %11,9 | **%23,7** |
| Türkiye'nin aylık katsayıları (0) | %14,4 | %17,5 | %52,9 |
| Türkiye'nin katsayıları × bölge ölçeği (1) | %14,3 | %19,1 | %30,5 |

- Türkiye'nin katsayıları her üç bölgede belirgin kötü: mevsim deseni farklı (Türkiye'de Haziran 1,98; Balkanlar'da 3,22, Kafkasya'da 3,80). Doğu Akdeniz'de Türkiye katsayıları VIIRS'i yarı yarıya eksik tahmin ediyor (2023–2025: −%42).
- Karışım (Türkiye deseni × bölge ölçeği) de kendi katsayılarından kötü. Karışım kullanılmadı.

### Doğu Akdeniz'de oran neden 7?
İki neden var, ikisi de ölçüldü:
1. **Etiketlenmemiş sabit kaynaklar seride kalıyor.** Filtreden geçen VIIRS tespitlerinin %14,8'i, yılın en az 10 farklı ayında ve en az 30 ayrı günde tespit veren 237 küçük hücrede (0,01°) ve %94'ü gece. Bu profil yangın değil, sanayi. Aynı pay Türkiye'de %3,4, Balkanlar'da %2,2, Kafkasya'da %2,6. Bu kaynakları VIIRS görüyor, MODIS çoğunlukla görmüyor; oranı yukarı itiyor.
2. **Yangınlar küçük.** Bu hücreler çıkarıldığında bile oran 6,3 (7,07'den). Bölgenin yangınlarının büyük kısmı Nil deltasındaki hasat sonrası tarla yakımı (FRP medyanı 2,9 MW; Türkiye'de 4,4): VIIRS'in gördüğü, MODIS'in çoğunu kaçırdığı küçük yangınlar.

### FIRMS'in "sabit kaynak" dediği tespitler gerçekten sanayi mi? Evet
Karadaki VIIRS tespitlerinin %44,4'ü sabit kaynak işaretli (106 369 tespit). Üç ayrı kontrol:

| Kontrol | Sabit kaynak işaretliler | Yangın sayılanlar |
|---|---|---|
| Mevsimsellik (en yoğun ay / ortalama ay) | 1,12 (yıl boyu düz) | 2,61 (Eylül–Ekim tepesi) |
| Gece payı | %92 | %37 |
| Kalıcı hücrede olanlar (≥ 30 gün, ≥ 10 farklı ay) | %99,4 | %13,5 |
| En çok 3 gün görülmüş hücrede olanlar | 17 tespit (%0,0) | %40 |

- **Nil deltası** (30,0–31,7 K, 30,0–32,4 D): sabit kaynak işaretliler burada da yıl boyu düz (1,13) ve %98,7'si kalıcı hücrelerde. Yangın sayılanlar ise Eylül'de %25, Ekim'de %35 ile keskin bir tepe yapıyor: pirinç hasadı sonrası anız yakma **seride duruyor, elenmemiş**.
- Sabit kaynakların %70'i 12 kümede toplanıyor; konumları bilinen sanayi bölgeleriyle örtüşüyor (Süveyş Körfezi kıyısı, Kahire'nin güneyi, Beni Suef, Sina, İdku, Hayfa, Ramla, Kıbrıs'ın güney kıyısı). Tesis adları bu veriden doğrulanmadı; konum eşleşmesi bir çıkarım.
- Sonuç: yanlışlıkla elenen tarım yangını bulunmadı (kalıcı olmayan hücrede yalnızca 17 işaretli tespit). Sorun ters yönde: bir kısım sanayi kaynağı işaretlenmemiş ve seride kalmış.

### Denenen ama uygulanmayan: kalıcılık filtresi
Kalıcı hücreler (≥ 30 gün ve ≥ 10 farklı ay) iki sensörden çıkarılınca Doğu Akdeniz'de:

| | Şimdiki filtre | + kalıcılık filtresi |
|---|---|---|
| Genel oran | 7,07 | 6,29 |
| Aylık hata | %23,7 | %21,3 |
| Yıllık hata (ortalama / en kötü) | %15,4 / %43,6 | %11,6 / %45,9 |
| 2023–2025 sınaması | +%18,7 | +%11,0 |

İyileştiriyor ama bölgeyi Türkiye düzeyine getirmiyor, ve onaylı filtre kararını (adım 28) bir bölge için değiştirmek anlamına geliyor. **Uygulanmadı**; istenirse sonraki iş olarak eklenebilir (VIIRS'in %13'ünü, MODIS'in %4'ünü çıkarır). Diğer bölgelerde etkisi önemsiz.

## 2. Az verili bölgede parametre sayısı
- Balkanlar ve Kafkasya'da en az verili ayda bile 675 ve 750 MODIS tespiti var; 12 katsayı sağlam, aylık model en iyisi. Türkiye ile aynı yöntem, değişiklik yok.
- **Doğu Akdeniz'de MODIS toplamı 13 284** (Türkiye'nin yedide biri); Mart ve Nisan'da 11 yılda yalnızca 184 ve 247 tespit var ve ham katsayılar 16,3 ve 17,9'a çıkıyor. Seçilen yöntem: aylık katsayı, az verili aylarda bölgenin yıllık oranına (7,07) çekilir:
  `c_ay = (ΣVIIRS_ay + 300 × 7,07) / (ΣMODIS_ay + 300)`. Çok verili ayda (Ekim: 3 392 tespit) katsayı neredeyse değişmez (6,32 → 6,39); az verili ayda yıllık orana yaklaşır (Nisan: 17,85 → 11,94).
- Mevsimlik (4) ve sabit (1) seçenekler daha kötü (yukarıdaki tablo). Çekilmiş aylık, 2023–2025 sınamasında da en iyisi (+%18,7; düz aylık +%22,8).
- λ = 100, 300, 1000 denendi; sonuçlar birbirine çok yakın (%23,4 / %23,7 / %24,9). 300 seçildi.

### Katsayılar
| Ay | Oca | Şub | Mar | Nis | May | Haz | Tem | Ağu | Eyl | Eki | Kas | Ara |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Balkanlar | 5,76 | 3,42 | 3,71 | 4,21 | 4,28 | 3,22 | 3,68 | 3,84 | 3,57 | 3,21 | 3,50 | 6,10 |
| Kafkasya | 4,23 | 3,36 | 3,41 | 4,24 | 4,47 | 3,80 | 3,98 | 4,13 | 4,26 | 3,38 | 4,00 | 5,41 |
| Doğu Akdeniz | 8,11 | 9,07 | 10,57 | 11,94 | 7,72 | 6,04 | 6,07 | 7,00 | 7,12 | 6,39 | 6,35 | 7,73 |
| Türkiye | 3,31 | 3,24 | 3,73 | 4,48 | 2,69 | 1,98 | 3,16 | 3,91 | 4,16 | 3,69 | 2,62 | 3,13 |

## 3. NOAA-20 katsayısı
**Karar: tüm bölgelerde tek ortak sabit, 0,986** (Türkiye'nin yayındaki değeri).

| | Balkanlar | Kafkasya | Doğu Akdeniz | Türkiye | Dört bölge birlikte |
|---|---|---|---|---|---|
| Bölgenin kendi k'sı (S-NPP / NOAA-20) | 0,994 | 0,997 | 0,974 | 0,986 | 0,989 |
| Yıllara göre | 0,987 / 0,958 / 1,043 | 0,949 / 1,001 / 1,023 | 0,988 / 0,988 / 0,941 | 0,981 / 0,956 / 1,033 | |
| Aylık hata: kendi k (bir yıl dışarıda) | %7,6 | %7,9 | %6,6 | %7,7 | |
| Aylık hata: ortak 0,986 | %6,9 | %7,5 | %6,4 | %7,1 | |

- Bölgeler arası fark (0,974–0,997), aynı bölgenin yıldan yıla oynamasından (±0,04) küçük. Bölgeye özel k, sınamada ortak sabitten **daha iyi değil**.
- Ortak sabit ayrıca kesişen alanlarda (madde 6) tutarlılık sağlar ve Türkiye'nin yayındaki değerini değiştirmez. (`s2_overlap_input.md` aynı oranı ters yönde, NOAA-20 / S-NPP olarak veriyor: 1,006 / 1,003 / 1,026.)

## 4. Aralık ve tahmin işaretleri
Türkiye ile aynı biçim, `harmonized_monthly.csv` içinde: `h_lo`, `h_hi` (sayfada `likely_low`, `likely_high`), `out_of_range`, `gap_days`, `src` (`M` ve `N` = tahmin).
- Aralık her bölgenin kendi sınamasından: ayların %68'i için gerçek / tahmin oranı (yukarıdaki tablo). Sınanmış aralığın dışındaki aylarda daha geniş aralık (%90): Balkanlar 0,72–1,54; Kafkasya 0,76–1,43; Doğu Akdeniz 0,70–2,41.
- Sınanmış aralık dışı aylar (`out_of_range`):
  - Balkanlar: 2006-07, 2006-11, 2007-01, 2007-06, **2007-07 (3,3 kat)**, 2007-08, 2010-11, 2011-10, 2011-11. 2007 yazı (Yunanistan'daki büyük yangınlar) serinin en yüksek yılı ve tahmini en belirsiz olanı.
  - Kafkasya: 2002-11, 2003-05, 2004-01, 2004-08, 2006-08, 2007-05, 2008-12, 2010-08, **2010-11 (2,9 kat)**, **2010-12 (2,8 kat)**.
  - Doğu Akdeniz: 2010-11, **2010-12 (3,6 kat)**.
- Yoğun aylarda fazla tahmin eğilimi Balkanlar'da ve Kafkasya'da zayıf (çok yoğun aylarda gerçek / tahmin 0,98 ve 0,92; Türkiye'de 0,85), Doğu Akdeniz'de güçlü (0,65).

## 5. MODIS başlangıcı: tek kural
**Kural: tüm bölgelerde MODIS 4 Temmuz 2002'den başlar; 1–3 Temmuz 2002 atılır ve veri boşluğu sayılır.**
- Gerekçe: Türkiye verisinde 1–3 Temmuz 2002'de yalnızca Terra var; Aqua'nın ilk tespiti 4 Temmuz. Katsayılar iki uydunun toplamından hesaplandığı için tek uydulu günler olduğundan düşük tahmin verir. Aqua'nın olmadığı diğer günler (30 Tem – 7 Ağu 2002) zaten boşluk olarak işaretli; 1–3 Temmuz da aynı listeye eklendi (`scripts/filters.py`).
- Türkiye'ye uygulandı (`regions.json` → `modis_first_date`, clean → grid → harmonize yeniden çalıştırıldı): **Temmuz 2002 değeri 2 673'ten 2 505'e indi (−%6,3), çünkü yalnızca Terra'nın çalıştığı ilk üç günün 53 tespiti seriden çıktı;** o ayın boşluk günü 2'den 5'e çıktı. Başka hiçbir ay değişmedi (toplam 747 310 → 747 142). Seri yine Temmuz 2002'den başlıyor.
- **Canlı sitedeki Türkiye verisi henüz eski değeri gösteriyor**; export adım 51'de yeniden çalıştırılınca güncellenecek.

## 6. Türkiye ile kesişen kutular
Kutular Türkiye topraklarını da içeriyor. Aynı hücre, Türkiye görünümünde Türkiye'nin, kutu görünümünde kutunun katsayısıyla çarpılıyor. Etki yalnızca 2012 öncesinde var (sonrası doğrudan VIIRS, ikisinde aynı).

| Kutu | Kesişen hücre | Kutunun MODIS verisindeki payı | 2002–2011 toplam fark (kutu katsayısı / Türkiye katsayısı) | Tek tek yıllarda |
|---|---|---|---|---|
| Balkanlar (Trakya, Batı Anadolu) | 219 | %8,3 | +%0,3 | −%2 … +%74 |
| Kafkasya (Kuzeydoğu Anadolu) | 146 | %3,5 | +%8,0 | +%2 … +%28 |
| Doğu Akdeniz (güney kıyı) | 2 | %0,5 | +%79 (43 tespit) | |

- Toplamda fark küçük (Balkanlar) ya da orta (Kafkasya), ama tek tek yıllarda büyük olabiliyor: Trakya'da yangınların Haziran'da yoğunlaştığı bir yılda Balkan katsayısı (3,22) Türkiye'ninkinden (1,98) %60 fazla verir.
- **Kural (belgelendi, kod değişmedi):** Her bölge kendi kutusu için ayarlanmış ayrı bir görünümdür; görünümler arasında toplama yapılmaz. **Türkiye toprakları için geçerli seri Türkiye görünümüdür.** Kutu görünümlerinde, Türkiye'ye düşen kısmın 2012 öncesi değerleri Türkiye görünümünden farklı çıkabilir; sayfada kutu bölgeleri için bir cümleyle belirtilmeli.
- Kalıcı çözüm (yapılmadı, gelecek iş): katsayıyı görünüme değil hücreye bağlamak. Bunun için kutulardaki tespitlerin "Türkiye içinde / dışında" diye ayrılması ve ızgaranın yeniden üretilmesi gerekir.

## 7. Yayın kararı
- **Balkanlar: yayınla.** Sınama Türkiye'den iyi.
- **Kafkasya: yayınla.** Sınama Türkiye ile aynı düzeyde; en zayıf yıllar 2015 (+%16,6) ve 2014 (−%11,5).
- **Doğu Akdeniz: "deneysel (kaba tahmin)" etiketiyle yayınlanır** (kullanıcı kararı, 14 Kasım 2026). Aylık hata Türkiye'nin 2 katı, yıllık hata 3 katı, en kötü yıl %44, 2025 sınaması +%51. 2012 sonrası (ölçüm) değerleri sağlam; kaba olan 2012 öncesi tahminler. `regions.json` içinde `harmonize.quality = "experimental"` olarak işaretlendi; sayfanın bunu göstermesi adım 51–52'nin işi.

## Adım 51 (OPUS) için
- `harmonize.py` üç bölge için çalıştı; çıktılar `data/processed/<bölge>/` altında, Türkiye ile aynı adlarda ve biçimde. Yeniden çalıştırmak gerekirse: `python scripts/harmonize.py --region <bölge>`.
- Yapılacak: `export.py --region <bölge>` (dört bölge; Türkiye de, Temmuz 2002 değiştiği için), `meta.json` → `k_n20 = 0.986`.
- Sayfa: `harmonize.quality == "experimental"` ise bölge adının yanında "experimental: rough estimate before 2012" etiketi; kutu bölgelerinde "Box regions overlap Türkiye; for Turkish territory use the Türkiye view" notu; Temmuz 2002 artık `gap_days = 5` (işaretli).
- `docs/coefficients.json` yalnızca Türkiye'nindir; diğerleri `docs/coefficients_<bölge>.json`.
