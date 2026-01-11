# uk-aq

Static web UI for CIC UK Air Quality Networks.

## Structure
- `web/` static site files (open `web/uk_aq_hex_map.html` or `web/uk_aq_bristol.html`).
- `web/data/` reference datasets and hex grids.
- `data/WHO-guidelines/` reference copy of the WHO GAQG 2021 CSV loaded into Supabase.

## Supabase config (optional)
`web/uk_aq_bristol.html` can embed the Supabase project ref and anon key for the live Edge Function URL.

Create a `.env` file in the repo root or set env vars:
```
SUPABASE_PROJECT_REF=your_project_ref
SUPABASE_ANON_JWT=your_anon_key
```

Then run:
```
node scripts/uk_aq_inject_project_ref.mjs
```

## Hosting
Set your publish directory to `web/` when deploying.
