#!/usr/bin/env python3
"""walk-route engine — turn waypoints into a clean BRouter/OSM walking route.

Stdlib-only (urllib) so it runs in a locked-down sandbox. Given an ordered list
of waypoints (place names geocoded via Nominatim, or raw `lat,lon`), it routes
them with BRouter, computes quality metrics, and emits a GPX plus a
self-contained HTML preview.

Design thesis: the public guide is the *signal* (where + roughly how); BRouter
is the *renderer* onto real OSM paths. Keep deliberate detours (a road to a
viewpoint); don't let routing optimise the signal away.

Usage:
  route.py --waypoints "Catgill Farm|53.9742,-1.8942|Bolton Abbey" \
           --name "Sat Loop" --out-dir /path [--profile hiking-beta] [--os-key KEY]

Point grammar (in --waypoints and --pins):
  lat,lon                routed; no pin unless labelled
  lat,lon@Name[::desc]   coordinate with a pin label (and optional tap-text)
  Place name[::desc]     geocoded; the name becomes the pin label

Named routing waypoints become GPX <wpt> pins automatically (first=Start,
last=Finish, middle=Waypoint). --pins are extra landmarks: marked but NOT
routed through, so an off-path feature (a viewpoint, the Strid) gets a pin
without bending the line toward it.

Prints a JSON metrics block to stdout; writes <name>.gpx and <name>.html to out-dir.
"""
import argparse
import json
import math
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

BROUTER = "https://brouter.de/brouter"
NOMINATIM = "https://nominatim.openstreetmap.org/search"
UA = "walk-route-skill/1.0 (personal walking-route generator)"

# highway= classes, split into car-bearing vs foot-only (for the road metric)
CAR = {"motorway", "trunk", "primary", "secondary", "tertiary", "unclassified",
       "residential", "service", "living_street", "road"}
FOOT = {"footway", "path", "track", "bridleway", "steps", "cycleway",
        "pedestrian", "byway"}


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read().decode("utf-8")


def geocode(name):
    """Resolve a place name to (lat, lon) via Nominatim. Returns None if unsure."""
    q = urllib.parse.urlencode({"q": name, "format": "json", "limit": 1})
    try:
        data = json.loads(_get(f"{NOMINATIM}?{q}"))
    except Exception as e:
        print(f"  ! geocode failed for {name!r}: {e}", file=sys.stderr)
        return None
    time.sleep(1.1)  # Nominatim usage policy: <=1 req/s
    if not data:
        return None
    return float(data[0]["lat"]), float(data[0]["lon"])


COORD_RE = re.compile(r"(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)")


def _split_desc(s):
    """'Name::desc' -> ('Name', 'desc'); 'Name' -> ('Name', None)."""
    if s is None:
        return None, None
    if "::" in s:
        name, desc = s.split("::", 1)
        return name.strip(), desc.strip()
    return s.strip(), None


def parse_points(spec, kind="waypoint"):
    """Pipe-separated points. Each item is one of:
        lat,lon                 bare coordinate (routed; no pin unless labelled)
        lat,lon@Name[::desc]    coordinate with a pin label (+ optional tap-text)
        Place name[::desc]      geocoded; the name becomes the pin label
    Returns a list of (lat, lon, name, desc). `name` is None only for a bare,
    unlabelled coordinate (a mechanical routing pin not worth marking)."""
    out = []
    for raw in spec.split("|"):
        item = raw.strip()
        if not item:
            continue
        if "@" in item:
            point, label = item.split("@", 1)
            point = point.strip()
            name, desc = _split_desc(label)
        else:
            point, name, desc = item, None, None
        m = COORD_RE.fullmatch(point)
        if m:
            out.append((float(m.group(1)), float(m.group(2)), name, desc))
            continue
        # named point: when no @label was given, the name itself may carry ::desc
        if name is None:
            name, desc = _split_desc(point)
            geo_q = name
        else:
            geo_q = point
        ll = geocode(geo_q)
        if ll is None:
            raise SystemExit(f"Could not geocode {kind}: {geo_q!r}")
        out.append((ll[0], ll[1], name, desc))
        print(f"  geocoded {geo_q!r} -> {ll[0]:.5f},{ll[1]:.5f}", file=sys.stderr)
    return out


def brouter(waypoints, profile, fmt):
    lonlats = "|".join(f"{lon},{lat}" for lat, lon, *_ in waypoints)
    q = urllib.parse.urlencode({
        "lonlats": lonlats, "profile": profile,
        "alternativeidx": 0, "format": fmt})
    return _get(f"{BROUTER}?{q}")


