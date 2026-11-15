// AI-assisted: generated with Claude (Anthropic)
// Interface language (EN default, TR optional). All interface text lives here. Static page text is marked in
// index.html with data-i18n (text), data-i18n-html (markup) and data-i18n-attr ("attr:key;attr:key"); its English
// version is read from the page itself, so only the Turkish version is written for those keys.
// Data values, CSV contents and the official FIRMS acknowledgment are never translated.
"use strict";

let LANG = "en";
let LOCALE = "en-US";
const LANGS = ["en", "tr"];

const I18N = {
  en: {
    "doc.title": "Burn Calendar – monthly satellite fire detections since 2002",
    "lang.label": "Language",
    "no data": "no data",
    "loading": "Loading {what}…",
    "loading.data": "data",
    "err.file": "The data could not be loaded because the page was opened as a file. Start a local web server (python -m http.server 8000 --directory web) and open http://localhost:8000.",
    "err.load": "The data for {what} could not be loaded ({msg}). Check your internet connection and reload the page.",
    "err.thispage": "this page",
    "map.failed": "Map could not be loaded; use the coordinate boxes.",
    "experimental.suffix": " (experimental)",
    "qnote.default": "values before 2012 are rough, and recent values may include some unflagged industrial sources.",
    "series.h": "Consistent series", "series.m": "MODIS only (raw)", "series.v": "VIIRS only (raw)",
    "series.opt.h": "Consistent series (recommended)", "series.opt.hraw": "Combined (raw, sensor switch 2012)",
    "series.opt.m": "MODIS (raw, not harmonized)", "series.opt.v": "VIIRS (raw, not harmonized)",
    "help.h": "One comparable count for every year. Click a month to compare it with other years.",
    "help.m": "MODIS only, as detected. Click a month to compare it with other years.",
    "help.v": "VIIRS only, as detected (from 2012). Click a month to compare it with other years.",
    "notice.raw": "Raw counts from one sensor: compare years only within this series.",
    "notice.rawextra": " Industrial heat sources and low-confidence detections are still included.",
    "bbox.empty": "No grid cell centre is inside this rectangle. Make it larger (at least 0.25° on each side).",
    "bbox.whole": "Whole region: {name}.",
    "bbox.sel": "Selected {n} grid cells: {s}–{n2}° N, {w}–{e}° E.",
    "draw.btn": "Draw on map", "draw.cancel": "Cancel drawing",
    "draw.kbd": "Drawing needs a mouse or touch. Type the four coordinates and press Apply.",
    "draw.hint": "Press and drag on the map to draw a rectangle.",
    "bbox.enterall": "Enter all four coordinates.",
    "period.adjusted": "Data cover {a} to {b}; the period was adjusted.",
    "period.swap": "The start cannot be after the end; the other end was moved to match.",
    "cal.aria": "Burn calendar, {series} detections per month, {y0} to {y1}. Highest month: {max}. Arrow keys move between months, Enter selects a month to compare. \"Show as table\" gives exact values.",
    "tip.partial": "(partial: days 1–{d})",
    "tip.src.V": "Measured: VIIRS S-NPP", "tip.src.M": "Estimate: MODIS × monthly factor", "tip.src.N": "Estimate: VIIRS NOAA-20 × {k}",
    "tip.source": "Source: {how}",
    "tip.range": "Likely range: {lo} – {hi}",
    "tip.oor": "Fire activity above the tested level: probably overestimated, wide range.",
    "tip.small": "Small areas: estimates before 2012 are rough.",
    "tip.viirsnone": "none (before Feb 2012)",
    "tip.viirs": "VIIRS satellite this month: {s}",
    "tip.gap": (o) => `${o.g} day${o.g > 1 ? "s" : ""} without satellite data${o.low ? "; value likely too low" : ""}.`,
    "legend.aria": "Colour legend. Colour scale from {min} (darkest) to {max} (brightest) detections per month, log scale. A ring marks 0 detections, hatching marks no data.",
    "legend.title": "Fire detections per month", "legend.log": "log scale",
    "legend.zero": "0 detections", "legend.nodata": "No data",
    "legend.partial": "Partial month (days 1–{d})",
    "legend.est": "Estimate", "legend.estwhen": "before Feb 2012, from Nov 2026",
    "legend.gap": "{n}+ days missing (likely too low)",
    "table.year": "Year", "table.total": "Total",
    "table.caption": "{series} detections per month. – = no data, e = estimate, ! = {n}+ days without satellite data, * = partial month.",
    "table.show": "Show as table", "table.hide": "Hide table",
    "opt.partial": " (partial month)",
    "details": "Details",
    "card.thisperiod": "This period", "card.thismonth": "This month",
    "card.median": "median",
    "card.years": (o) => `${o.n} years${o.span ? `, ${o.span}` : ""}`,
    "card.estN20": "Estimate from NOAA-20 (likely {lo}–{hi}).",
    "card.estmonth": "This month is an estimate (likely {lo}–{hi}).",
    "card.medmodis": "The median includes years estimated from MODIS (before 2012).",
    "card.gap": "{g} days without satellite data: value likely too low.",
    "card.medperiod": "The median uses only years inside the selected period.",
    "card.typical": (o) => `a typical ${o.month}${o.days ? ` 1–${o.days}` : ""}`,
    "card.above": "above", "card.below": "below",
    "card.cmp": "{dir} {what}",
    "card.few": "Too few detections for a percentage.",
    "card.noother": "No other years to compare with.",
    "pct": "{sign}{n}%",
    "card.sofar": "So far (days 1–{d})", "tag.partial": "partial",
    "ctx.sel": "Selected area",
    "ctx.through": " · data through {d} (UTC)",
    "ctx.range": "{a} to {b}",
    "card.partialtitle": "{m} so far (days 1–{d})",
    "card.curmonth": "Current month so far", "card.outside": "Outside the selected period.",
    "card.peak": "Peak month", "card.nodata": "No data in the selected period.",
    "card.peakest": "Estimated from {src}, likely {lo}–{hi}.",
    "card.peakoor": "Fire activity was above the level the method was tested on.",
    "card.measured": "Measured peak",
    "card.measuredaria": "Measured peak: {m}, {v} detections. Show in the calendar",
    "card.estover": " · estimate, probably overestimated", "card.estimate": " · estimate", "card.detections": " detections",
    "card.showcal": "Show in calendar", "card.showcalaria": "Show {m} in the calendar",
    "card.estmonths": "Estimated months",
    "card.em": "{n} before February 2012 (estimated from MODIS).",
    "card.en": "{n} from November 2026 (estimated from NOAA-20).",
    "card.oor": "{n} of them had fire activity above the tested level: probably overestimated.",
    "card.ofmonths": "of {n} months, dashed in the calendar",
    "card.rawonly": "Raw series: measurements only",
    "card.nmonths": "{n} months in the period.",
    "card.notcomparable": "MODIS and VIIRS raw counts are not comparable with each other.",
    "line.modis": "MODIS (raw)", "line.viirs": "VIIRS (raw)", "line.h": "Consistent series", "line.hraw": "Combined (raw)",
    "line.aria": "Line chart of monthly fire detections, {a} to {b}: {names}. Highest {h} month: {m}, {v}. \"Show as table\" and \"Download CSV\" give the exact values.",
    "line.sub": "{where}, fire detections per month. ",
    "line.subh": "Compare years with the solid magenta line; the other lines show what each sensor saw.",
    "line.subraw": "Raw counts, not comparable between sensors.",
    "line.rec": " (recommended)", "line.band": "Likely range of estimates", "line.sel": "Month selected in the calendar",
    "bar.none": "No data for this series in the selected period.",
    "bar.estn": (o) => `${o.n} estimated month${o.n > 1 ? "s" : ""}`,
    "bar.only": (o) => `only ${o.n} month${o.n > 1 ? "s" : ""} in the period`,
    "bar.partial": "includes the current, unfinished month",
    "bar.missing": (o) => `${o.n} month${o.n > 1 ? "s" : ""} without data`,
    "bar.aria": (o) => `Bar chart of yearly totals, ${o.series}, ${o.y0} to ${o.y1}. Highest ${o.complete ? "complete " : ""}year: ${o.top}, ${o.v} detections.`,
    "bar.sub": "{series}, sum of the months in the selected period.",
    "bar.meas": "Measured year", "bar.total": "Year total", "bar.est": "Includes estimates", "bar.inc": "Incomplete year (not comparable)",
    "csv.done": "Downloaded {name} ({n} months).",
    // map layer
    "dir.N": "N", "dir.S": "S", "dir.E": "E", "dir.W": "W",
    "map.cellrange": "{a} to {b}, {c} to {d}",
    "map.periodtotal": "{a} – {b} total",
    "map.estM": "Estimated: MODIS × monthly factor (before February 2012).",
    "map.estN": "Estimated: VIIRS NOAA-20 × {k}.",
    "map.partial": "Partial month: days 1–{d}.",
    "map.nodata": "No data for this series in this month.",
    "map.gap": "{g} days without satellite data: values likely too low.",
    "map.includes": (o) => `Includes ${o.n} estimated month${o.n > 1 ? "s" : ""}.`,
    "map.tipcount": (o) => `<b>${o.v}</b> fire detection${o.one ? "" : "s"}${o.est ? ' <span class="t-muted">(estimated)</span>' : ""}`,
    "map.cell": "Cell {p}",
    "map.centre": "Map centre: {t}", "map.outside": "Map centre is outside the region.",
    "map.estbadge": "estimated",
    "map.selarea": "the selected area",
    "map.toptitle": "Most active cells in {where}",
    "map.toparia": "Rank {r}: {p}, {v} detections. Show on map",
    "map.nodet": "No detections in {where}.",
    "map.desc": "Map layer: fire detections per {cell}° cell{label}, {when}. ",
    "map.descn": "{n} cells in {where} have detections, {total} in total; the most active cell is at {p} with {v}. ",
    "map.legmonth": "Detections per cell per month", "map.legperiod": "Detections per cell, period total", "map.leglog": "(log scale)",
    "map.legzero": "No colour = 0 detections", "map.legest": ". Values are estimates",
    "map.legaria": "Map legend: colour from {min} (darkest) to {max} (brightest) detections per cell, log scale. No colour means 0.",
    "play": "Play", "pause": "Pause", "play.aria": "Play the months of the selected period", "pause.aria": "Pause playback",
    // findings
    "f.title": "Key findings", "f.exp": "experimental",
    "f.det": (o) => `${o.v} fire detection${o.one ? "" : "s"}${o.est ? " (estimated)" : ""}`,
    "f.days": "{m}, days 1–{d}",
    "f.nodata": "{span}: no data for this series in {where}.",
    "f.few": "{span}: {val} in {where}; too few detections in a typical {cal} for a percentage.",
    "f.noother": "{span}: {val} in {where}; no other years in the period to compare with.",
    "f.cmp": (o) => `${o.span}: ${o.val} in ${o.where}, ${o.n}% ${o.up ? "above" : "below"} the median ${o.cal}${o.days ? ` (days 1–${o.days})` : ""} of ${o.years} other years (${o.med}).`,
    "f.unranked": "The month is not finished yet (data through day {d}), so it is not ranked.",
    "f.rank": (o) => `It ranks ${o.rank} of ${o.n} complete months (${o.a} – ${o.b})${o.est ? "; its value is an estimate" : ""}.`,
    "f.peakm": "Highest measured month in {where} (VIIRS, from February 2012): {m}, {v} detections.",
    "f.peak": "Highest month in {where}: {m}, {v} detections.",
    "f.nomeas": "No measured months in the selected period.",
    "f.nomeash": "No measured months in the selected period: all values before February 2012 are estimates.",
    "f.expnote": "Experimental region. {note}",
    "f.selarea": "the selected area",
    // climate
    "c.title": "Climate context", "c.when": "{m}, fire-weighted region average",
    "c.temp": "Temperature", "c.prec": "Precipitation",
    "c.vs": "vs. average ({v}; average {a})",
    "c.none": "No climate data for {m} yet (available to {last}).",
    "c.local": " Not specific to the drawn area.",
    "c.note": "Difference from the {b0}–{b1} {cal} average, region-wide: weighted average of {n} points in the areas of {name} with the most fires in 2012–2025.{local} Shown alongside the fire counts, not a causal claim. Source: NASA POWER.",
    // share
    "share.copy": "Copy link", "share.copied": "Copied", "share.ok": "Link copied to the clipboard.", "share.fail": "Copy failed. Link: {url}",
  },

  tr: {
    "doc.title": "Yanma Takvimi – 2002'den bu yana aylık uydu yangın tespitleri",
    "lang.label": "Dil",
    "no data": "veri yok",
    "loading": "{what} yükleniyor…",
    "loading.data": "Veri",
    "err.file": "Sayfa dosya olarak açıldığı için veri yüklenemedi. Yerel bir web sunucusu başlatın (python -m http.server 8000 --directory web) ve http://localhost:8000 adresini açın.",
    "err.load": "{what} verisi yüklenemedi ({msg}). İnternet bağlantınızı kontrol edip sayfayı yenileyin.",
    "err.thispage": "Bu sayfanın",
    "map.failed": "Harita yüklenemedi; koordinat kutularını kullanın.",
    "experimental.suffix": " (deneysel)",
    "qnote.default": "2012 öncesi değerler kaba tahmindir; son yıllardaki değerler işaretlenmemiş bazı endüstriyel kaynakları içerebilir.",
    "qnote.se_australia": "2012 öncesi değerler kaba tahmindir: yangının az olduğu yıllarda tahmin yaklaşık üçte bir fazla çıkabilir.",
    "region.turkiye": "Türkiye", "region.balkanlar": "Balkanlar", "region.kafkasya": "Kafkasya", "region.dogu_akdeniz": "Doğu Akdeniz",
    "region.se_australia": "Güneydoğu Avustralya", "region.california": "Kaliforniya", "region.amazon_arc": "Amazon yayı",
    "series.h": "Tutarlı seri", "series.m": "Yalnız MODIS (ham)", "series.v": "Yalnız VIIRS (ham)",
    "series.opt.h": "Tutarlı seri (önerilen)", "series.opt.hraw": "Birleşik (ham, 2012'de sensör değişir)",
    "series.opt.m": "MODIS (ham, uyumlaştırılmamış)", "series.opt.v": "VIIRS (ham, uyumlaştırılmamış)",
    "help.h": "Her yıl için karşılaştırılabilir tek bir sayı. Bir aya tıklayarak onu diğer yıllarla karşılaştırın.",
    "help.m": "Yalnız MODIS, tespit edildiği gibi. Bir aya tıklayarak onu diğer yıllarla karşılaştırın.",
    "help.v": "Yalnız VIIRS, tespit edildiği gibi (2012'den itibaren). Bir aya tıklayarak onu diğer yıllarla karşılaştırın.",
    "notice.raw": "Tek sensörün ham sayıları: yılları yalnızca bu seri içinde karşılaştırın.",
    "notice.rawextra": " Endüstriyel ısı kaynakları ve düşük güvenli tespitler hâlâ dahildir.",
    "bbox.empty": "Bu dikdörtgenin içinde hiçbir ızgara hücresinin merkezi yok. Dikdörtgeni büyütün (her kenarı en az 0,25°).",
    "bbox.whole": "Bölgenin tamamı: {name}.",
    "bbox.sel": "{n} ızgara hücresi seçildi: {s}–{n2}° K, {w}–{e}° D.",
    "draw.btn": "Haritada çiz", "draw.cancel": "Çizimi iptal et",
    "draw.kbd": "Çizim için fare ya da dokunma gerekir. Dört koordinatı yazıp Uygula'ya basın.",
    "draw.hint": "Dikdörtgen çizmek için haritaya basılı tutup sürükleyin.",
    "bbox.enterall": "Dört koordinatın hepsini girin.",
    "period.adjusted": "Veri {a} ile {b} arasını kapsıyor; dönem buna göre ayarlandı.",
    "period.swap": "Başlangıç bitişten sonra olamaz; diğer uç buna göre kaydırıldı.",
    "cal.aria": "Yanma takvimi, aylık {series} tespitleri, {y0}–{y1}. En yüksek ay: {max}. Ok tuşları aylar arasında gezer, Enter karşılaştırılacak ayı seçer. \"Tablo olarak göster\" kesin değerleri verir.",
    "tip.partial": "(eksik ay: 1–{d}. günler)",
    "tip.src.V": "Ölçüm: VIIRS S-NPP", "tip.src.M": "Tahmin: MODIS × aylık katsayı", "tip.src.N": "Tahmin: VIIRS NOAA-20 × {k}",
    "tip.source": "Kaynak: {how}",
    "tip.range": "Olası aralık: {lo} – {hi}",
    "tip.oor": "Yangın etkinliği sınanan düzeyin üstünde: büyük olasılıkla fazla tahmin, aralık geniş.",
    "tip.small": "Küçük alanlar: 2012 öncesi tahminler kabadır.",
    "tip.viirsnone": "yok (Şubat 2012 öncesi)",
    "tip.viirs": "Bu ay VIIRS uydusu: {s}",
    "tip.gap": (o) => `${o.g} gün uydu verisi yok${o.low ? "; değer büyük olasılıkla düşük" : ""}.`,
    "legend.aria": "Renk açıklaması. Renk skalası aylık {min} (en koyu) ile {max} (en parlak) tespit arasında, logaritmik ölçek. Halka 0 tespiti, tarama veri olmadığını gösterir.",
    "legend.title": "Aylık yangın tespiti", "legend.log": "logaritmik ölçek",
    "legend.zero": "0 tespit", "legend.nodata": "Veri yok",
    "legend.partial": "Eksik ay (1–{d}. günler)",
    "legend.est": "Tahmin", "legend.estwhen": "Şubat 2012 öncesi, Kasım 2026 sonrası",
    "legend.gap": "{n}+ gün eksik (değer büyük olasılıkla düşük)",
    "table.year": "Yıl", "table.total": "Toplam",
    "table.caption": "Aylık {series} tespitleri. – = veri yok, e = tahmin, ! = {n}+ gün uydu verisi yok, * = eksik ay.",
    "table.show": "Tablo olarak göster", "table.hide": "Tabloyu gizle",
    "opt.partial": " (eksik ay)",
    "details": "Ayrıntılar",
    "card.thisperiod": "Bu dönem", "card.thismonth": "Bu ay",
    "card.median": "medyan",
    "card.years": (o) => `${o.n} yıl${o.span ? `, ${o.span}` : ""}`,
    "card.estN20": "NOAA-20'den tahmin (olası aralık {lo}–{hi}).",
    "card.estmonth": "Bu ayın değeri tahmindir (olası aralık {lo}–{hi}).",
    "card.medmodis": "Medyan, MODIS'ten tahmin edilen yılları da içerir (2012 öncesi).",
    "card.gap": "{g} gün uydu verisi yok: değer büyük olasılıkla düşük.",
    "card.medperiod": "Medyan yalnızca seçili dönemdeki yılları kullanır.",
    "card.typical": (o) => `tipik bir ${o.month}${o.days ? ` (1–${o.days})` : ""} ayına göre`,
    "card.above": "fazla", "card.below": "az",
    "card.cmp": "{what} {dir}",
    "card.few": "Yüzde vermek için tespit sayısı çok az.",
    "card.noother": "Karşılaştırılacak başka yıl yok.",
    "pct": "{sign}%{n}",
    "card.sofar": "Şu ana kadar (1–{d}. günler)", "tag.partial": "eksik",
    "ctx.sel": "Seçili alan",
    "ctx.through": " · veri {d} tarihine kadar (UTC)",
    "ctx.range": "{a} – {b}",
    "card.partialtitle": "{m}, şu ana kadar (1–{d}. günler)",
    "card.curmonth": "İçinde bulunulan ay", "card.outside": "Seçili dönemin dışında.",
    "card.peak": "En yoğun ay", "card.nodata": "Seçili dönemde veri yok.",
    "card.peakest": "{src} verisinden tahmin, olası aralık {lo}–{hi}.",
    "card.peakoor": "Yangın etkinliği, yöntemin sınandığı düzeyin üstündeydi.",
    "card.measured": "Ölçülmüş en yoğun ay",
    "card.measuredaria": "Ölçülmüş en yoğun ay: {m}, {v} tespit. Takvimde göster",
    "card.estover": " · tahmin, büyük olasılıkla fazla", "card.estimate": " · tahmin", "card.detections": " tespit",
    "card.showcal": "Takvimde göster", "card.showcalaria": "{m} ayını takvimde göster",
    "card.estmonths": "Tahmin edilen aylar",
    "card.em": "{n} ay Şubat 2012 öncesi (MODIS'ten tahmin).",
    "card.en": "{n} ay Kasım 2026'dan itibaren (NOAA-20'den tahmin).",
    "card.oor": "Bunların {n} tanesinde yangın etkinliği sınanan düzeyin üstünde: büyük olasılıkla fazla tahmin.",
    "card.ofmonths": "{n} ay içinde, takvimde kesikli çizgili",
    "card.rawonly": "Ham seri: yalnızca ölçümler",
    "card.nmonths": "Dönemde {n} ay var.",
    "card.notcomparable": "MODIS ve VIIRS ham sayıları birbiriyle karşılaştırılamaz.",
    "line.modis": "MODIS (ham)", "line.viirs": "VIIRS (ham)", "line.h": "Tutarlı seri", "line.hraw": "Birleşik (ham)",
    "line.aria": "Aylık yangın tespitlerinin çizgi grafiği, {a} – {b}: {names}. En yüksek {h} ayı: {m}, {v}. Kesin değerler için \"Tablo olarak göster\" ve \"CSV indir\".",
    "line.sub": "{where}, aylık yangın tespiti. ",
    "line.subh": "Yılları düz magenta çizgiyle karşılaştırın; diğer çizgiler her sensörün gördüğünü gösterir.",
    "line.subraw": "Ham sayılar, sensörler arasında karşılaştırılamaz.",
    "line.rec": " (önerilen)", "line.band": "Tahminlerin olası aralığı", "line.sel": "Takvimde seçilen ay",
    "bar.none": "Seçili dönemde bu seri için veri yok.",
    "bar.estn": (o) => `${o.n} tahmin edilen ay`,
    "bar.only": (o) => `dönemde yalnızca ${o.n} ay`,
    "bar.partial": "içinde bulunulan, bitmemiş ayı içerir",
    "bar.missing": (o) => `${o.n} ay verisiz`,
    "bar.aria": (o) => `Yıllık toplamların sütun grafiği, ${o.series}, ${o.y0}–${o.y1}. En yüksek ${o.complete ? "tam " : ""}yıl: ${o.top}, ${o.v} tespit.`,
    "bar.sub": "{series}, seçili dönemdeki ayların toplamı.",
    "bar.meas": "Ölçülmüş yıl", "bar.total": "Yıl toplamı", "bar.est": "Tahmin içerir", "bar.inc": "Eksik yıl (karşılaştırılamaz)",
    "csv.done": "{name} indirildi ({n} ay).",
    "dir.N": "K", "dir.S": "G", "dir.E": "D", "dir.W": "B",
    "map.cellrange": "{a} – {b}, {c} – {d}",
    "map.periodtotal": "{a} – {b} toplamı",
    "map.estM": "Tahmin: MODIS × aylık katsayı (Şubat 2012 öncesi).",
    "map.estN": "Tahmin: VIIRS NOAA-20 × {k}.",
    "map.partial": "Eksik ay: 1–{d}. günler.",
    "map.nodata": "Bu ay bu seri için veri yok.",
    "map.gap": "{g} gün uydu verisi yok: değerler büyük olasılıkla düşük.",
    "map.includes": (o) => `${o.n} tahmin edilen ay içerir.`,
    "map.tipcount": (o) => `<b>${o.v}</b> yangın tespiti${o.est ? ' <span class="t-muted">(tahmin)</span>' : ""}`,
    "map.cell": "Hücre {p}",
    "map.centre": "Harita merkezi: {t}", "map.outside": "Harita merkezi bölgenin dışında.",
    "map.estbadge": "tahmin",
    "map.selarea": "seçili alan",
    "map.toptitle": "En yoğun hücreler ({where})",
    "map.toparia": "{r}. sıra: {p}, {v} tespit. Haritada göster",
    "map.nodet": "Tespit yok ({where}).",
    "map.desc": "Harita katmanı: {cell}° hücre başına yangın tespiti{label}, {when}. ",
    "map.descn": "Tespit olan hücre sayısı: {n} ({where}), toplam {total}; en yoğun hücre {p} konumunda, {v} tespit. ",
    "map.legmonth": "Hücre başına aylık tespit", "map.legperiod": "Hücre başına tespit, dönem toplamı", "map.leglog": "(logaritmik ölçek)",
    "map.legzero": "Renksiz = 0 tespit", "map.legest": ". Değerler tahmindir",
    "map.legaria": "Harita açıklaması: renk hücre başına {min} (en koyu) ile {max} (en parlak) tespit arasında, logaritmik ölçek. Renksiz 0 demektir.",
    "play": "Oynat", "pause": "Duraklat", "play.aria": "Seçili dönemin aylarını oynat", "pause.aria": "Oynatmayı duraklat",
    "f.title": "Öne çıkanlar", "f.exp": "deneysel",
    "f.det": (o) => `${o.v} yangın tespiti${o.est ? " (tahmin)" : ""}`,
    "f.days": "{m}, 1–{d}. günler",
    "f.nodata": "{span}: {where} için bu seride veri yok.",
    "f.few": "{span}: {where} için {val}; tipik bir {cal} ayında yüzde vermek için tespit çok az.",
    "f.noother": "{span}: {where} için {val}; dönemde karşılaştırılacak başka yıl yok.",
    "f.cmp": (o) => `${o.span}: ${o.where} için ${o.val}; diğer ${o.years} yılın ${o.cal}${o.days ? ` (1–${o.days}. günler)` : ""} medyanından (${o.med}) %${o.n} ${o.up ? "fazla" : "az"}.`,
    "f.unranked": "Ay henüz bitmedi (veri {d}. güne kadar), bu yüzden sıralamaya girmiyor.",
    "f.rank": (o) => `${o.n} tam ay arasında ${o.rank} sırada (${o.a} – ${o.b})${o.est ? "; değeri tahmindir" : ""}.`,
    "f.peakm": "Ölçülmüş en yoğun ay ({where}; VIIRS, Şubat 2012'den itibaren): {m}, {v} tespit.",
    "f.peak": "En yoğun ay ({where}): {m}, {v} tespit.",
    "f.nomeas": "Seçili dönemde ölçülmüş ay yok.",
    "f.nomeash": "Seçili dönemde ölçülmüş ay yok: Şubat 2012 öncesindeki tüm değerler tahmindir.",
    "f.expnote": "Deneysel bölge. {note}",
    "f.selarea": "seçili alan",
    "c.title": "İklim bağlamı", "c.when": "{m}, yangın ağırlıklı bölge ortalaması",
    "c.temp": "Sıcaklık", "c.prec": "Yağış",
    "c.vs": "ortalamaya göre ({v}; ortalama {a})",
    "c.none": "{m} için henüz iklim verisi yok ({last} ayına kadar var).",
    "c.local": " Çizilen alana özgü değildir.",
    "c.note": "{b0}–{b1} {cal} ortalamasından fark, bölge geneli: {name} içinde 2012–2025'te en çok yangın görülen yerlerdeki {n} noktanın ağırlıklı ortalaması.{local} Yangın sayılarıyla yan yana gösterilir; aralarında neden-sonuç ilişkisi iddia edilmez. Kaynak: NASA POWER.",
    "share.copy": "Bağlantıyı kopyala", "share.copied": "Kopyalandı", "share.ok": "Bağlantı panoya kopyalandı.", "share.fail": "Kopyalanamadı. Bağlantı: {url}",

    // ---------- static page text (English comes from index.html) ----------
    "s.title": "Yanma Takvimi",
    "s.lede": "Uyduların 2002'den bu yana her ay kaç yangın gördüğü ve bu ayın olağan dışı olup olmadığı.",
    "s.howto": "Nasıl okunur",
    "s.howtotext": "Bir kare = bir ay. Daha parlak = daha çok yangın.<br>Kesikli = tahmin, taralı = veri yok.",
    "s.loading": "Veri yükleniyor…",
    "s.copyhelp": "Bu görünümün bağlantısını kopyalar: bölge, alan, dönem ve seçili ay.",
    "s.summary": "Özet",
    "s.cmpmonth": "Karşılaştırılacak ay",
    "s.area": "Alan seçin", "s.region": "Bölge",
    "s.bboxhelp": "Haritada bir dikdörtgen çizin ya da koordinatları yazın; merkezi içeride kalan 0,25°'lik ızgara hücreleri toplanır.",
    "s.maparia": "Alan seçme haritası. Çizim için fare ya da dokunma gerekir; klavye ve ekran okuyucu kullananlar koordinatları kutulara yazabilir.",
    "s.whole": "Bölgenin tamamı", "s.coords": "Koordinat yaz", "s.coordsaria": "Alan koordinatları (derece)",
    "s.north": "Kuzey", "s.south": "Güney", "s.west": "Batı", "s.east": "Doğu", "s.apply": "Uygula",
    "s.period": "Dönem seçin", "s.periodlegend": "Dönem", "s.from": "Başlangıç", "s.to": "Bitiş",
    "s.frommonth": "Başlangıç ayı", "s.fromyear": "Başlangıç yılı", "s.tomonth": "Bitiş ayı", "s.toyear": "Bitiş yılı",
    "s.fullperiod": "Tüm dönem", "s.csv": "CSV indir",
    "s.heat": "Haritada yangın yoğunluğu", "s.showlayer": "Katmanı göster", "s.show": "Göster",
    "s.selmonth": "Seçili ay", "s.periodtotal": "Dönem toplamı",
    "s.playaria": "Seçili dönemin aylarını oynatma", "s.prev": "Önceki ay", "s.next": "Sonraki ay",
    "s.speed": "Hız", "s.slow": "Yavaş", "s.normal": "Normal", "s.fast": "Hızlı",
    "s.motion": "Azaltılmış hareket açık: oynatma yavaş başlar ve başa dönmez.",
    "s.readout": "Sayısını görmek için bir hücrenin üzerine gelin ya da dokunun. Klavyeyle haritaya odaklanıp ok tuşlarını kullanın: ortadaki artının altındaki hücre okunur.",
    "s.topcells": "En yoğun hücreler",
    "s.line": "Ay ay", "s.bar": "Yıllık toplamlar",
    "s.explore": "İncele", "s.series": "Seri",
    "s.exp": "<strong>Deneysel:</strong> <span id=\"exp-text\"></span>",
    "s.legendaria": "Renk açıklaması",
    "s.hint": "Klavye: Tab ile takvime gelin, ok tuşları aylar arasında gezer, Home ve End yıl içinde atlar, Enter ya da Boşluk karşılaştırılacak ayı seçer.",
    "s.about": "Veri hakkında",
    "s.foot.disc": "Veriler NASA LANCE/FIRMS tarafından \"olduğu gibi\" sağlanır; taktik kararlar ya da yerel ölçekteki koşullar için uygun değildir. <a href=\"https://firms.modaps.eosdis.nasa.gov/download/Readme.txt\" rel=\"noopener\">Tam sorumluluk reddi</a> · <a href=\"https://www.earthdata.nasa.gov/engage/open-data-services-software-policies/data-use-policy\" rel=\"noopener\">Veri kullanım politikası</a>",
    "s.foot.ack": "Üstteki teşekkür metni NASA'nın istediği resmî İngilizce biçimdir: veriler NASA FIRMS'ten alınmıştır.",
    "s.foot.map": "Harita: <a href=\"https://leafletjs.com\" rel=\"noopener\">Leaflet</a>; harita verisi © <a href=\"https://www.openstreetmap.org/copyright\" rel=\"noopener\">OpenStreetMap</a> katkıcıları.",
    "s.foot.about": "Hakkında: NASA Space Apps Challenge 2026 için Yolcular ekibi tarafından yapıldı. Kod ve belgeler yapay zekâ desteğiyle (Claude, Anthropic) üretildi.",
    "s.aboutbody": `
        <h3>Ne sayılıyor ve seri nasıl oluşturuluyor</h3>
        <p>NASA FIRMS'ten MODIS (Temmuz 2002'den beri) ve VIIRS (2012'den beri S-NPP, sonra NOAA-20) aktif yangın tespitleri (tek bir uydu geçişinde görülen sıcak pikseller; tek tek yangınlar değil), 0,25°'lik ızgarada takvim ayı (UTC) başına toplanır. <span id="about-filters"></span></p>
        <p>VIIRS, MODIS'ten birkaç kat daha fazla yangın görür ve bu oran her yerde aynı değildir: Türkiye'de genel olarak 3,25, Doğu Akdeniz kutusunda 7,07'ye kadar. Bu yüzden her bölgenin her takvim ayı için kendi katsayısı vardır: 2012–2022 yıllarında VIIRS toplamının MODIS toplamına bölümü (verisiz günler hariç). Şubat 2012 öncesi değer MODIS × katsayıdır (tahmin); Şubat 2012'den itibaren doğrudan VIIRS S-NPP sayısıdır; Kasım 2026'dan itibaren VIIRS NOAA-20 × 0,986'dır (tüm bölgelerde aynı).</p>
        <h3>Tahminler ne kadar doğru</h3>
        <p>2012–2022'nin her yılı sırayla dışarıda bırakılarak ve ayrıca 2023–2025 üzerinde bağımsız olarak sınandı. Ayların yaklaşık üçte ikisi, ipuçlarında ve grafiklerde gösterilen "olası aralık" içinde kalıyor.</p>
        <div class="table-scroll"><table class="val-table">
          <caption class="sr-only">Bölgelere göre tahmin hatası</caption>
          <thead><tr><th scope="col">Bölge</th><th scope="col">Tipik hata, ay</th><th scope="col">Tipik hata, yıl</th><th scope="col">En kötü yıl</th><th scope="col">Sınama 2023–2025</th><th scope="col">Olası aralık</th></tr></thead>
          <tbody>
            <tr><th scope="row">Türkiye</th><td>%11,8</td><td>%4,6</td><td>%11,3</td><td>+%1,5</td><td>0,85–1,34 ×</td></tr>
            <tr><th scope="row">Balkanlar</th><td>%8,7</td><td>%3,1</td><td>%5,2</td><td>+%3,8</td><td>0,88–1,27 ×</td></tr>
            <tr><th scope="row">Kafkasya</th><td>%12,0</td><td>%5,5</td><td>%16,6 (2015)</td><td>+%0,7</td><td>0,87–1,24 ×</td></tr>
            <tr><th scope="row">Doğu Akdeniz (deneysel)</th><td>%23,7</td><td>%15,4</td><td>%43,6 (2020)</td><td>+%18,7</td><td>0,87–1,69 ×</td></tr>
            <tr><th scope="row">Kaliforniya</th><td>%10,2</td><td>%7,3</td><td>%18,4 (2016)</td><td>%0,0</td><td>0,80–1,22 ×</td></tr>
            <tr><th scope="row">Amazon yayı</th><td>%6,8</td><td>%2,5</td><td>%10,0 (2021)</td><td>−%0,3</td><td>0,69–1,23 ×</td></tr>
            <tr><th scope="row">Güneydoğu Avustralya (deneysel)</th><td>%14,6</td><td>%12,1</td><td>%36,0 (2012)</td><td>+%8,2</td><td>0,76–1,35 ×</td></tr>
          </tbody>
        </table></div>
        <h3>Sınırlar</h3>
        <ul>
          <li>Şubat 2012 öncesindeki tüm değerler tahmindir; küçük çizilmiş alanlarda kabadır. Yoğun aylar fazla, sakin aylar az tahmin edilme eğilimindedir.</li>
          <li>Sınanan her aydan daha yoğun aylar işaretlidir ve büyük olasılıkla fazla tahmindir (Türkiye'de 2009–2011 Ağustos–Ekim aylarında: 2009 ve 2011 toplamlarını üst sınır olarak okuyun).</li>
          <li>Deneysel: Doğu Akdeniz kutusu (MODIS tespiti az; son yıllardaki VIIRS tespitlerinin yaklaşık %15'i büyük olasılıkla işaretlenmemiş endüstriyel kaynak) ve Güneydoğu Avustralya kutusu (2012 öncesinde sakin yıllar yaklaşık üçte bir fazla çıkabilir).</li>
          <li>Amazon yayı kutusu: 2003 ve 2004 beşte bire kadar düşük olabilir (MODIS'teki sabit kaynak işaretleri şüpheli). 2023'ten itibaren ham MODIS sayıları düşüktür (yörünge kayması) ve tahminde kullanılmaz.</li>
          <li>Kutular yalnızca karayı kapsayan dikdörtgenlerdir, ülke toplamı değildir. Balkanlar, Kafkasya ve Doğu Akdeniz kutuları Türkiye ile kesişir; Türkiye toprakları için Türkiye görünümünü kullanın.</li>
          <li>3 ya da daha fazla gün uydu verisi olmayan aylar işaretlidir (küçük üçgen) ve büyük olasılıkla düşüktür; taralı karelerde seçili seri için veri yoktur.</li>
        </ul>
        <h3>İklim bağlamı</h3>
        <p>Aylık 2&nbsp;m hava sıcaklığı ve yağış (NASA POWER), aynı ayın 2002–2025 ortalamasından fark olarak gösterilir: her bölgede, 2012–2025'te tespitlerin en çok görüldüğü yerlere konmuş 5 kara noktasının yangın ağırlıklı ortalaması (Türkiye'de Güneydoğu Anadolu ve Çukurova, Ege değil). Yangın sayılarıyla yan yana gösterilir; birinin diğerini açıkladığı iddia edilmez. NASA POWER atfı (resmî İngilizce): The data was obtained from National Aeronautics and Space Administration (NASA) Langley Research Center's Prediction Of Worldwide Energy Resources (POWER) project funded through the NASA Earth Science Division. The data was obtained from the POWER Project's Monthly 2.10.0 version on 2026/11/15.</p>
        <h3>Kaynaklar ve yapay zekâ kullanımı</h3>
        <p>NASA FIRMS (yangın), <a href="https://power.larc.nasa.gov" rel="noopener">NASA POWER</a> (iklim), <a href="https://www.naturalearthdata.com" rel="noopener">Natural Earth</a> (sınırlar, kara maskesi), inferno renk skalası (matplotlib, CC0), Leaflet ve OpenStreetMap (harita). Ayrıntılar: <a href="https://github.com/meceylan/yolcular/blob/main/docs/method.md" rel="noopener">yöntemin tamamı</a>, <a href="https://github.com/meceylan/yolcular/blob/main/docs/references.md" rel="noopener">tüm kaynaklar</a>. Kod ve belgeler yapay zekâ desteğiyle (Claude, Anthropic) üretildi ve ekip tarafından kontrol edildi.</p>`,
    "meta.filters": "Sabit kaynak ya da açık deniz olarak işaretlenen tespitler ve düşük güvenli tespitler çıkarılır; yakın gerçek zamanlı son veriler için arşivdeki sabit kaynaklardan oluşturulan bir konum maskesi kullanılır.",
  },
};

