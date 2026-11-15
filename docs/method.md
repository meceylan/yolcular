# Method: one fire-detection series from MODIS and VIIRS

AI-assisted: written with Claude (Anthropic), checked by the team. Every number below comes from the project's own analysis notes (`harmonize.md`, `harmonize_s2.md`, `harmonize_s3.md`, `validation.md`, `validation_s2.md`, `validation_s3.md`, `filters.md`).

## 1. Problem

NASA FIRMS gives active fire detections from two sensor families. MODIS (Terra and Aqua) reaches back to July 2002; VIIRS (S-NPP) starts in 2012 and sees several times more hot pixels because its pixels are smaller. The two counts cannot be compared directly. If the series are simply joined, fires seem to multiply in 2012: the usual yearly level after 2012 is 3.4 times the level before it in Türkiye and between 2 and 10 times in the other regions. That step is made by the sensor change, not by fire.

## 2. Method

**Filters (same in every region).** Detections that FIRMS flags as volcano, static land source or offshore (`type` 1, 2, 3) and low-confidence detections (MODIS below 30, VIIRS `l`) are removed. Türkiye is cut at the national border; box regions keep land only. Recent near-real-time data has no `type` field, so a location mask is used instead: 0.01° cells where archived static-source detections occurred on at least 3 days. Day and night are counted together on a 0.25° grid, per calendar month (UTC).

**Factor per region and calendar month.** For each region and each of the 12 calendar months, factor = sum of VIIRS S-NPP detections / sum of MODIS detections over 2012–2022, with satellite outage days left out. Only 2012–2022 is used because the MODIS satellites drift to other overpass times from 2023. In the Eastern Mediterranean box, where MODIS data is thin, months with little data are pulled towards the region's yearly ratio.

**The series.** Before February 2012: MODIS × factor (an estimate, marked as such). From February 2012: the VIIRS S-NPP count itself, unchanged. From November 2026: VIIRS NOAA-20 × 0.986, one common multiplier for all regions, measured on the days in 2023–2025 when both satellites delivered data. MODIS counts start on 4 July 2002, the first day both MODIS satellites were working.

## 3. Validation

Two tests. (1) Each year of 2012–2022 is left out in turn, the factor is computed from the other years, and the left-out year's VIIRS count is predicted from MODIS. (2) 2023–2025 never enters the factor and is an independent test.

| Region | Monthly error | Yearly error (mean) | Worst year | 2023–2025 total |
|---|---|---|---|---|
| Türkiye | 11.8% | 4.6% | 11.3% | +1.5% |
| Balkans box | 8.7% | 3.1% | 5.2% | +3.8% |
| Caucasus box | 12.0% | 5.5% | 16.6% (2015) | +0.7% |
| Eastern Mediterranean box (experimental) | 23.7% | 15.4% | 43.6% (2020) | +18.7% |
| California box | 10.2% | 7.3% | 18.4% (2016) | 0.0% |
| Amazon arc box | 6.8% | 2.5% | 10.0% (2021) | −0.3% |
| Southeast Australia box (experimental) | 14.6% | 12.1% | 36.0% (2012) | +8.2% |

At the junction, the 2012 total for Türkiye predicted from MODIS without using any 2012 data differs from the VIIRS measurement by +1.0%. After harmonization the level ratio (2012–2025 against 2003–2011) is 1.00 in Türkiye, and in every region it follows the ratio MODIS shows on its own. That last point follows from the method and is not independent evidence; the two tests above are.

## 4. Finding: the ratio is not universal

The overall VIIRS/MODIS ratio after filtering is 3.25 in Türkiye, 3.65 in the Balkans box, 3.84 in the Amazon arc, 3.87 in the Caucasus, 4.30 in California, 5.12 in Southeast Australia and 7.07 in the Eastern Mediterranean. It also changes with the season (Türkiye: 1.98 in June, 4.48 in April; Amazon arc: below 1 in the wet season) and with the level of fire activity. Borrowing Türkiye's factors for the neighbouring boxes gives monthly errors of 14.4%, 17.5% and 52.9%, against 8.7%, 12.0% and 23.7% with each region's own factors. A single global conversion factor would therefore be wrong almost everywhere; each region needs its own calibration and its own test.