def haversine(a, b):
    R = 6371000.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp = math.radians(b[0] - a[0])
    dl = math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def gpx_trackpoints(gpx):
    return [(float(la), float(lo)) for lo, la in
            re.findall(r'<trkpt lon="([-\d.]+)" lat="([-\d.]+)"', gpx)]


def retrace_pct(pts, thresh=25.0):
    """Fraction of second-half points within `thresh` m of any first-half point.
    High = out-and-back; low = a true loop."""
    if len(pts) < 4:
        return 0.0
    mid = len(pts) // 2
    first, second = pts[:mid], pts[mid:]
    # coarse stride to keep it O(n) enough for interactive use
    stride = max(1, len(first) // 200)
    near = 0
    for q in second:
        for i in range(0, len(first), stride):
            if haversine(q, first[i]) <= thresh:
                near += 1
                break
    return round(100 * near / len(second), 1)


def road_metres(geojson):
    """Sum segment distances by highway class from BRouter's message table."""
    data = json.loads(geojson)
    msgs = data["features"][0]["properties"].get("messages")
    if not msgs:
        return {}
    header = msgs[0]
    di = header.index("Distance") if "Distance" in header else None
    wi = header.index("WayTags") if "WayTags" in header else None
    if di is None or wi is None:
        return {}
    car = foot = other = 0
    for row in msgs[1:]:
        try:
            dist = float(row[di])
        except (ValueError, IndexError):
            continue
        tags = row[wi] if wi < len(row) else ""
        m = re.search(r"highway=([\w_]+)", tags)
        cls = m.group(1) if m else ""
        if cls in CAR:
            car += dist
        elif cls in FOOT:
            foot += dist
        else:
            other += dist
    return {"car_m": round(car), "foot_m": round(foot), "other_m": round(other)}


HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/proj4js/2.11.0/proj4.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/proj4leaflet/1.0.2/proj4leaflet.min.js"></script>
<style>html,body{margin:0;height:100%}#map{height:100%}
.info{position:absolute;z-index:1000;top:10px;left:50px;background:#fff;padding:6px 10px;
border-radius:6px;font:13px system-ui;box-shadow:0 1px 4px rgba(0,0,0,.3)}</style></head>
<body><div class="info"><b>__TITLE__</b><br>__SUBTITLE__</div><div id="map"></div>
<script>
var pts = __PTS__, marks = __MARKS__, osKey = "__OSKEY__";
var bng = new L.Proj.CRS('EPSG:27700',
  '+proj=tmerc +lat_0=49 +lon_0=-2 +k=0.9996012717 +x_0=400000 +y_0=-100000 ' +
  '+ellps=airy +towgs84=446.448,-125.157,542.06,0.15,0.247,0.842,-20.489 +units=m +no_defs',
  {resolutions:[896,448,224,112,56,28,14,7,3.5,1.75], origin:[-238375.0,1376256.0]});
var base, map;
if (osKey) {
  base = L.tileLayer('https://api.os.uk/maps/raster/v1/zxy/Outdoor_27700/{z}/{x}/{y}.png?key='+osKey,
    {maxZoom:9,minZoom:0,attribution:'Contains OS data &copy; Crown copyright and database rights 2026'});
  map = L.map('map',{crs:bng,layers:[base],minZoom:0,maxZoom:9});
} else {
  base = L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
    {maxZoom:17,attribution:'&copy; OpenTopoMap (CC-BY-SA)'});
  map = L.map('map',{layers:[base]});
}
var line = L.polyline(pts,{color:'#d6336c',weight:4,opacity:.9});
var grp = [line];
marks.forEach(function(m){grp.push(L.marker(m.ll).bindTooltip(m.label));});
var route = L.layerGroup(grp).addTo(map);
L.control.layers({'Base':base},{'Route':route},{collapsed:false}).addTo(map);
map.fitBounds(line.getBounds(),{padding:[30,30]});
</script></body></html>
"""


def _xesc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def wpt_xml(lat, lon, name, desc, typ):
    """One GPX <wpt> pin (name, optional desc, type for app grouping)."""
    parts = [f' <wpt lat="{lat:.5f}" lon="{lon:.5f}">',
             f'  <name>{_xesc(name)}</name>']
    if desc:
        parts.append(f'  <desc>{_xesc(desc)}</desc>')
    parts.append(f'  <type>{_xesc(typ)}</type>')
    parts.append(' </wpt>')
    return "\n".join(parts) + "\n"


def build_pins(wps, pins):
    """Turn routing waypoints + extra landmarks into (lat,lon,name,desc,type)
    pin rows. Named endpoints become Start/Finish; named middles, Waypoint;
    every --pin, Landmark. A loop's repeated end coordinate is not double-pinned."""
    rows = []
    first = (wps[0][0], wps[0][1])
    n = len(wps)
    for i, (la, lo, name, desc) in enumerate(wps):
        if i == 0:
            typ = "Start"
        elif i == n - 1:
            if (la, lo) == first:      # loop close: same point as Start
                continue
            typ = "Finish"
        else:
            typ = "Waypoint"
        if name is None:
            if typ not in ("Start", "Finish"):
                continue               # unnamed middle = mechanical routing pin
            name = typ                 # generic label for an unnamed endpoint
        rows.append((la, lo, name, desc, typ))
    for la, lo, name, desc in pins:
        rows.append((la, lo, name or f"{la:.5f},{lo:.5f}", desc, "Landmark"))
    return rows


