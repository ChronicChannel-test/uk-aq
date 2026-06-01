You are working in the uk-aq repo.

Task: amend the Hex Map toolbar view buttons in hex_map.html so the two View buttons match the supplied new reference image.

Reference image:
- Use the supplied image in this task thread (the one showing:
  - “United Kingdom” + “Constituencies”
  - “Countries & Regions” + “Local Authorities”
  - taller row and larger two-line segmented buttons)

Before changing anything:
1. Create an archive folder under the repo if it does not already exist:
   archive/2026-06-01/
2. Copy the existing hex_map.html into that folder before editing it.
3. Do not change any files outside hex_map.html, except for creating/copying into the archive folder.

Context:
The current toolbar has a View label followed by a segmented control with two buttons:
- #toolbar-tab-uk currently says “United Kingdom”
- #toolbar-tab-cr currently says “Countries & Regions”

The current markup is in the toolbar inside #main-toolbar. The active tab state is controlled by JS using the existing button IDs and the active class, so do not change the IDs, button types, or JS behaviour.

Current relevant markup resembles:
<span class="field-label chart-mode-view-control">View</span>
<div class="segmented chart-mode-view-control">
  <button type="button" id="toolbar-tab-uk" class="active">United Kingdom</button>
  <button type="button" id="toolbar-tab-cr">Countries &amp; Regions</button>
</div>

The current CSS for .toolbar, .segmented, .segmented button, and .segmented button.active controls the button styling.

Required change:
Update the segmented View buttons so they become taller and have two centred text lines:

Button 1:
Line 1: United Kingdom
Line 2: Constituencies

Button 2:
Line 1: Countries & Regions
Line 2: Local Authorities

Design requirements:
- The whole toolbar/buttons row must become taller enough to comfortably fit the two-line buttons.
- Keep all toolbar contents vertically centred within the taller row.
- The View label must remain vertically centred alongside the taller buttons.
- The two View buttons must be taller than they are now.
- The first line should keep the existing visual style of the current button text.
- The second line must use the same font family and colour as the first line, but be smaller.
- The text in each button must be horizontally centred.
- The two text lines must be vertically centred within each button.
- Preserve selected/active styling: active button keeps pale blue background, blue text, blue border, and heavier weight.
- Preserve inactive styling and hover/focus behaviour.
- Do not alter chart-mode hiding behaviour for .chart-mode-view-control.
- Do not break tab switching behaviour.
- Do not change pollutant/window/network/status/refresh controls other than allowing row height to accommodate taller View buttons.
- Keep layout responsive. On narrower widths the toolbar may wrap as it already does, but button text should remain readable.

Implementation guidance:
- Change button contents to structured spans, for example:
  <span class="view-button-main">United Kingdom</span>
  <span class="view-button-sub">Constituencies</span>
- Add small, scoped CSS classes for two-line View buttons.
- Do not apply two-line styles globally to all toolbar buttons.
- Add a specific class to the View segmented control, for example:
  <div class="segmented segmented--view chart-mode-view-control">
- Scope new styles under .segmented--view.
- Use flex/inline-flex with column direction and centered alignment.
- Increase vertical padding/min-height only for View buttons.
- Increase .map-controls-row min-height and/or .toolbar min-height only as needed.
- Control line-height so the two text lines look compact and centred.
- Ensure HTML uses &amp; for “Countries & Regions”.

Acceptance checks:
1. Open hex_map.html in a browser.
2. In default UK view, “United Kingdom / Constituencies” is active and visibly selected.
3. “Countries & Regions / Local Authorities” is inactive.
4. Click Countries & Regions:
   - switches to CR view exactly as before
   - active styling moves to CR button
   - region dropdown still appears
5. Click United Kingdom:
   - switches back exactly as before
   - region dropdown hides as before
6. Check chart mode:
   - View controls still hide as before because they retain chart-mode-view-control
7. Check toolbar:
   - Pollutant, Window, Chart range, Live status, Refresh, and Networks controls still behave and align correctly
8. Check mobile/narrow width:
   - toolbar can wrap without clipping two-line button text

Return a concise summary of what changed and confirm archive path used.