## 5. Limitations

- **Values before February 2012 are estimates, not measurements.** For one grid cell in one month the estimate is rough, and a cell where MODIS saw nothing stays zero.
- **Typical-year bias.** The factor fits a typical year. In the Türkiye test, busy months were overestimated by 6–15% and quiet months (less than half the usual level) underestimated by 38%.
- **2009 and 2011 (Türkiye).** August–October of 2009–2011 had more MODIS detections than any month used for testing (September 2011: 1.51 times the highest tested level). These months are flagged and are probably overestimated; the 2009 and 2011 yearly totals (65,656 and 61,117) should be read as upper bounds. Other regions have such months too (for example Balkans summer 2007, California June 2008, most Amazon dry seasons of 2002–2007).
- **Eastern Mediterranean box: experimental.** MODIS saw few fires there (13,284 detections in the calibration data, a seventh of Türkiye), the ratio swings between 4.6 and 10.3 from year to year, and about 15% of the VIIRS detections that pass the filter are probably industrial sources that FIRMS has not flagged.
- **Southeast Australia box: experimental.** The ratio depends on activity (5.4–5.9 in big fire years, 3.3–3.4 in quiet ones), so quiet years are overestimated by about a third (2012: +36%).
- **Amazon arc, 2003–2004.** Many MODIS detections of those years carry a static-source flag that does not look like a static source (seasonal, not persistent). They are removed by the common filter, so 2003 and 2004 may be 14–20% too low.
- **MODIS orbit drift from 2023.** Raw MODIS counts after 2022 are increasingly low. They are not used for the factor, and no MODIS-based estimates are made for recent years.
- **NOAA-20 multiplier.** The common 0.986 may leave values from November 2026 about 5% low in Southeast Australia and 3.5% low in the Amazon arc.
- **Data gaps.** Months where the source satellite sent no data for 3 or more days are marked and not corrected; their values are too low. Months filtered with the location mask run about 5% low (measured in Türkiye).
- **Overlapping boxes.** The Balkans, Caucasus and Eastern Mediterranean boxes overlap Türkiye, and each view uses its own factors. For Turkish territory the Türkiye view is the valid one; pre-2012 values for the same cells can differ between views (Caucasus: +8.0% over 2002–2011).
- **Climate context box.** Temperature and precipitation are a fire-weighted average of 5 points per region, placed where most detections occurred in 2012–2025. In Türkiye these points lie in Southeast Anatolia and Çukurova, not on the Aegean coast, so the box does not describe the weather of the Aegean region. It is shown alongside the fire counts; no causal claim is made.
- **What is counted.** A detection is a hot pixel seen in one satellite pass, not a fire. Boxes are sample areas, not country or biome totals.

## 6. Sources

Full list with licences and links: `docs/references.md`.

- **NASA FIRMS**, MODIS Collection 6.1 and VIIRS 375 m (S-NPP, NOAA-20) active fire data: archive download and API, https://firms.modaps.eosdis.nasa.gov. We acknowledge the use of data and/or imagery from NASA's Fire Information for Resource Management System (FIRMS) (https://earthdata.nasa.gov/firms), part of NASA's Land, Atmosphere Near real-time Capability for Earth observations (LANCE) (https://earthdata.nasa.gov/lance) and NASA's Earth Science Data and Information System (ESDIS).
- **NASA POWER** (T2M, PRECTOTCORR, monthly), https://power.larc.nasa.gov. The data was obtained from National Aeronautics and Space Administration (NASA) Langley Research Center's Prediction Of Worldwide Energy Resources (POWER) project funded through the NASA Earth Science Division. The data was obtained from the POWER Project's Monthly 2.10.0 version on 2026/11/15.
- **Natural Earth** 1:10m Admin 0 Countries and Land (public domain), https://www.naturalearthdata.com: Türkiye border and land/sea mask.
- **Inferno colour map** (matplotlib; Nathaniel Smith and Stéfan van der Walt; CC0), https://bids.github.io/colormap/ (calendar and map colour scale).
- **Leaflet** 1.9.4 and **OpenStreetMap** tiles (© OpenStreetMap contributors): map.
- **Claude / Claude Code** (Anthropic): code and documentation assistance.