def insert_wpts(gpx, rows):
    """Splice <wpt> pins in before <trk> (correct GPX element order)."""
    if not rows:
        return gpx
    block = "".join(wpt_xml(*r) for r in rows)
    idx = gpx.find("<trk")
    return gpx if idx == -1 else gpx[:idx] + block + gpx[idx:]


def write_html(path, title, subtitle, pts, marks, os_key):
    html = (HTML.replace("__TITLE__", title).replace("__SUBTITLE__", subtitle)
            .replace("__PTS__", json.dumps([[la, lo] for la, lo in pts]))
            .replace("__MARKS__", json.dumps(marks))
            .replace("__OSKEY__", os_key or ""))
    path.write_text(html)


def main():
    ap = argparse.ArgumentParser(description="Build a walking route from waypoints.")
    ap.add_argument("--waypoints", required=True,
                    help="Pipe-separated routed points: 'lat,lon', "
                         "'lat,lon@Name[::desc]', or 'Place name[::desc]'. "
                         "Named points become Start/Finish/Waypoint pins.")
    ap.add_argument("--pins", default="",
                    help="Pipe-separated extra landmarks (same grammar) marked "
                         "as pins but NOT routed through — for off-path features.")
    ap.add_argument("--name", required=True, help="Route name (used for filenames).")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--profile", default="hiking-beta",
                    help="BRouter profile (hiking-beta avoids busy roads; trekking tolerates them).")
    ap.add_argument("--os-key", default="",
                    help="OS Data Hub API key for Outdoor tiles (else $OS_API_KEY, else OpenTopoMap).")
    args = ap.parse_args()

    os_key = args.os_key or os.environ.get("OS_API_KEY", "")
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    wps = parse_points(args.waypoints, "waypoint")
    if len(wps) < 2:
        raise SystemExit("Need at least two waypoints.")
    pins = parse_points(args.pins, "pin") if args.pins else []
    gpx = brouter(wps, args.profile, "gpx")
    pts = gpx_trackpoints(gpx)
    if not pts:
        raise SystemExit("BRouter returned no track — check waypoints/profile.")

    geo = brouter(wps, args.profile, "geojson")
    pin_rows = build_pins(wps, pins)
    gpx = insert_wpts(gpx, pin_rows)

    m = re.search(r"track-length = (\d+) filtered ascend = (\d+)", gpx)
    length_m = int(m.group(1)) if m else 0
    ascent_m = int(m.group(2)) if m else 0

    metrics = {
        "name": args.name,
        "profile": args.profile,
        "miles": round(length_m / 1609.34, 2),
        "length_m": length_m,
        "ascent_m": ascent_m,
        "trackpoints": len(pts),
        "retrace_pct": retrace_pct(pts),
        **road_metres(geo),
        "waypoints": [{"label": name, "ll": [la, lo]} for la, lo, name, _ in wps],
        "pins": [{"label": name, "type": typ, "ll": [la, lo]}
                 for la, lo, name, _, typ in pin_rows],
    }

    gpx_path = out / f"{args.name}.gpx"
    html_path = out / f"{args.name}.html"
    gpx_path.write_text(gpx)
    subtitle = f"{metrics['miles']} mi &middot; {ascent_m} m ascent &middot; {metrics['retrace_pct']}% retrace"
    marks = [{"ll": [la, lo], "label": name} for la, lo, name, _, _ in pin_rows]
    write_html(html_path, args.name, subtitle, pts, marks, os_key)

    metrics["gpx"] = str(gpx_path)
    metrics["html"] = str(html_path)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
