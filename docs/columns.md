# MODIS ve VIIRS sütun karşılaştırması (adım 16)

Tarih: 14 Kasım 2026. Betik: `scripts/sample_compare.py`. Sayısal özet: `docs/sample_summary.json`.
Ham örnekler: `data/raw/sample/` (git'e girmez). Alan tanımları FIRMS öznitelik tablolarından (bkz. `docs/references.md`).

## Örnekler
Kutu: Türkiye (35.8–42.2 K, 25.6–44.9 D). İki ayrı hafta alındı, çünkü `type` alanı yalnızca arşiv (SP) verisinde var.

| Kaynak | Hafta | Satır | Gündüz / Gece |
|---|---|---|---|
| MODIS_SP | 1–7 Ağu 2025 | 189 | 160 / 29 |
| VIIRS_SNPP_SP | 1–7 Ağu 2025 | 1079 | 394 / 685 |
| VIIRS_NOAA20_SP | 1–7 Ağu 2025 | 921 | 315 / 606 |
| MODIS_NRT | 20–26 Eki 2026 | 390 | 378 / 12 |
| VIIRS_SNPP_NRT | 20–26 Eki 2026 | 2406 | 1736 / 670 |
| VIIRS_NOAA20_NRT | 20–26 Eki 2026 | 2615 | 1864 / 751 |

Aynı hafta ve kutuda VIIRS, MODIS'in yaklaşık 5–7 katı tespit veriyor (uyumlaştırmanın nedeni).

## Sütunlar

| Sütun | MODIS | VIIRS (S-NPP, NOAA-20) | Fark |
|---|---|---|---|
| latitude, longitude | 4–5 ondalık, ~1 km piksel merkezi | 5 ondalık, ~375 m piksel merkezi | Çözünürlük farklı |
| brightness / bright_ti4 | `brightness`: 4 µm kanal (21/22), K | `bright_ti4`: I-4 kanalı, K; 367 K'de doygun | **Ad farklı**, alet farklı; karşılaştırılamaz |
| bright_t31 / bright_ti5 | `bright_t31`: 11 µm kanal, K | `bright_ti5`: I-5 kanalı, K | **Ad farklı** |
| scan, track | 1.0–4.8 km, 1.0–2.0 km | 0.32–0.80 km, 0.36–0.78 km | Piksel boyutu; MODIS tarama kenarında 4 kata kadar büyüyor |
| acq_date | YYYY-MM-DD, **UTC** | aynı | Yok |
| acq_time | HHMM, **UTC**, başta sıfır düşebilir (ör. `3` = 00:03) | aynı | Metin olarak okunmalı, 4 haneye tamamlanmalı |
| satellite | `Terra`, `Aqua` | `N` (S-NPP), `N20` (NOAA-20), `N21` | Kodlar farklı |
| instrument | `MODIS` | `VIIRS` | |
| confidence | **Tam sayı 0–100** | **Harf: `l`, `n`, `h`** (düşük, normal, yüksek) | Tür farklı, doğrudan eşlenemez (adım 28) |
| version | SP: `61.03`; NRT: `6.1NRT` | SP: `2`; NRT: `2.0NRT` | NRT ayrımı buradan okunur |
| frp | MW, ~1 km piksel başına | MW, ~375 m piksel başına | Tek tespit FRP'si karşılaştırılamaz; hücre toplamı karşılaştırılabilir |
| daynight | `D` / `N` | `D` / `N` | Yok |
| type | **Yalnızca SP'de** | **Yalnızca SP'de** | NRT'de sütun hiç yok |

İki ailenin ortak olmayan tek sütunları parlaklık sıcaklıklarıdır; geri kalan 13 sütun adı aynıdır.

## Güven alanı
- MODIS (örnek): medyan 61–67; %5–6'sı 30'un altında, %12–24'ü 80 ve üstü, çoğunluk 30–79.
- VIIRS (örnek): `n` %87–95, `l` %4–12, `h` %1,5–4.
- FIRMS tanımına göre MODIS'te 0–29 düşük, 30–79 nominal, 80–100 yüksek sayılır; bu, VIIRS `l`/`n`/`h` ile doğal eşlemedir. Örnekteki dağılımlar bu eşlemeyle uyumlu (iki tarafta da çoğunluk "nominal"). Kesin filtre kararı adım 28'de.
- VIIRS'te `l` çoğunlukla gündüz güneş parlaması ya da zayıf sıcaklık farkı demektir; MODIS'te düşük güven oranı benzer büyüklükte.

## Tespit türü (`type`), sabit kaynak ve deniz
Alan var, ama **yalnızca arşiv (SP) verisinde**:

| Değer | Anlam | MODIS_SP | S-NPP_SP | NOAA-20_SP |
|---|---|---|---|---|
| 0 | Olası bitki örtüsü yangını | 161 | 577 | 460 |
| 1 | Etkin yanardağ | 0 | 0 | 0 |
| 2 | Diğer sabit kara kaynağı (sanayi, meşale vb.) | 28 (%15) | 502 (%47) | 460 (%50) |
| 3 | Deniz (açık deniz platformu vb.) | 0 | 0 | 1 |

Doğrulananlar:
- **Sabit kaynak alanı var (`type = 2`) ve etkisi çok büyük.** VIIRS tespitlerinin yaklaşık yarısı sabit kaynak; bunların %90'ı gece. Filtrelenmezse takvim yangını değil sanayiyi gösterir. MODIS'te pay çok daha küçük (%15), yani filtre uygulanmazsa MODIS/VIIRS oranı da bozulur.
- Sabit kaynakların ~%40'ı kutunun güneydoğu köşesinde (enlem < 37.3, boylam > 38: Suriye ve Irak petrol sahaları); kalanı kutunun her yerine dağılmış (sanayi tesisleri). Haftada yalnızca ~135–145 ayrı noktadan (0,01°) geliyor, yani aynı yerler tekrar tekrar görünüyor.
- **Deniz alanı var (`type = 3`)**, ama yalnızca açık deniz sabit kaynaklarını işaretler (örnekte 1 tespit: Batı Karadeniz, 41.26 K 31.41 D). Denize düşen sıradan yanlış tespitler için ayrı alan yok.
- **NRT verisinde `type` sütunu yok.** 2026'nın son aylarında (MODIS Eylül'den, VIIRS Ağustos'tan itibaren) sabit kaynak FIRMS alanıyla ayıklanamaz.

Adım 28 için sonuç: arşivde `type` ile ayıkla; NRT için arşivdeki `type = 2/3` konumlarından bir sabit kaynak maskesi üret ve o konumlara düşen NRT tespitlerini at. Kara/deniz için gerekirse ayrıca kara maskesi.

## Gündüz/gece ve geçiş saatleri
Saatler UTC; Türkiye yerel saati UTC+3.

| Uydu | Gündüz geçişi (UTC) | Gece geçişi (UTC) | Yerel karşılığı |
|---|---|---|---|
| Terra (MODIS) | 2025: 07–08; 2026: 06–07 | 2025: 18–19; 2026: 16–17 | sabah ~10 ve akşam ~21 |
| Aqua (MODIS) | 2025: 11–12; 2026: 12–13 | 00 (2026: 02) | öğleden sonra ~14–16 ve gece ~03–05 |
| S-NPP (VIIRS) | 09–12 | 22–01 | ~13:30 ve ~01:30 |
| NOAA-20 (VIIRS) | 09–12 | 21–01 | S-NPP ile aynı yörünge, ~50 dk arayla |

- VIIRS günde 2 bakış (tek uydu), MODIS günde 4 bakış (iki uydu). MODIS'in sabah/akşam bakışları (Terra) VIIRS'te yok.
- **MODIS yörüngeleri kayıyor:** Terra 2025'ten 2026'ya ~1 saat erkene, Aqua ~1 saat geçe kaymış. Yangınlar öğleden sonra arttığı için bu kayma MODIS sayılarını yıllar içinde etkiler; son yılların MODIS/VIIRS oranı eski yıllarla aynı olmayabilir (adım 30–31'de yıla göre bakılmalı).
- **Gece tespitleri UTC gün sınırına oturuyor:** aynı yerel gecenin VIIRS geçişleri 21–23 UTC (bir önceki UTC günü) ile 00–01 UTC (sonraki gün) arasına bölünüyor. Günlük sayımda aynı gece iki güne dağılır; aylık takvimde etkisi yok denecek kadar az.
- `daynight` iki ailede de aynı kodlu. Gece payı VIIRS'te yazın %65 (sabit kaynaklar yüzünden), MODIS'te %15.

## Diğer gözlemler
- NRT VIIRS'te bozuk değer olabiliyor: örnekte `frp = 0` ve `bright_ti5 = 0` görüldü. FRP toplamlarında bunlar zararsız, ama temizlikte not edilmeli.
- S-NPP ve NOAA-20 aynı haftada birbirine çok yakın sayı veriyor (2025: 1079 / 921; 2026: 2406 / 2615; fark ±%15, yönü değişken). NOAA-20, S-NPP'nin yerine geçmeye uygun aday; oran örtüşme döneminden (2018–2026) hesaplanmalı.
- Ekim 2026 haftasında gündüz tespiti çok yüksek (anız yakma dönemi); haftalar arası karşılaştırma yapılmamalı.
