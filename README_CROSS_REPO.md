# Cross-repo map: CIC-test-uk-aq (web UI)

## Main repo
- `CIC-test-uk-aq-ingest` is the main repo for this project and the default starting point for cross-repo tasks.

## Purpose
This repo is a static HTML/CSS/JS front-end for the UK Air Quality Networks project. It renders latest station readings, timeseries charts, and hex-map summaries by calling Supabase Edge Functions and using local data files for geometry and styling.

It does not ingest data itself; it relies on the ingest and population repos (Edge Functions) and the schema repo (tables/views) for all live data.

## Repo layout
- `index.html`: Main dashboard page (latest station table + trend chart).
- `uk_aq_stations_chart.html`: Station-search dashboard page (latest station table + trend chart).
- `uk_aq_hex_map.html`: Primary hex-map UI.
- `hex_map_test*.html`: Hex-map test variants.
- `scripts/`: Build-time helper ([scripts/uk_aq_inject_project_ref.mjs](scripts/uk_aq_inject_project_ref.mjs)).
- `data/`: Local datasets and hex grids used by the UI.
- `system_docs/`: UI and schema notes ([system_docs/uk-aq-hex-map-ui.md](system_docs/uk-aq-hex-map-ui.md)).
- `supabase/`: SQL helpers used for checks ([supabase/data_check.sql](supabase/data_check.sql)).
- `fonts/`, `favicon.ico`: Static assets.
- `archive/`: Historical assets (do not edit).

## How this repo connects to the other repos
- **Schema repo**: `CIC-test-uk-aq-schema` defines the tables/views used by the Edge Functions.
- **AQ ingest repo**: `CIC-test-uk-aq-ingest` owns the main air-quality ingest and most Edge Functions called by this UI.
- **Population ingest repo**: `CIC-Test-uk-population-ingest` provides the `uk_aq_population` Edge Function used by the hex map.
- **History repo**: `CIC-test-uk-aq-history` houses historical/backfill tooling against the same schemas.

Data flow across repos:
- `CIC-test-uk-aq-schema` defines tables/views/RPC/policies.
- `CIC-test-uk-aq-ingest`, `CIC-test-uk-aq-history`, and `CIC-Test-uk-population-ingest` write data into those schemas.
- This repo reads data and calls Edge Functions.
- Edge Functions (if present) live under `/supabase` in the ingest repo; population Edge Functions live under `/supabase` in the population ingest repo.

## Supabase touchpoints
### Reads
- **PostgREST**: none found (no direct `/rest/v1` usage in this repo).
- **RPC**: none found.
- **Edge Functions**:
  - [index.html](index.html) and [uk_aq_stations_chart.html](uk_aq_stations_chart.html): `uk_aq_stations_chart`, `uk_aq_timeseries`.
  - [uk_aq_hex_map.html](uk_aq_hex_map.html): `uk_aq_latest`, `uk_aq_pcon_hex`, `uk_aq_la_hex`, `uk_aq_population`.
  - [hex_map_test.html](hex_map_test.html), [hex_map_test1.html](hex_map_test1.html), [hex_map_test2.html](hex_map_test2.html), [hex_map_test3.html](hex_map_test3.html), [hex_map_test_met1.html](hex_map_test_met1.html): `uk_aq_latest`, `uk_aq_pcon_hex`, `uk_aq_population` (varies per file).
- **Storage**: none found.
- **Auth**: anon key is injected and sent in `Authorization`/`apikey` headers in the HTML files above.
- **Realtime**: none found.

### Writes
- No direct writes from this repo (static front-end only).

### Edge Functions (if applicable)
- **Location**:
  - AQ functions: [../../CIC-test-uk-aq-ingest/supabase/functions/](../../CIC-test-uk-aq-ingest/supabase/functions/)
  - Population function: [../../CIC UK Population Ingest/CIC-Test-uk-population-ingest/supabase/functions/uk_aq_population](../../CIC%20UK%20Population%20Ingest/CIC-Test-uk-population-ingest/supabase/functions/uk_aq_population)
- **Invocation pattern**: `https://<project_ref>.supabase.co/functions/v1/<function_name>`
- **Public vs user-specific responses**: requests use an anon key; the UI does not attach user-specific auth tokens in code.

## Running and configuration (NO SECRETS)
- **Env vars (names only)**:
  - `SUPABASE_PROJECT_REF`
  - `SB_ANON_JWT`
  - `SUPABASE_ANON_JWT`
  - `SUPABASE_PUBLISHABLE_DEFAULT_KEY`
  - `SUPABASE_ANON_KEY`
- **Env files**: `.env` exists at repo root (no `.env.example` found).
- **Commands (documented)**:
  - `node scripts/uk_aq_inject_project_ref.mjs`
  - `node scripts/uk_aq_inject_project_ref.mjs uk_aq_hex_map.html`
- **Hosting**: serve the static files from this repo root directory.
  - README notes a publish directory of `web/` for hosting (confirm).

## Data model pointers
- Core AQ tables/views (timeseries, observations, stations, guidelines, pcon/la latest views):
  - [../../CIC-test-uk-aq-schema/uk-aq-schema/schemas/uk_aq_core_schema.sql](../../CIC-test-uk-aq-schema/uk-aq-schema/schemas/uk_aq_core_schema.sql)
- Public read-only views (if used by Edge Functions):
  - [../../CIC-test-uk-aq-schema/uk-aq-schema/schemas/uk_aq_public_views.sql](../../CIC-test-uk-aq-schema/uk-aq-schema/schemas/uk_aq_public_views.sql)
- Population views (`uk_population_observations`):
  - [../../CIC-test-uk-aq-schema/uk-aq-schema/schemas/uk_aq_pop_schema.sql](../../CIC-test-uk-aq-schema/uk-aq-schema/schemas/uk_aq_pop_schema.sql)

## Egress-relevant notes (FACTUAL, no solutions)
- [index.html](index.html) and [uk_aq_stations_chart.html](uk_aq_stations_chart.html) poll live data every 5 minutes via Edge Functions.
- [uk_aq_hex_map.html](uk_aq_hex_map.html) polls live data every 60 seconds and sets `limit=10000` on `uk_aq_latest` requests.
- [hex_map_test.html](hex_map_test.html), [hex_map_test1.html](hex_map_test1.html), [hex_map_test2.html](hex_map_test2.html), [hex_map_test3.html](hex_map_test3.html), and [hex_map_test_met1.html](hex_map_test_met1.html) poll live data every 10 minutes.
- The pages above use repeated fetches for Edge Functions on load and on refresh actions.

## Archive policy (REQUIRED)
“Archive policy:
- /archive directories may be searched and used as reference.
- Do not modify or delete any existing files in /archive.
- You may add new files to /archive, but never change existing archived content.”

## Permissions (REQUIRED)
- The agent may edit any files without asking for permission, except files under any `/archive` directory.

## WORKING STYLE (IMPORTANT)

REQUIRED OUTPUT FORMAT

Summary (2–5 bullets)
Files changed (paths)
Implementation details (short, specific)
Supabase steps (instructions only,)
Verification checklist (clear pass/fail)
