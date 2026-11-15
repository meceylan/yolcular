# Temizle ve birleştir (adım 22)

Betik: `scripts/clean.py --region turkiye`. Çıktı: `data/processed/turkiye/detections.parquet` (git'e girmez, 28 MB), özet: `data/processed/turkiye/clean_summary.json`. Şema: `docs/data_contract.md` A bölümü (eklenen alanlar dahil).

## Satır sayıları
| Aşama | Satır |
|---|---|
| Okunan (arşiv 744 130 + 1108 API dosyası 460 431) | 1 204 561 |
| Atılan kopya (NOAA-20 NRT'de üst üste binen iki parça) | 876 |
| Atılan "SP varken NRT" | 0 |
| Tabloya giren | 1 203 685 |
| Türkiye sınırı içinde (`keep = true`) | 1 053 497 |

| Kaynak | Köken | Satır | Sınır içinde | İlk | Son |
|---|---|---|---|---|---|
| MODIS_SP | arşiv | 138 521 | 138 521 | 2012-01-03 | 2025-12-29 |
| MODIS_SP | API | 132 192 | 111 754 | 2002-07-01 | 2026-08-31 |
| MODIS_NRT | API | 4 107 | 2 677 | 2026-09-01 | 2026-11-13 |
| VIIRS_SNPP_SP | arşiv | 605 609 | 605 609 | 2012-01-20 | 2025-12-31 |
| VIIRS_SNPP_SP | API | 21 449 | 12 859 | 2026-01-01 | 2026-07-31 |
| VIIRS_SNPP_NRT | API | 30 861 | 18 260 | 2026-08-01 | 2026-10-31 |
| VIIRS_NOAA20_SP | API | 237 447 | 143 581 | 2023-01-01 | 2026-07-31 |
| VIIRS_NOAA20_NRT | API | 33 499 | 20 236 | 2026-08-01 | 2026-11-14 |

Uydu geçişi (`in_series`): S-NPP 636 591 satır seride, 137 satır (Ocak 2012) dışarıda. NOAA-20 721 satır seride (1–14 Kasım 2026), 163 096 satır yalnızca `k_N20` için.

## Sınır maskesi
- Arşiv FIRMS'in kendi ülke sınırıyla kesilmiş; API verisi kutu olarak geldiği için Natural Earth 1:10m Türkiye sınırıyla kesildi.
- Uyum kontrolü: arşiv noktalarının %97,99'u (MODIS %99,86, VIIRS %97,57) Natural Earth sınırının içinde. Dışarıda kalan 14 938 noktanın %92'si sabit kaynak ya da deniz (`type` 2/3): İskenderun, İzmit Körfezi, Samsun, Aliağa kıyı sanayisi ve Karadeniz platformu. Yangın (`type` 0) farkı yalnızca 1 266 nokta (%0,2). Sabit kaynaklar adım 28'de ayıklanacağı için iki sınır arasındaki fark seriye etkisizdir.

## MODIS sürüm etiketi
- Arşivde 2012–2022 `6.03`, 2023–2025 `61.03`. API'den gelen 2002–2011 `6.03`, 2026 SP `61.03`, NRT `6.1NRT`.
- `modis_v61_label` sütunu bunu işaretler (36 301 satır, sınır içinde). Adım 30/32'de 2022→2023 geçişinde kırılma olup olmadığına bakılmalı.

## Filtre işaretleri (sınır içindeki satırlarda; hiçbiri silinmedi)
| İşaret | Satır |
|---|---|
| `flag_static` (type 1/2) | 219 889 |
| `flag_offshore` (type 3) | 5 650 |
| `flag_low_conf` | 79 742 |
| `flag_no_type` (NRT) | 41 173 |
| `flag_bad_value` | 154 |

## Adım 23 için gözlem
MODIS 2009–2011 yıllık sayıları (~13 000–19 000) 2012 sonrasından (~7 000–12 000) belirgin yüksek. Fazlalık Ağustos–Ekim aylarında ve Güneydoğu (37–38 K, 39–41 D) ile İç Anadolu'da (39 K, 34–35 D): büyük olasılıkla anız yakma. Veri hatası mı gerçek mi, adım 23'te bakılmalı.