// Text for a key in the current language (falls back to English, then to the key itself).
function t(key, vars) {
  let s = I18N[LANG][key];
  if (s === undefined) s = I18N.en[key];
  if (s === undefined) return key;
  if (typeof s === "function") return s(vars || {});
  return vars ? s.replace(/\{(\w+)\}/g, (m, k) => (vars[k] !== undefined ? vars[k] : m)) : s;
}

// Number formatting by language; the numbers themselves never change.
const nf = (v, digits = 0) => Number(v).toLocaleString(LOCALE, { minimumFractionDigits: digits, maximumFractionDigits: digits });
const pctText = (sign, n) => t("pct", { sign, n });
// Percent figures: English keeps the plain digits it always showed; Turkish uses its own separators.
const pctNum = (x) => (LANG === "tr" ? nf(Math.abs(x)) : Math.abs(x).toFixed(0));
function ordinalText(n) {
  if (LANG === "tr") return `${n}.`;
  const s = ["th", "st", "nd", "rd"], v = n % 100;
  return n + (s[(v - 20) % 10] || s[v] || s[0]);
}
function setMonthNames() {
  const long = new Intl.DateTimeFormat(LOCALE, { month: "long", timeZone: "UTC" });
  const short = new Intl.DateTimeFormat(LOCALE, { month: "short", timeZone: "UTC" });
  for (let m = 0; m < 12; m++) {
    const d = new Date(Date.UTC(2021, m, 15));
    MONTHS_LONG[m] = long.format(d);
    MONTHS[m] = short.format(d).replace(".", "");
  }
}

