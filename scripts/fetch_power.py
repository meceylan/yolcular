# AI-assisted: generated with Claude (Anthropic)
"""Step 77 (fixed): monthly climate context from NASA POWER (no key needed), fire-weighted.

For each region listed in web/data/index.json: the region's land grid cells are grouped into 1 x 1 degree
blocks and the 5 blocks with the most fire detections in 2012-2025 (measured VIIRS months of the consistent
series) are chosen. In each block the point is the most active 0.25 deg cell; a cell on the coast (not all
8 neighbours on land) is moved to the nearest inland cell. One POWER monthly point request per point:
2m air temperature (T2M, deg C) and corrected precipitation (PRECTOTCORR, mm/day, written as a monthly
total in mm). The region value is the average of the 5 points weighted by each block's fire total.
Output: web/data/<region>/climate.json (small; the page never calls the API).

Usage: python scripts/fetch_power.py [--region <id>]
"""
import argparse
import calendar
import json
import time
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web" / "data"
API = ("https://power.larc.nasa.gov/api/temporal/monthly/point?parameters=T2M,PRECTOTCORR"
       "&community=AG&longitude={lon}&latitude={lat}&start=2002&end={end}&format=JSON")
CITATION = ("The data was obtained from National Aeronautics and Space Administration (NASA) Langley Research "
            "Center's Prediction Of Worldwide Energy Resources (POWER) project funded through the NASA Earth Science Division.")


def fetch(lat, lon):
    for end in (date.today().year, date.today().year - 1):   # the current year may not be published yet
        url = API.format(lat=lat, lon=lon, end=end)
        req = urllib.request.Request(url, headers={"User-Agent": "burn-calendar/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except Exception as e:   # noqa: BLE001
            print(f"  end={end}: {e}")
            time.sleep(3)
    raise RuntimeError("POWER request failed")


N_POINTS = 5
FIRE_YEARS = (2012, 2025)


def fire_points(rid):
    """The 5 most fire-active 1 x 1 degree land blocks of a region, one inland point in each, with weights."""
    g = json.loads((WEB / rid / "grid.json").read_text(encoding="utf-8"))
    months = g["months"]
    c = g["cell_deg"]
    ks = {k for k, ym in enumerate(months) if FIRE_YEARS[0] <= int(ym[:4]) <= FIRE_YEARS[1]}
    total = {}
    for x in g["cells"]:
        total[(x["i"], x["j"])] = sum(r[1] for r in x["d"] if r[0] in ks and r[1])
    cells = set(total)
    ctr = lambda i, j: ((i + 0.5) * c - 90, (j + 0.5) * c - 180)
    per = round(1 / c)
    blocks = {}
    for (i, j), v in total.items():
        blocks.setdefault((i // per, j // per), []).append(((i, j), v))
    inner = [t for t in cells if all((t[0] + a, t[1] + b) in cells for a in (-1, 0, 1) for b in (-1, 0, 1))]
    top = sorted(blocks.items(), key=lambda kv: -sum(v for _, v in kv[1]))[:N_POINTS]
    pts = []
    for _, members in top:
        (i, j), _v = max(members, key=lambda m: m[1])
        moved = False
        if (i, j) not in inner and inner:   # coastal cell: pull to the nearest inland cell
            i2, j2 = min(inner, key=lambda t: (t[0] - i) ** 2 + (t[1] - j) ** 2)
            moved = (i2, j2) != (i, j)
            i, j = i2, j2
        la, lo = ctr(i, j)
        pts.append({"lat": round(la, 3), "lon": round(lo, 3), "weight": round(sum(v for _, v in members), 1), "moved_inland": moved})
    return pts


def series(js):
    p = js["properties"]["parameter"]
    fill = js.get("header", {}).get("fill_value", -999)
    out = {}
    for key in sorted(p["T2M"]):
        y, m = int(key[:4]), int(key[4:])
        if m > 12:   # annual value
            continue
        t, pr = p["T2M"].get(key), p["PRECTOTCORR"].get(key)
        t = None if t is None or t == fill or t <= -900 else t
        pr = None if pr is None or pr == fill or pr <= -900 else pr * calendar.monthrange(y, m)[1]
        out[f"{y}-{m:02d}"] = (t, pr)
    return out


def wmean(pairs):
    pairs = [(v, w) for v, w in pairs if v is not None]
    sw = sum(w for _, w in pairs)
    return sum(v * w for v, w in pairs) / sw if pairs and sw > 0 else None


def region_climate(rid):
    pts = fire_points(rid)
    data, version = [], "?"
    for n, p in enumerate(pts):
        if n:
            time.sleep(2)   # be gentle with the service
        js = fetch(p["lat"], p["lon"])
        version = js.get("header", {}).get("api", {}).get("version", version)
        data.append(series(js))
    months = sorted(set().union(*[d.keys() for d in data]))
    t2m, prec, keep = [], [], []
    for ym in months:
        t = wmean([(d.get(ym, (None, None))[0], p["weight"]) for d, p in zip(data, pts)])
        pr = wmean([(d.get(ym, (None, None))[1], p["weight"]) for d, p in zip(data, pts)])
        if t is None and pr is None:
            continue
        keep.append(ym); t2m.append(None if t is None else round(t, 2)); prec.append(None if pr is None else round(pr, 1))
    out = {"source": "NASA POWER, monthly point data (T2M, PRECTOTCORR)", "api_version": version,
           "data_reference": f"The data was obtained from the POWER Project's Monthly {version.lstrip('v')} version on {date.today():%Y/%m/%d}.",
           "citation": CITATION, "url": "https://power.larc.nasa.gov",
           "method": "fire-weighted region average",
           "points": pts,
           "scope": f"fire-weighted average of {len(pts)} points: the most active 0.25 deg land cell in each of the "
                    f"{len(pts)} 1 x 1 deg blocks with the most fire detections {FIRE_YEARS[0]}-{FIRE_YEARS[1]}, "
                    "weighted by block fire totals; coastal cells moved to the nearest inland cell",
           "units": {"t2m": "deg C", "prec": "mm per month"},
           "baseline": "2002-2025", "fetched": date.today().isoformat(),
           "months": keep, "t2m": t2m, "prec": prec}
    (WEB / rid / "climate.json").write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    print(f"{rid}: {[(p['lat'], p['lon'], p['weight'], p['moved_inland']) for p in pts]} {keep[0]}..{keep[-1]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region")
    a = ap.parse_args()
    ids = [r["id"] for r in json.loads((WEB / "index.json").read_text(encoding="utf-8"))["regions"]]
    if a.region:
        ids = [a.region]
    for i, rid in enumerate(ids):
        if i:
            time.sleep(3)   # be gentle with the service
        region_climate(rid)


if __name__ == "__main__":
    main()
