---
name: trails
description: Turn a public walk or trail-run guide — text description, a list of landmarks, an image, or a rough/partial GPX — into a clean, followable GPX route on real OSM paths, with a map preview and quality metrics. Normalises the input into ordered waypoints (geocoding names, or tracing the OSM path network with Overpass where names run out), routes them with BRouter, reports distance/ascent/retrace and how much of the line is on roads-with-cars vs paths, and writes a GPX — with named waypoint pins for start, landmarks and destination that map apps show as labelled markers — for offline phone use (OsmAnd). Gates the route shape before saving. Use when the user says "trails", "plan this walk", "plan this run", "plan this trail run", "make a GPX for this route", "build me a route from these waypoints", or shares a walk or run guide to turn into a followable track. Needs full network (BRouter/Nominatim) — runs in Claude Code, not the claude.ai chat sandbox; the claude.ai path is a cloud variant over a brain-mcp tool.
---

# Trails

Turn a walk — described by a public guide or a handful of named landmarks — into one clean GPX the user can follow offline on their phone. Route the waypoints onto real paths, show a map, surface the quality metrics, and only save once the shape is confirmed.

**Core thesis: the guide is the *signal*, BRouter is the *renderer*.** The guide is authoritative on *where* the walk goes and roughly *how*; BRouter renders that intent onto actual OSM ways. The renderer must never override the signal — if a guide deliberately walks a road (e.g. to reach a viewpoint), keep it; don't let routing "optimise" it onto a parallel path that misses the point. Where the guide and the routed line disagree, **stop and surface it** rather than quietly improvising.

## Inputs — many signals, one renderer

The signal arrives in different forms. The skill's job is to **normalise whatever it gets into an ordered list of waypoints** (plus, optionally, an anchor track), then let BRouter render that onto real paths. Recognise which input you have and pick the adapter — the renderer downstream is identical:

