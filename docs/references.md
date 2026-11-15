# References

Every external source used in this project (libraries, data, images, basemaps). This list feeds the competition form's reference field.

| Resource | Type | Link | Use |
|---|---|---|---|
| NASA FIRMS (MODIS and VIIRS active fire data) | Data | https://firms.modaps.eosdis.nasa.gov | Fire hotspot detections |
| FIRMS Archive Download (MODIS C6.1 and VIIRS S-NPP C2 standard files; Türkiye 2012–2025, box regions MODIS from July 2002 and VIIRS S-NPP from 2012 to 2025) | Data | https://firms.modaps.eosdis.nasa.gov/download/ | Long-term archive for all regions (see docs/method.md) |
| FIRMS API (data_availability, area) | Data API | https://firms.modaps.eosdis.nasa.gov/api/ | Source availability check and downloads |
| FIRMS active fire data attributes for MODIS and VIIRS | Documentation | https://www.earthdata.nasa.gov/data/tools/firms/active-fire-data-attributes-modis-viirs | Column definitions, confidence and type fields |
| NASA POWER Project (Prediction Of Worldwide Energy Resources), monthly point API, parameters T2M and PRECTOTCORR | Data API | https://power.larc.nasa.gov | Climate context box (step 77): monthly temperature and precipitation, fire-weighted average of 5 inland points per region (most fire-active 1° areas, 2012–2025), 2002–2026, scripts/fetch_power.py |
| VIIRS I-Band 375 m active fire product page | Documentation | https://www.earthdata.nasa.gov/data/instruments/viirs/viirs-i-band-375-m-active-fire-data | VIIRS product description and confidence classes |
| Natural Earth 1:10m Admin 0 Countries (public domain) | Data | https://www.naturalearthdata.com (file via https://github.com/nvkelso/natural-earth-vector) | Türkiye border mask for API data (`data/boundaries/TUR.geojson`) |
| Natural Earth 1:10m Land (public domain) | Data | https://www.naturalearthdata.com (file via https://github.com/nvkelso/natural-earth-vector, `geojson/ne_10m_land.geojson`) | Land/sea mask for all box regions (`data/boundaries/ne_10m_land.geojson`, not in git) |
| numpy | Library | https://numpy.org | Array calculations in the scripts |
| pyarrow | Library | https://arrow.apache.org | Parquet files |
| matplotlib | Library | https://matplotlib.org | Charts in the data report |
| Viridis colour map (matplotlib, Stéfan van der Walt and Nathaniel Smith; CC0) | Colour scale | https://bids.github.io/colormap/ | Colour-blind-safe scale of the first version of the burn calendar (replaced by inferno) |
| Inferno colour map (matplotlib, Nathaniel Smith and Stéfan van der Walt; CC0) | Colour scale | https://bids.github.io/colormap/ | Burn calendar and map layer colour scale on the published page |
| Leaflet 1.9.4 (BSD-2-Clause) | Library | https://leafletjs.com (loaded from cdnjs: https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/) | Map and rectangle area selection |
| cdnjs (Cloudflare) | CDN | https://cdnjs.com | Serves the Leaflet files |
| OpenStreetMap standard tiles (© OpenStreetMap contributors, ODbL; tile usage policy) | Basemap | https://www.openstreetmap.org/copyright | Background map; attribution shown on the map and in the page footer |
| pandas | Library | https://pandas.pydata.org | Table processing |
| requests | Library | https://requests.readthedocs.io | HTTP requests to FIRMS API |
| Claude / Claude Code (Anthropic) | AI tool | https://claude.com | Code and documentation assistance |
| GitHub Actions (checkout, configure-pages, upload-pages-artifact, deploy-pages) | Tool | https://github.com/features/actions | Publishing web/ to GitHub Pages |
| GitHub Pages | Hosting | https://pages.github.com | Hosting the static site |
| WCAG 2.1 (W3C), success criteria 1.4.1 and 1.4.11 | Standard | https://www.w3.org/TR/WCAG21/ | Contrast and colour-use criteria for the calendar |
| Machado, Oliveira and Fernandes (2009), "A physiologically-based model for simulation of color vision deficiency", IEEE TVCG | Method | https://doi.org/10.1109/TVCG.2009.113 | Colour-blindness simulation in scripts/check_a11y.py |
| CIEDE2000 colour difference (CIE 142-2001; Sharma, Wu and Dalal 2005) | Method | https://doi.org/10.1002/col.20070 | Colour-step measurement in scripts/check_a11y.py |

