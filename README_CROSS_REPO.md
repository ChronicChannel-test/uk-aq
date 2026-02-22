# Cross-repo map: CIC-test-uk-aq (web UI)

## Main repo
- `CIC-test-uk-aq` is the main repo for this project and the default starting point for cross-repo tasks.
- Filesystem location: `/Users/mikehinford/Library/CloudStorage/Dropbox/Projects/CIC Website/CIC Air Quality Networks/CIC UK-AQ Webpage/CIC-test-uk-aq`.

## Purpose
This repo is a static HTML/CSS/JS front-end for the UK Air Quality Networks project. It renders latest station readings, timeseries charts, and hex-map summaries by calling the Cloudflare cache proxy (`/api/aq/*`) for AQ reads and using local data files for geometry and styling.

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
  - [index.html](index.html) and [uk_aq_stations_chart.html](uk_aq_stations_chart.html): `stations-chart`, `timeseries` via cache proxy routes under `/api/aq/*`.
  - [uk_aq_hex_map.html](uk_aq_hex_map.html): `latest`, `pcon-hex`, `la-hex` via cache proxy routes under `/api/aq/*`; `uk_aq_population` remains a direct Supabase edge function route when enabled.
  - [hex_map_test.html](hex_map_test.html), [hex_map_test1.html](hex_map_test1.html), [hex_map_test2.html](hex_map_test2.html), [hex_map_test3.html](hex_map_test3.html), [hex_map_test_met1.html](hex_map_test_met1.html): `uk_aq_latest`, `uk_aq_pcon_hex`, `uk_aq_population` (varies per file).
- **Storage**: none found.
- **Auth**: cached AQ read routes (`/api/aq/*`) use a Cloudflare Worker session cookie (`uk_aq_edge_session`, HttpOnly) initialized via `POST /api/aq/session/start`; session start sends `X-UK-AQ-Session-Init: 1` plus `CF-Turnstile-Token` from Turnstile solve, and browser fetches use `credentials: include` without `Authorization`/`apikey` headers for AQ reads. Direct Supabase calls (for example population/test pages) still use the publishable key flow where configured.
- **Realtime**: none found.

### Writes
- No direct writes from this repo (static front-end only).

### Edge Functions (if applicable)
- **Location**:
  - AQ functions: [../../CIC-test-uk-aq-ingest/supabase/functions/](../../CIC-test-uk-aq-ingest/supabase/functions/)
  - Population function: [../../CIC UK Population Ingest/CIC-Test-uk-population-ingest/supabase/functions/uk_aq_population](../../CIC%20UK%20Population%20Ingest/CIC-Test-uk-population-ingest/supabase/functions/uk_aq_population)
- **Invocation pattern**:
  - AQ reads (main pages): `https://uk-aq-cache-cic-test.chronicillnesschannel.co.uk/api/aq/<route>`
  - Direct Supabase edge calls (where still used): `https://<project_ref>.supabase.co/functions/v1/<function_name>`
- **Public vs user-specific responses**: AQ cache routes use worker-managed session cookies (not user account JWTs). The UI does not attach user-specific auth tokens in code.

## Running and configuration (NO SECRETS)
- **Env vars (names only)**:
  - `SUPABASE_PROJECT_REF`
  - `SB_PUBLISHABLE_DEFAULT_KEY`
- **Env files**: `.env` exists at repo root (no `.env.example` found).
- **Commands (documented)**:
  - `node scripts/uk_aq_inject_project_ref.mjs`
  - `node scripts/uk_aq_inject_project_ref.mjs uk_aq_hex_map.html`
- **Hosting**: serve the static files from this repo root directory.
  - README notes a publish directory of `web/` for hosting (confirm).

## Data model pointers
- Core AQ tables/views (timeseries, observations, stations, guidelines, pcon/la latest views):
  - [../../CIC-Test-UK-AQ-Schema/CIC-test-uk-aq-schema/schemas/main_db/uk_aq_core_schema.sql](../../CIC-Test-UK-AQ-Schema/CIC-test-uk-aq-schema/schemas/main_db/uk_aq_core_schema.sql)
- Public read-only views (if used by Edge Functions):
  - [../../CIC-Test-UK-AQ-Schema/CIC-test-uk-aq-schema/schemas/main_db/uk_aq_public_views.sql](../../CIC-Test-UK-AQ-Schema/CIC-test-uk-aq-schema/schemas/main_db/uk_aq_public_views.sql)
- Population views (`uk_population_observations`):
  - [../../CIC-Test-UK-AQ-Schema/CIC-test-uk-aq-schema/schemas/main_db/uk_aq_pop_schema.sql](../../CIC-Test-UK-AQ-Schema/CIC-test-uk-aq-schema/schemas/main_db/uk_aq_pop_schema.sql)

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
