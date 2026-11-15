# Biyom kutuları: boyut ölçümü (adım 80)

Durum: 15 Kasım 2026, yalnızca satır sayısı tahmini. Hiçbir şey indirilmedi, veri dosyası yazılmadı.

## Yöntem
- FIRMS API, her kutu için 2023'te mevsim başına tek 5 günlük örnek (API sınırı 5 gün): 15 Ocak, 15 Nisan, 15 Temmuz, 15 Ekim başlangıçlı. MODIS (`MODIS_SP`) ve VIIRS S-NPP (`VIIRS_SNPP_SP`) ayrı. Toplam 40 istek.
- Yıllık satır = dört örneğin ortalaması ÷ 5 gün × 365.
- 2002–2025 toplamı: MODIS yıllık × 23,5 yıl (Temmuz 2002 – Aralık 2025) + VIIRS yıllık × 14 yıl (2012 – 2025). Her yılın 2023'e benzediği varsayıldı.
- Belirsizlik büyük (en az ±%50): örnek yalnızca 4 beş günlük pencere. Yangın mevsimi tepesi pencereye denk gelirse (Kanada Temmuz, Kaliforniya Ekim) yıllık değer şişer, denk gelmezse düşer. 2023 Kanada için rekor yangın yılıdır, bu yüzden Kanada tahmini muhtemelen birkaç kat fazla.

## Tablo (W, S, E, N; örnekler sırayla Oca, Nis, Tem, Eki)
| Kutu | Koordinat | MODIS örnek | VIIRS örnek | MODIS satır/yıl | VIIRS satır/yıl | MODIS 2002–2025 | VIIRS 2012–2025 | Toplam satır |
|---|---|---|---|---|---|---|---|---|
| Güneydoğu Avustralya | 146, -38, 151, -33 | [31, 215, 21, 8] | [170, 704, 114, 71] | 5,019 | 19,327 | 117,941 | 270,574 | **388,515** |
| Kaliforniya | -123.5, 36.5, -118.5, 41.5 | [1, 64, 60, 219] | [28, 293, 177, 1164] | 6,278 | 30,331 | 147,533 | 424,641 | **572,174** |
| Amazon yayı | -57, -12, -52, -7 | [23, 32, 204, 275] | [25, 27, 738, 776] | 9,746 | 28,580 | 229,019 | 400,113 | **629,132** |
| Sahel savanı (önerilen) | -5, 10, 0, 15 | [286, 89, 4, 62] | [2398, 886, 23, 372] | 8,048 | 67,142 | 189,134 | 939,984 | **1,129,118** |
| Kanada boreal (önerilen) | -115, 55, -110, 60 | [1, 2, 2516, 70] | [18, 49, 13952, 466] | 47,249 | 264,351 | 1,110,357 | 3,700,918 | **4,811,275** |

## İndirme süresi (API, 5 günlük parça)
- Kutu başına yaklaşık 2738 istek (MODIS 1 716 + VIIRS 1 022). Ölçülen ortalama 4.5 sn/istek, art arda gönderilirse kutu başına yaklaşık 3.4 saat; 3 kutu yaklaşık 10 saat.
- Hız sınırı (10 dakikada 5 000 işlem) bu işte sınırlayıcı değil, süreyi istek sırası belirler: yaklaşık 2738 istek sınırın çok altında.
- Bu yüzden API değil FIRMS Archive Download kullanılmalı: kutu başına 2 talep (MODIS, VIIRS S-NPP), e-postayla zip, dakikalar-saatler. Talepler adım 83'te kullanıcı işi.
- 2026 boşluğu API ile kapanır (Seviye 2'deki gibi, yaklaşık 410 istek/kutu).

## Öneri
Güneydoğu Avustralya, Kaliforniya ve Amazon yayı makul: her biri ~0,65 milyon satırın altında, üç ayrı yangın rejimi. Sahel de makul (~1,1 milyon), Kanada boreal tahmini 4.8 milyon satır olduğu için 3 milyon sınırını aşıyor ve seçilirse kutu 2,5°×2,5°'ye küçültülmeli. Sahel ve Kanada için kutu önerileri (5°×5°) yukarıdaki tabloda.
