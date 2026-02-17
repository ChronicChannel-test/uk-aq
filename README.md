# uk-aq

Static web UI for CIC UK Air Quality Networks.

## Structure
- `uk_aq_hex_map.html` main hex map UI.
- `uk_aq_stations_chart.html` station-search chart page.
- `data/` reference datasets and hex grids.
- `data/WHO-guidelines/` reference copy of the WHO GAQG 2021 CSV loaded into Supabase.

## Supabase config (optional)
The HTML pages can embed the Supabase project ref and publishable key for live Edge Function URLs.

Create a `.env` file in the repo root or set env vars:
```
SUPABASE_PROJECT_REF=your_project_ref
SB_PUBLISHABLE_DEFAULT_KEY=your_publishable_key
```

Then run:
```
node scripts/uk_aq_inject_project_ref.mjs
```

You can also target specific files:
```
node scripts/uk_aq_inject_project_ref.mjs uk_aq_hex_map.html
```

### GitHub Pages
In your GH Pages workflow, set repo secrets `SUPABASE_PROJECT_REF` and `SB_PUBLISHABLE_DEFAULT_KEY`, then run:
```
node scripts/uk_aq_inject_project_ref.mjs
```

## Hosting
Set your publish directory to `web/` when deploying.
