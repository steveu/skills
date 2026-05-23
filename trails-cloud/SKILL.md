---
name: trails-cloud
description: Turn a public walk or trail-run guide — named landmarks, a photo of a guide, text turn-by-turn, coordinates, or a published GPX — into a clean, followable GPX on real OSM paths, by driving the brain-mcp `walk_route` and `save_route` tools (the engine runs on the Mac; the claude.ai sandbox can't reach BRouter/Nominatim). Normalises the input into the tool's ordered-waypoint grammar in the model, calls `walk_route` for metrics and a map URL, shows that preview, and files the GPX to the vault's `Travel/` via `save_route` only once the shape is approved. Use when, in claude.ai, the user says "plan this walk", "plan this run", "make a GPX for this route", "build me a route from these waypoints", or shares a walk/run guide to turn into a followable track. In Claude Code on the Mac use the `trails` skill instead — it bundles the engine and traces the OSM network with Overpass; this cloud variant defers sparse-terrain tracing and partial-GPX anchoring to it.
---

# Trails (cloud)

Turn a walk — a public guide or a handful of named landmarks — into one clean GPX the user can follow offline on their phone, **from inside claude.ai**, by driving the brain-mcp `walk_route` and `save_route` tools. Route the waypoints onto real paths, show the returned map and metrics, and only save once the shape is confirmed.

**Core thesis: the guide is the *signal*, BRouter is the *renderer*.** The guide is authoritative on *where* the walk goes and roughly *how*; `walk_route` (BRouter, server-side) renders that intent onto actual OSM ways. The renderer must never override the signal — if a guide deliberately walks a road (e.g. to reach a viewpoint), keep it; don't let routing "optimise" it onto a parallel path that misses the point. Where the guide and the routed line disagree, **stop and surface it** rather than quietly improvising.

## Why this drives a tool, not an engine

The route engine needs full outbound network (BRouter, Nominatim) and runs on the Mac. The **claude.ai sandbox can't reach those services**, so this skill never routes locally — it **calls the brain-mcp `walk_route` tool**, which runs the same engine server-side and returns the metrics and a map URL. `save_route` then files the chosen draft into the vault. Your job here is the *adapter* — turn whatever the user gives you into the tool's waypoint grammar — plus the *gate*: show, confirm, then save.

This mirrors `capture` driving the brain-mcp `capture` tool. The Claude Code `trails` skill is the richer sibling: it bundles the engine, traces the OSM path network with Overpass over sparse terrain, and anchors a partially-right GPX where OSM is patchy. Those two need network and compute the sandbox doesn't have — so **defer them to `trails` on the Mac** rather than faking them here.

## Inputs — the adapters live in the model

The signal arrives in different forms. Recognise which you have and normalise it into an ordered list of waypoints in the tool's grammar; the renderer downstream is identical. What you can do here, in-model:

- **Named landmarks → pass the names.** `walk_route` geocodes each via Nominatim. Works in well-mapped areas; **verify every resolved point** in the returned metrics before trusting it (the tool flags wild outliers, but a subtly-wrong town it won't).
- **Explicit coordinates → pass `lat,lon`.** Prefer these for precision — geocoding a vague name often lands wrong.
- **A photo / screenshot / sketch of a guide → read it, then fall through.** Extract the ordered landmarks and rough shape off the image, then pass them as names or coords. It's a signal to extract, not something to trace pixel-by-pixel.
- **Text turn-by-turn → extract the ordered named points.** Pull the sequence of geocodable points (village, named lane, pub, named crag) into waypoints. Where the *middle* has no geocodable names (open moor, forest), `walk_route` will take the shortest line — usually a road — and skip the walk's character. That's the case the CC `trails` skill solves with Overpass tracing; **don't fake it here** — say so and offer to hand off to `trails` on the Mac.
- **A published GPX → decimate to waypoints.** Read the file's coordinates and drop a handful of ordered `lat,lon` points (start, key turns, finish), then re-route. True *anchoring* — keeping verbatim geometry where OSM is patchy and the line sits off BRouter's graph — isn't available through the tool (it always re-routes); if a section is genuinely off-graph, flag it and defer to `trails`.

A real walk often mixes these — named ends, a few coords through the middle. Stay flexible; the through-line is *signal in → waypoints → `walk_route` → metrics + map, gated before `save_route`*.

**Tune for "avoid cars":** the `profile` argument. `hiking-beta` (the default) sheds busy roads; `trekking` tolerates them. The main lever.

**Won't do:** invent a route the user didn't ask for or pad to a round number; claim the line "follows paths" from eyeballing — say it from the `car_m`/`foot_m`/retrace the tool returns, and name the gap if unsure; route a river crossing (or any feature) the guide doesn't take.

## The waypoint grammar

Both `waypoints` and `pins` are **pipe-separated, in walk order**. Each item is one of:

- `lat,lon` — a routed point, no pin (e.g. `54.0608,-2.1490`)
- `lat,lon@Name` — a coordinate with a labelled pin (e.g. `54.0703,-2.1530@Malham Cove`)
- `Place name` — geocoded by the tool; the name becomes the pin label (e.g. `Janet's Foss`)
- append `::desc` to any of the above for tap-text on the pin (e.g. `@The Strid::DO NOT jump it`)

For a **loop**, repeat the start as the final waypoint. Minimum two waypoints.

### Pins (markers in the app)

The GPX carries two layers: the `<trkpt>` line (the route) and `<wpt>` **pins** — named markers OsmAnd/OS Maps render as labelled points. Give the user pins, not just a bare line.

- **Named routing waypoints become pins automatically** — first is `Start`, last is `Finish`, middles are `Waypoint`. A loop's repeated end coord isn't double-pinned. Bare unlabelled coords get no pin.
- **The `pins` argument marks landmarks the route passes but isn't routed *through*** — a viewpoint, a pub, a feature tens of metres off the path. They become `Landmark` pins **without bending the line toward them**. Don't put an off-path feature in `waypoints` — that drags the route off course.
- **Pin at the real feature, only where the route passes it.** Use the landmark's own coordinate and confirm the route actually goes by; drop a "riverside" pin the line never reaches.

## Driving `walk_route`

Call the tool with the normalised grammar:

- `waypoints` (required) — pipe-separated, in order, e.g. `Catgill Farm|54.0089,-1.8889@Cavendish Pavilion::Cafe stop|Bolton Abbey`
- `name` (required) — the route name; used for the draft filename **and to key the draft**. **Keep it stable across edits to the same route** — re-running with the same name overwrites the same draft (and reuses its id), which is exactly what the build loop wants. A new name forks a new draft.
- `pins` (optional) — off-route landmarks, same grammar
- `profile` (optional) — defaults `hiking-beta`; pass `trekking` to tolerate roads
- `basemap` (optional) — `os` (OS Outdoor detail) or `opentopo`; defaults to OS when the server has an OS key, else OpenTopoMap. Leave unset unless the user asks.

The tool returns a plain-text block: the headline metrics, the resolved waypoints and pins, any **⚠ bad-geocode** warnings, a **`Map:` URL**, and a **`Draft id:`**.

## The build → preview → gate → save loop

Run the tool, then **show, ask one short question, adjust** — don't monologue.

1. **Build.** Call `walk_route` from the normalised waypoints.
2. **Preview.** Relay to the user the headline metrics (miles, ascent, retrace, foot-vs-car metres) and the **`Map:` URL exactly as the tool returned it** — never fabricate or guess a hostname. If the tool says the map URL is unavailable, say so plainly; the route still built and can still be saved.
3. **Gate.** Check the resolved waypoints and any ⚠ warnings, then ask one focused question — "Drop the road and route via the field path?", "Keep the detour to the viewpoint?". Apply the edit by changing `waypoints`/`profile` and **re-running with the same `name`** (overwrites the draft). Each turn is a quick re-render, not an essay.
4. **Save.** Only once the user approves the shape, call `save_route` with the **`id` from the metrics block** (16 hex chars), optionally a `filename`. It copies the draft GPX into the vault's `Travel/` and returns the saved path. This is the gate — never save an unapproved draft.

## Reading the returned metrics

- **`mi` / `m ascent`** — sanity-check against the guide's stated figures. A big mismatch means the waypoints are wrong, not the guide.
- **retrace %** — fraction of the back half within ~25 m of the front half. High (>60%) = an out-and-back/lollipop; low = a true loop. Neither is bad, but it should match what the user expects.
- **roads-with-cars vs foot-only metres** — the "avoid cars" evidence. If the car metres are high and unwanted, try `trekking`→`hiking-beta` or reshape; if a road is *deliberate* (it leads somewhere), keep it and say why.
- **⚠ bad-geocode warnings** — a waypoint resolved far from the rest. Almost always a wrong town/country; fix the input, don't route on it.

## Output — where the GPX goes

`save_route` files the GPX into the vault's `Travel/` folder on the Mac. It syncs to the phone via the normal vault sync; `Travel/` is shareable, and a public-walk GPX carries no PII. Name it clearly (`<Trip> - <Day> <Walk>.gpx`). On the phone the user follows it offline in **OsmAnd** (free, worldwide OSM, imports GPX). OS Maps is GB-only — don't recommend it for non-UK walks.

## When to stop and ask

- A geocoded waypoint resolved somewhere implausible (the ⚠ warning, or a town you don't recognise) — surface it; don't save on a bad point.
- The routed line diverges from the guide's described path (crosses where the guide doesn't, takes a different bank/junction) — stop and surface; the guide is the signal.
- The metrics contradict the guide (distance off by a lot, a "riverside" walk full of road metres) — flag it rather than save.
- The user wants to keep a road the router avoids (or vice-versa) — confirm intent; don't silently re-optimise.
- The walk needs sparse-terrain tracing or genuine off-graph anchoring — say the cloud tool can't, and offer to hand off to the Claude Code `trails` skill on the Mac.
- `walk_route`/`save_route` is unavailable or errors — relay it plainly; don't fabricate a track, a map URL, or a saved path.

## Anti-patterns

- Routing locally or hand-rolling BRouter/Nominatim/Overpass calls — the sandbox can't reach them; always go through the tools.
- Hardcoding or guessing the map hostname — the tool returns the URL; relay only that.
- Letting the renderer override the signal — re-routing off a deliberate road, snapping away from a line the guide clearly takes.
- Claiming the route avoids roads / follows paths without citing the foot-vs-car metres the tool returned.
- Trusting a geocoded place name without checking where it landed.
- Calling `save_route` before the user has approved the shape, or with an id you didn't get back from `walk_route`.
- Faking mode-3 tracing or partial-GPX anchoring instead of deferring to `trails` on the Mac.
- Recommending OS Maps for an overseas walk (GB-only), or a subscription app when OsmAnd does the job free.
