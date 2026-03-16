# Codex prompt: fix stations line chart loading direction, timeline alignment, and colour system

Please update `uk_aq_stations_chart.html` to improve the chart loading behaviour and visual consistency.

## Goal

Make the line chart feel like it loads **from most recent to oldest**, while keeping the **full selected time range fixed from the start**.

When changing from a small window to a larger one, the newest data on the right should remain visible immediately, and the chart should progressively fill older history **from right to left**.

Also make the timeline width match the **chart plot area** exactly, and update the chart colour accents to match the blue accent system used in `uk_aq_hex_map.html`.

## Files

- Primary file to edit: `uk_aq_stations_chart.html`
- Reference styling file: `uk_aq_hex_map.html`

## Required behaviour changes

### 1) Keep the full requested x-domain fixed from the first render

Right now the chart appears to reframe while loading older data. Change this so that:

- the full requested time range is reserved immediately when a window is selected
- the x-axis domain is fixed to the requested `range.startMs -> range.endMs` from the first frame
- the newest data remains pinned to the right edge
- older data is progressively revealed into the existing fixed domain
- do **not** visually grow the domain as chunks arrive

Important:

- stop rendering intermediate chart states with `domainStartMs: displayedStartMs`
- instead, keep intermediate and final renders anchored to the full requested domain
- the chart should look like history is being filled in from the right side backwards, not like the plot is expanding or zooming out

### 2) Preserve the newest visible data when switching to a larger window

When the user switches from a smaller window such as `24h` to a larger one such as `7d`, `31d`, or `90d`:

- keep the already available recent data visible immediately on the right
- start fetching missing older data only for the newly needed earlier period
- progressively reveal that older data toward the left
- avoid clearing the chart and redrawing from scratch unless there is no usable seed data

This should feel continuous and stable.

### 3) Keep fetch order newest-to-oldest, but make the visual reveal smooth

It is fine to keep chunked fetching under the hood, but the visual result should feel smooth rather than obviously blocky.

Requirements:

- continue requesting older history in reverse time order, newest to oldest
- preserve correctness of merged data and cache logic
- smooth the visual reveal so users perceive a continuous right-to-left fill
- avoid abrupt jumps in timeline boundary position or chart appearance where possible

### 4) Timeline must align to the plot area, not the full SVG/card width

The timescale/timeline at the top currently does not match the chart width.

Please change it so that:

- the timeline track width matches the **inner plot area** of the chart exactly
- the timeline starts at the same left inset as the plotted data area
- the timeline ends at the same right inset as the plotted data area
- it should **not** align to the full SVG width including y-axis gutter
- it should **not** align to the outer card width

Implementation is up to you, but the timeline and plot area must stay locked together responsively.

A good approach is to derive both from the same margin/inset values or expose the inner plot geometry to the timeline layout.

### 5) Timeline loading direction must be right-to-left

The loading model should clearly communicate that recent data is available first and older data is still being loaded.

Required behaviour:

- newest side is the right side
- loaded portion should begin at the right and extend leftward as older data arrives
- unloaded portion should remain on the left until fetched
- the loading boundary should move left as loading progresses
- the visual logic of the timeline must match the chart reveal direction

### 6) Keep a fixed centered “Loading” label above the timeline

Change the timeline loading label behaviour so that:

- it simply says `Loading`
- it stays centered above the timeline
- it does **not** move with the boundary
- it does **not** track the current loaded position
- it can remain visible only while loading is active

Do not animate the text position.

### 7) Use the colour system from `uk_aq_hex_map.html`

Update the chart accent colours to match the hex map page.

Use the same blue accent family as the hex map, especially the main accent blue:

- main accent blue: `#3C78AC`

Apply that blue system consistently to the station chart UI where appropriate, such as:

- main line colour
- timeline loaded bar / progress accent
- active button or active control states related to the chart
- other subtle chart accents that currently use teal

Please also derive lighter variants from that same blue for secondary fills, subtle states, and softer accents as needed.

### 8) Keep existing AQI / health colours that should stay semantic

Do **not** replace semantic colours that carry meaning.

Keep these intact unless there is a strong reason not to:

- AQI / DAQI band colours
- guideline warning/red threshold colours
- other semantic health/risk colours that should remain distinct from the blue UI accent system

The goal is to replace the teal UI accent system with the blue hex-map system, not to erase semantic colours.

### 9) Tooltip / point emphasis

For point emphasis / hover treatment:

- keep the hover state visually clear
- make sure it still works against the new blue palette
- maintain good contrast and readability

You may keep the warm hover accent if it still looks good with the new palette.

## Implementation notes

Please review the current chart loading flow carefully before editing.

Key issues to address:

- current intermediate renders appear to use a changing domain start, which makes loading feel visually wrong
- timeline progress and boundary logic currently feel left-anchored in presentation, even though the fetch chunking is reverse-time
- timeline width and chart plot width are not locked together tightly enough

Please refactor as needed, but keep the code readable.

## Constraints

- keep the current functionality working for all supported windows
- do not break caching, incremental refresh, guideline rendering, or tooltip behaviour
- do not introduce layout shift when switching windows
- do not add heavy dependencies
- keep this as a single-file HTML implementation unless there is a strong reason otherwise

## Acceptance criteria

The change is successful if all of the following are true:

1. Selecting a larger window keeps the newest data visible immediately on the right.
2. Older data appears progressively from right to left.
3. The x-axis domain is fixed to the full selected range from the beginning.
4. The chart no longer appears to zoom, reframe, or expand leftward while loading.
5. The timeline width matches the actual chart plot area exactly.
6. The timeline loaded state clearly grows from right to left.
7. The word `Loading` stays centered above the timeline while loading.
8. The chart uses the blue accent system from `uk_aq_hex_map.html`, centred on `#3C78AC`, instead of the old teal accents.
9. Semantic AQI / threshold colours remain intact.
10. The end result feels visually smooth and polished.

## Please provide in your response

1. A short summary of what you changed
2. Any important implementation notes
3. Any tradeoffs or caveats
4. The final edited HTML
