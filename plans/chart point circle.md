You are working in the UK AQ repo on `hex_map.html`.
Please make a very small chart styling change only. Do not refactor unrelated code, do not change data files, and do not change anything outside `hex_map.html`.
## Goal
Change the active/hovered chart point marker from yellow fill to a neutral cream fill with a blue border.
This is the circle that appears when hovering over a chart line/point to show which reading the tooltip is for.
## Required change
Find the CSS for the active chart point marker, likely:
```css
.chart-dot {
  fill: var(--sun);
  stroke: var(--accent-deep);
  stroke-width: 1.5px;
}

Change it to use:

.chart-dot {
  fill: var(--surface-2);
  stroke: var(--accent);
  stroke-width: 2px;
}

or equivalent using the existing UK AQ design variables.

Constraints

* Do not use yellow, orange, green, red, or purple for this marker.
* Do not change pollutant/AQI colour scales.
* Do not change line colours.
* Do not change tooltip styling.
* Do not change chart symbols in the sensor list or sensor chips.
* Keep the change CSS-only unless absolutely necessary.

Acceptance checks

Please verify in chart mode:

1. Hover over a chart line.
2. Confirm the active point marker is cream-filled.
3. Confirm it has a blue border.
4. Confirm the marker no longer uses yellow.
5. Confirm pollutant reading colours and AQI colours are unchanged.

Please summarise the exact CSS changed.