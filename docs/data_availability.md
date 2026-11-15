# Veri erişim testi (adım 15)

Tarih: 14 Kasım 2026. Betik: `scripts/check_access.py`. Ham çıktı: `docs/data_availability.csv`.

## MAP_KEY
Çalışıyor. Sınır: 10 dakikada 5000 işlem.

## Kaynaklar ve tarihler (FIRMS data_availability)

| Kaynak | İlk tarih | Son tarih | Bizim için |
|---|---|---|---|
| MODIS_SP | 2000-11-01 | 2026-08-31 | MODIS arşivi (2012-2025 tamamı var) |
| MODIS_NRT | 2026-09-01 | 2026-11-14 | 2026 "bu ay" için MODIS |
| VIIRS_SNPP_SP | 2012-01-20 | 2026-07-31 | VIIRS arşivi, uzun seri (2012-2025) |
| VIIRS_SNPP_NRT | 2026-08-01 | **2026-11-02** | S-NPP son verisi 2 Kasım 2026 |
| VIIRS_NOAA20_SP | 2018-04-01 | 2026-07-31 | yedek / karşılaştırma |
| VIIRS_NOAA20_NRT | 2026-08-01 | 2026-11-14 | 2026 güncel VIIRS adayı |
| VIIRS_NOAA21_SP | 2023-03-01 | 2026-07-31 | kullanılmıyor |
| VIIRS_NOAA21_NRT | 2024-01-17 | 2026-11-14 | kullanılmıyor |
| LANDSAT_NRT, GOES_NRT, BA_MODIS, BA_VIIRS | | | kapsam dışı |

## Sonuçlar
- **Seviye 1 dönemi (2012-2025) doğrulandı.** MODIS ve VIIRS S-NPP arşivi bu yılları tam kapsıyor. VIIRS S-NPP 20 Ocak 2012'de başlıyor; 2012 Ocak ayı eksik.
- **Örtüşme dönemi:** MODIS ve VIIRS S-NPP 2012-2025 boyunca birlikte var, yani uyumlaştırma (adım 30-31) için 14 yıllık ortak dönem mevcut.
- **VIIRS S-NPP 2 Kasım 2026'da veri üretmeyi bıraktı.** NRT verisi bu tarihte bitiyor. 2026 Kasım'ı için S-NPP yok.
- **Veri kaynağı ayrımı:** 2012-2025 arşivden (Archive Download e-postası ya da API, SP kaynakları). 2026 verisi "bu ay" karşılaştırması için API ile alınacak (SP + NRT).
- **Açık karar (FABLE, adım 18/28):** 2 Kasım 2026 sonrası VIIRS için hangi uydu kullanılacak? Aday: VIIRS NOAA-20 (aynı alet türü, 2018'den beri SP arşivi var; S-NPP ile 2018-2026 örtüşmesinden oran çıkarılabilir). Seçilmezse 2026 karşılaştırması yalnızca MODIS ile ya da 2 Kasım'a kadar S-NPP ile yapılır.