// Region display name: Turkish names from the dictionary, English names from data/index.json.
function regionName(id) {
  if (LANG === "tr" && I18N.tr[`region.${id}`]) return I18N.tr[`region.${id}`];
  return (typeof regionNames !== "undefined" && regionNames[id]) || id;
}
function qualityNote(meta) {
  if (LANG === "tr") return I18N.tr[`qnote.${meta.id}`] || I18N.tr["qnote.default"];
  return meta.quality_note || I18N.en["qnote.default"];
}

// Static page text: remember the English version on first use, then show the chosen language.
const STATIC_EN = new Map();
function applyStaticText() {
  document.querySelectorAll("[data-i18n],[data-i18n-html]").forEach((el) => {
    const html = el.hasAttribute("data-i18n-html"), key = el.getAttribute(html ? "data-i18n-html" : "data-i18n");
    if (!STATIC_EN.has(el)) STATIC_EN.set(el, html ? el.innerHTML : el.textContent);
    const tr = LANG === "tr" ? I18N.tr[key] : undefined;
    const val = tr !== undefined ? tr : STATIC_EN.get(el);
    if (html) el.innerHTML = val; else el.textContent = val;
  });
  document.querySelectorAll("[data-i18n-attr]").forEach((el) => {
    for (const pair of el.getAttribute("data-i18n-attr").split(";")) {
      const [attr, key] = pair.split(":");
      if (!STATIC_EN.has(`${key}@`)) STATIC_EN.set(`${key}@`, el.getAttribute(attr) || "");
      el.setAttribute(attr, LANG === "tr" && I18N.tr[key] !== undefined ? I18N.tr[key] : STATIC_EN.get(`${key}@`));
    }
  });
  document.title = t("doc.title");
  document.documentElement.lang = LANG;
  document.querySelectorAll(".lang-switch button").forEach((b) => {
    const on = b.dataset.lang === LANG;
    b.setAttribute("aria-pressed", String(on));
  });
}

function langFromURL() {
  const v = new URLSearchParams(location.search).get("lang");
  return LANGS.includes(v) ? v : "en";
}

// Switch language: static text, select options, then everything drawn from data. Region, month, period and box stay.
function setLang(lang, redraw = true) {
  LANG = LANGS.includes(lang) ? lang : "en";
  LOCALE = LANG === "tr" ? "tr-TR" : "en-US";
  setMonthNames();
  applyStaticText();
  if (!redraw || typeof state === "undefined" || !state.monthly) return;
  relabelControls();
  regionTexts();
  setBbox(state.bbox, state.full);   // same box; refreshes the status line and redraws everything
  if (typeof heatSetPlaying === "function") heatSetPlaying(heat.playing);
}