- **Named landmarks → geocode (mode 1).** Resolve each via Nominatim → waypoints. Works in well-mapped "honeypot" areas; verify every resolved point. *Fails* where the route's middle has no geocodable names — BRouter then takes the shortest line (usually a road) and skips the walk's character.
- **Text turn-by-turn over sparse terrain → trace from OSM (mode 3).** Moor/forest walks whose turns ("up Moor Lane, through gates, to the sheep pens") don't geocode. Pull the OSM path network with Overpass and trace the track chain into waypoints. See below.
- **A published GPX, well-mapped → use or decimate.** Use it as-is, or thin it to waypoints and re-route.
- **A partially-right GPX → anchor (mode 2).** Keep the verbatim geometry where OSM is patchy (paths tens of metres off the nearest way are off BRouter's graph — no router fixes missing data); re-route only the parts safely on-graph. Anchor, don't blindly re-route.
- **An image (map photo, guide screenshot, sketch) → extract, then fall through.** Read the landmarks/shape off it, then route via mode 1 or mode 3. It's a signal to extract, not something to trace pixel-by-pixel.

A real walk often needs **more than one** — e.g. mode 1 anchors the ends, mode 3 traces the moor middle. Stay flexible; the through-line is *signal in → waypoints → BRouter → GPX + metrics, gated before saving*.

Other constants:

- **Tune for "avoid cars"** — `hiking-beta` sheds busy roads; `trekking` tolerates them. The main lever.
- **Won't do:** invent a route the user didn't ask for or pad to a round number; claim the line "follows paths" from eyeballing a map (say it from `car_m`/`foot_m`/retrace, and name the gap if unsure); route a river crossing (or any feature) the guide doesn't take — keep one bank if the guide does, and verify.

## Running the engine

Don't hand-roll BRouter/Nominatim calls — use the bundled engine:

```sh
python3 route.py \
  --waypoints "Malham|54.0608,-2.1490@Gordale Scar|Janet's Foss|Malham" \
  --pins "54.0703,-2.1530@Malham Cove::limestone amphitheatre" \
  --name "Malham Cove circuit" \
  --out-dir <dir> \
  [--profile hiking-beta]
```

- `--waypoints` is pipe-separated, **in walk order**; each item is a place name (geocoded via Nominatim) or a raw `lat,lon`. Prefer `lat,lon` for precision — geocoding a vague name ("X village") often lands wrong, so **verify any geocoded point** before trusting it (the engine prints what each name resolved to).
- For a **loop**, repeat the start as the final waypoint.
- It writes `<name>.gpx` and `<name>.html` to `--out-dir` and prints a JSON metrics block to stdout.
- **OS Outdoor tiles** in the preview: set `OS_API_KEY` in the repo `.env` (Data Hub key) — else the preview falls back to OpenTopoMap. OS tiles are GB-only and optional; never put the key in this file.

### Waypoint pins (markers in the app)

The GPX carries two layers: the `<trkpt>` line (the route) and `<wpt>` **pins** — named markers OsmAnd/Komoot/OS Maps render as labelled points (start, destination, landmarks). Give the user pins, not just a bare line.

- **Point grammar** (in both `--waypoints` and `--pins`): `lat,lon` · `lat,lon@Name` (label a coordinate) · `Place name` · and `::desc` on any of them for tap-text (`@The Strid::DO NOT jump it`).
- **Named routing waypoints become pins automatically** — first is `Start`, last is `Finish`, middles are `Waypoint`. A loop's repeated end coord isn't double-pinned. Bare unlabelled coords (mode-3 mechanical routing points) get no pin.
- **`--pins` marks landmarks that aren't routed through** — a viewpoint, a pub, the Strid sitting tens of metres off the path. They become `Landmark` pins **without bending the line toward them**. Don't add an off-path feature to `--waypoints` — that drags the route off course.
- **Pin at the real feature, only where the route passes it.** Use the landmark's own coordinate (Nominatim gives OSM's, which lines up with the OSM track), and confirm the route actually goes by — snap each candidate to the nearest trackpoint and drop any that are far off (a "riverside" pin 1 km from the line means that walk doesn't reach it). Don't pad the map with pins the walk never passes.

## Tracing a text guide over sparse terrain (mode 3)

When the guide is a turn-by-turn and the middle has no geocodable names (open moor, forest), geocoding the ends alone makes BRouter take the shortest line — typically a road — and skip the route's character (e.g. a "Barden Moor" loop came back 54% road, missing the moor entirely). Trace it from OSM instead:

1. **Anchor the ends.** Geocode the start, finish and any named points (village, named lane, pub).
2. **Pull the path network** in the corridor between anchors from Overpass — tracks, paths, bridleways, footways, **with geometry**. Named ways are sparse on the moor, so you need the unnamed ones too:

   ```sh
   curl -s -A "trails/1.0 (personal)" https://overpass-api.de/api/interpreter \
     --data-urlencode 'data=[out:json][timeout:30];way["highway"~"track|path|bridleway|footway"](S,W,N,E);out geom;'
   ```
   A bare `curl` returns `406 Not Acceptable` — the `-A` User-Agent is required. Public Overpass is flaky; retry or use a mirror.
3. **Find the chain.** Match the description to a connected track/bridleway chain across the corridor (e.g. Moor Lane → the long moor bridleway → the descent to the village) and drop one waypoint per link, so BRouter is pinned to the chain, not the road.
4. **Route, then verify against the guide.** Distance should land near the guide's figure, and `car_m` should be mostly the guide's *sanctioned* road (its stated approach/return), not a cop-out across the middle. Adjust and re-run: too long means a moor waypoint is too far out; too much road means one is missing. (Worked on Catgill Walk 5: bare anchors 5.3mi/54% road → traced chain 6.25mi vs the guide's 6.5mi, 4.2km of it bridleway.)

## The build loop (keep it tight)

Run the engine, then **show, ask one short question, adjust** — don't monologue:

1. **Route.** Build from the waypoints (or the guide's landmarks).
2. **Show.** Open/return the `.html` preview and the headline metrics (miles, ascent, retrace, foot vs car metres).
3. **Confirm or adjust** with one focused question — e.g. "Drop the road and route via the field path?" or "Keep this detour to the viewpoint?". Apply the edit by changing waypoints/profile and re-running. Each turn is a quick re-render, not an essay.
4. **Finalise** only when the user approves the shape.

## Reading the metrics

- **`miles` / `ascent_m`** — sanity-check against the guide's stated figures. A big mismatch means the waypoints are wrong, not the guide.
- **`retrace_pct`** — fraction of the back half within 25 m of the front half. High (>60%) = an out-and-back/lollipop; low = a true loop. Neither is bad — but it should match what the user expects.
- **`car_m` vs `foot_m`** — metres on roads-that-carry-cars vs foot-only ways. This is the "avoid cars" evidence. If `car_m` is high and unwanted, try `hiking-beta`, or reshape; if a road is *deliberate* (leads somewhere), keep it and say why.

## Where this runs

This skill bundles the engine and **calls BRouter/Nominatim/Overpass over the network**, so it needs full outbound internet. That means **Claude Code** (local Mac, or Claude Code on web with all-domains egress). It does **not** work inside the claude.ai chat sandbox, whose egress is restricted to package registries — BRouter/Nominatim are blocked there. The claude.ai path is a separate cloud variant that calls a brain-mcp `walk_route` tool backed by the same engine on the Mac (mirrors `capture` → `capture-cloud`).

## Output — where the GPX goes

- **In Claude Code (Mac):** write the final GPX into the vault at `~/brain/vault/Travel/`. It syncs to the phone via the normal vault sync; `Travel/` is shareable, and a public-walk GPX carries no PII. Name it clearly (`<Trip> - <Day> <Walk>.gpx`).
- **On the phone:** the user follows it offline in **OsmAnd** (free, worldwide OSM, imports GPX). OS Maps is GB-only — don't recommend it for non-UK walks.

## When to stop and ask

- A geocoded waypoint resolved somewhere implausible — surface it, don't route on a bad point.
- The routed line diverges from the guide's described path (crosses where the guide doesn't, takes a different bank/junction) — stop and surface; the guide is the signal.
- Metrics contradict the guide (distance off by a lot, a "riverside" walk full of `car_m`) — flag it rather than save.
- The user wants to keep a road the router avoids (or vice-versa) — confirm intent; don't silently re-optimise.
- BRouter or Nominatim errors/timeouts — relay plainly and retry once; don't fabricate a track.

## Anti-patterns

- Letting the renderer override the signal — re-routing off a deliberate road, snapping away from a published track where OSM is wrong.
- Claiming the route avoids roads / follows paths without citing the foot-vs-car metres.
- Trusting a geocoded place name without checking where it landed.
- Saving before the shape is approved, or saving a draft into `Travel/` as if final.
- Recommending OS Maps for an overseas walk (GB-only), or a subscription app when OsmAnd does the job free.
- Crossing a river/feature the guide doesn't, then asserting it matches the guide.