## FIRMS acknowledgment and disclaimer

Source: NASA FIRMS download README, https://firms.modaps.eosdis.nasa.gov/download/Readme.txt (section "DATA CITATION AND DISCLAIMER"). NASA asks that anyone who provides LANCE / FIRMS data to a third party follows the citation guidelines and replicates or links to the disclaimer. The page footer carries the acknowledgment and links the disclaimer.

**Acknowledgment (used in the page footer and in every CSV header):** the FIRMS acknowledgment on the NASA Earthdata FIRMS page, section "Acknowledgments", https://www.earthdata.nasa.gov/data/tools/firms (read 15 November 2026):

> We acknowledge the use of data and/or imagery from NASA's Fire Information for Resource Management System (FIRMS) (https://earthdata.nasa.gov/firms), part of NASA's Land, Atmosphere Near real-time Capability for Earth observations (LANCE) (https://earthdata.nasa.gov/lance) and NASA's Earth Science Data and Information System (ESDIS).

The same page lists the product papers: Giglio, Schroeder and Justice (2016), Remote Sensing of Environment 178: 31-41, doi:10.1016/j.rse.2016.02.054 (MODIS Collection 6 active fire); Schroeder, Oliva, Giglio and Csiszar (2014), Remote Sensing of Environment 143: 85-96, doi:10.1016/j.rse.2013.12.008 (VIIRS 375 m active fire).

**Disclaimer (verbatim from the README):**

> NASA promotes the full and open sharing of all data with the research and applications communities, private industry, academia, and the general public. Read the NASA Data and Information Policy.
>
> If you provide the LANCE / FIRMS data to a third party, we request you follow the guidelines in the citation and replicate or provide a link to the disclaimer.
>
> LANCE is operated by the ESDIS Project. The information presented through LANCE, GIBS, Worldview, and FIRMS are provided “as is” and users bear all responsibility and liability for their use of data, and for any loss of business or profits, or for any indirect, incidental or consequential damages arising out of any use of, or inability to use, the data, even if NASA or ESDIS were previously advised of the possibility of such damages, or for any other claim by you or any other person. Due to the spatial resolution and other characteristics of these data, their use for tactical decision-making or informing about conditions at a local scale are not advised.
>
> ESDIS makes no representations or warranties of any kind, express or implied, including implied warranties of fitness for a particular purpose or merchantability, or with respect to the accuracy of or the absence or the presence or defects or errors in data, databases of other information. The designations employed in the data do not imply the expression of any opinion whatsoever on the part of ESDIS concerning the legal or development status of any country, territory, city or area or of its authorities, or concerning the delimitation of its frontiers or boundaries. For more information please contact Earthdata Support: earthdata-support@nasa.gov.

## NASA POWER acknowledgment (step 77)

Wording from the POWER Referencing Guide (https://power.larc.nasa.gov/docs/referencing/), which asks for both lines:

> POWER's Reference: The data was obtained from National Aeronautics and Space Administration (NASA) Langley Research Center's Prediction Of Worldwide Energy Resources (POWER) project funded through the NASA Earth Science Division.
>
> POWER's Data Reference: The data was obtained from the POWER Project's Monthly 2.10.0 version on 2026/11/15.

Used on the page in "About the data" and stored in each web/data/<region>/climate.json (fields `citation`, `data_reference`). Method: fire-weighted region average of 5 points (most active 0.25° land cell in each of the 5 one-degree blocks with the most detections in 2012–2025, coastal cells moved to the nearest inland cell, weights = block fire totals); points and weights are listed in each climate.json (`points`). The project also asks to be told about publications and redistribution (larc-power-project@mail.nasa.gov); that is the team's decision.
