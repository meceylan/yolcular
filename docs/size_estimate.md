# Veri boyutu tahmini (adım 17)

Betik: `scripts/estimate_size.py`. Ham ölçümler: `docs/size_estimate_samples.csv`, tablo: `docs/size_estimate.csv`.

## Yöntem
- **Türkiye (gerçek):** arşiv dosyalarından (`docs/archive_files.md`). Satır başına ~78 bayt (MODIS) ve ~80 bayt (VIIRS) CSV.
- **Diğer bölgeler (tahmin):** 2025'in her ayının 15'inde 1 günlük API örneği (12 gün) × 365. Aynı örnek Türkiye kutusu için de alındı. Türkiye arşivinin gerçek 2025 sayısı örnekten çıkan tahminin ~%74'ü (MODIS) ve ~%70'i (VIIRS). Fark iki kaynaktan geliyor: arşiv ülke sınırıyla kesilmiş, örnek günler ise yalnızca birer gün. Bu oran diğer bölgelere düzeltme olarak uygulandı. Gerçek değer büyük olasılıkla düzeltilmiş tahmin ile ham örnek tahmini arasında.
- S2 kutuları taslaktır, kesin hâli adım 48'de belirlenir.

## Yıllık satır sayısı (2025 temel alındı)

| Bölge | Izgara | Hücre | MODIS satır/yıl | VIIRS satır/yıl | Ham CSV MB/yıl |
|---|---|---|---|---|---|
| Türkiye (ülke, arşiv, gerçek) | 0,25° | 2 028 | 9 499 | 39 421 | 3,9 |
| Balkanlar | 0,25° | 2 176 | 6 000–8 000 | 32 000–45 000 | 3–4 |
| Kafkasya | 0,25° | 1 248 | 6 000–8 000 | 20 000–28 000 | 2–3 |
| Orta Doğu | 0,25° | 12 064 | 67 000–89 000 | 410 000–585 000 | 38–54 |
| Doğu Akdeniz | 0,25° | 1 904 | 2 000–2 500 | 18 000–26 000 | 1,6–2,3 |
| S3 Avrupa + Akdeniz + K. Afrika | 0,5° | 15 960 | 126 000–169 000 | 550 000–780 000 | 54–76 |
| S4 Dünya | 1° | 64 800 | 2,5–3,4 milyon | 12–17 milyon | 1 200–1 600 |

Türkiye ortalaması 2012–2025: MODIS ~9 900, VIIRS ~43 300 satır/yıl.

## Tüm dönem ve indirme yükü
API tek istekte en fazla 5 gün veriyor. Ölçülen süre: Türkiye kutusu için bir istek ~1–2 saniye. Büyük kutular API işlem sayacını daha hızlı dolduruyor (sınır: 10 dakikada 5000 işlem).

| İş | Süre | İstek | Ham veri | Gerçekçi mi? |
|---|---|---|---|---|
| S1: Türkiye MODIS 2002-07 – 2011 (API) | 9,5 yıl | ~700 | ~8 MB | **Evet**, ~15–25 dk |
| S1: Türkiye 2012–2025 | arşivde var | 0 | 59 MB | **Hazır** |
| S2: 4 bölge, MODIS 2002–2025 + VIIRS 2012–2025 (API) | 23,5 + 14 yıl | ~11 000 | ~650–900 MB | **Zor**: 4–6 saat istek, Orta Doğu payı %85 |
| S3: 0,5° yalnızca özet (API) | 23,5 + 14 yıl | ~2 700 (çok ağır kutu) | ~1,5–2 GB | **Hayır** (API ile), ancak arşiv talebiyle |
| S4: Dünya | | | ~35 GB+ | **Hayır**, gelecek çalışma |

## Sonuç ve öneriler
1. **S1 rahat.** 2012–2025 elimizde; 2002–2011 MODIS'i API ile ~20 dakikada çekeriz.
2. **S2 için API yerine arşiv talebi gerekir.** Yük büyük ölçüde Orta Doğu'dan geliyor (petrol/gaz meşaleleri; adım 50). Öneri: S2 bölgeleri için şimdiden FIRMS Archive Download talebi açılsın (kullanıcı işi, adım 14 gibi). Olmazsa S2'de Orta Doğu çıkarılır ya da yalnızca 2012–2025'e indirilir.
3. **S3 yalnızca arşiv talebiyle ve 0,5° özetle mümkün**, zaman kalırsa. Sayfaya giden JSON küçük kalır (15 960 hücre, ama çoğu boş).
4. **S4 bu hackathonda gerçekçi değil.** "Gelecek çalışma" olarak yazılmalı.
5. Web tarafı: Türkiye `grid.json` 2 028 hücreden doluları kadar (her ay için 4 değer), boyutu birkaç MB'ı geçmemeli; adım 24'te ölçülür.
