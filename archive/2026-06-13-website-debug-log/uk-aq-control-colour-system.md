# UK-AQ Control Colour System

## Purpose

This defines a reusable control-state system for UK-AQ controls so users can quickly distinguish:

- active/selected choice
- selectable/inactive choices
- disabled/unavailable choices
- primary action buttons

Use this across `hex_map.html` and future UK-AQ pages for consistent interaction cues.

## Core Accent Colours

- Accent: `--accent: #3C78AC`
- Deep accent: `--accent-deep: #285A84`

## Shared Token Values

Current `:root` values used by the top map toolbar:

- `--ukaq-control-selected-bg: color-mix(in oklab, #3C78AC 12%, #FFFFFF)`
- `--ukaq-control-selected-text: #285A84`
- `--ukaq-control-selected-border: rgba(60, 120, 172, 0.45)`
- `--ukaq-control-selectable-bg: #FBFAF7` (from `--surface-2`)
- `--ukaq-control-selectable-text: #1B2A38` (from `--ink-1`)
- `--ukaq-control-selectable-border: #E4E6EA` (from `--line`)
- `--ukaq-control-selectable-hover-bg: #DDEFF7`
- `--ukaq-control-hover-shadow: 0 8px 18px rgba(60, 120, 172, 0.22)`
- `--ukaq-control-hover-border: rgba(60, 120, 172, 0.35)`
- `--ukaq-control-disabled-bg: #F1F3F5`
- `--ukaq-control-disabled-text: #9AA7B3` (from `--ink-4`)
- `--ukaq-control-disabled-border: rgba(20, 34, 37, 0.12)`
- `--ukaq-action-bg: #3C78AC`
- `--ukaq-action-text: #FFFFFF`

## State Meanings

### Selected / Active

- Blue-tinted background (accent tint)
- Blue-teal text
- Blue-teal border
- No hover lift/halo where re-click does not change state

### Selectable / Inactive

- Clay background (`#FBFAF7`)
- Black/near-black text
- Grey border by default for bordered controls
- Lift + blue halo/shadow on hover
- No colour-fill change on hover for View/Pollutant controls

### Disabled / Unavailable

- Faded grey icon/text
- No lift/halo
- Disabled cursor behaviour

### Primary Action

- Solid blue-teal background (`#3C78AC`)
- White text (`#FFFFFF`)
- Lift + blue halo/shadow on hover

## Control-Specific Rules

### View (segmented)

- Outer segmented container: clay background + grey border
- Active View option: blue-tinted selected fill + blue selected border
- Inactive View option: clay fill + no individual border

### Pollutant (pills)

- Active pill: blue-tinted selected fill + blue selected border
- Inactive pill: clay fill + grey border

### Window (stepper)

- Center value: compact selected capsule
- Arrows: standalone triangles (not boxed pill buttons)
- Hover/Focus: triangle itself lifts with blue halo/shadow
- Disabled arrows: faded grey triangle, no lift

### Network (dropdown multi-select)

- Trigger (closed): selectable style (`--ukaq-control-selectable-bg`, `--ukaq-control-selectable-text`, `--ukaq-control-selectable-border`)
- Trigger (open): selected style (`--ukaq-control-selected-bg`, `--ukaq-control-selected-text`, `--ukaq-control-selected-border`)
- Dropdown panel: white surface (`#FFFFFF`) with standard line border (`#E4E6EA`)
- Header count uses tabular numerals and accent-deep text (`#285A84`)
- Bulk actions:
  - `Select all`: filled square icon with white tick on accent (`#3C78AC`)
  - `Clear all`: empty outlined square icon in accent (`#3C78AC`)
  - Enabled actions: selectable style + lift/halo hover
  - Disabled actions: disabled style (`#F1F3F5` / `#9AA7B3`) with no lift
- Network rows:
  - Clickable full row with checkbox + name + right-aligned active count
  - Calm pale hover/focus background only (no lift)
  - Unselected rows slightly muted but fully legible

## Shape Guidance

Use shapes by control type:

- Segmented: mode/view choices
- Pills: pollutant/filter choices
- Dropdowns: compact multi-choice selectors (for example future Network picker)
- Steppers: ordered values such as Window

## Hover Guidance

- Selectable controls: lift + blue halo/shadow
- Selected controls: no lift when clicking does nothing
- Disabled controls: never lift
- Table text links/buttons: no lift motion

## Sensor-List Guidance

- Clickable sensor names may shift to blue-teal on hover/focus
- Chart icon may appear on hover/focus
- Sensor rows and sensor names should not lift
