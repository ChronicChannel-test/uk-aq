# AGENTS

## Main Repo
- `CIC-test-uk-aq-ops` is the main repo for this project and the default starting point for cross-repo work.
- Ops repo path: `/Users/mikehinford/Dropbox/Projects/CIC Website/CIC Air Quality Networks/CIC-test-uk-aq-Operations/CIC-test-uk-aq-ops`.
- Webpage repo path: `/Users/mikehinford/Dropbox/Projects/CIC Website/CIC Air Quality Networks/CIC-UK-AQ Webpage/CIC-test-uk-aq-webpage`.

## Codex operating mode
Default mode is code-only implementation.
Codex should:
- make focused code, schema, documentation, and test edits requested by the task;
- run only fast, local, non-destructive checks needed to verify the edit;
- provide a clear manual validation and deployment plan;
- include exact SQL, gcloud, wrangler, GitHub Actions, and Supabase commands for the user to run manually.
Codex must not, unless explicitly asked:
- run SQL against live/test Supabase databases;
- apply migration files;
- deploy Cloud Run services, Workers, or GitHub Actions workflows;
- run backfills, reconciliations, bulk jobs, or long-running data jobs;
- run broad external API fetches;
- repeatedly inspect cloud logs;
- make operational changes in GCP, Supabase, Cloudflare, R2, Dropbox, or GitHub settings.
When database or deployment work is needed, Codex should stop after producing:
1. files changed,
2. tests run,
3. exact manual commands,
4. expected outputs,
5. rollback notes,
6. post-deploy validation checklist.

## Permission levels
Unless the prompt says otherwise, use Level 1.
### Level 1 — Code only
Edit files and run small local/static tests. Do not touch external services or databases.
### Level 2 — Local validation
Level 1 plus local-only scripts/tests that do not call Supabase, GCP, Cloudflare, R2, Dropbox, or external APIs.
### Level 3 — Assisted operations
Prepare SQL, deploy commands, and validation commands, but do not run them.
### Level 4 — Execute operations
Only when explicitly requested in the prompt. May run database, deployment, or cloud commands.

## Planning Requests
When proposing plans, offer more than one option when possible, list pros/cons for each, and recommend which to pick with a brief rationale.

## Implementation Reporting
- When changing code, schema, workflows, or config, always include clear implementation steps in the response.
- Implementation steps must state what changed, which files were changed, and any required apply/deploy/run commands.
- If no code changes were made, state that explicitly.

## Notes
- PM2.5 outlier handling: edge functions already drop any station whose latest PM2.5 reading is above 500 µg/m³. The hex map keeps a frontend safety net at the same threshold (`MAX_VALID_PM25_VALUE = 500`) to guard against regressions or stale caches. If this duplicate guard ever causes issues, it can be removed safely once backend filtering is trusted.

## Archive
Files in `archive/` can be referenced for context but must never be modified once created. Adding new files/directories under `archive/` is allowed.

## External Archive Policy
For `/Users/mikehinford/Dropbox/Projects/CIC Website/CIC Air Quality Networks/CIC-Test-UK-AQ-Schema/CIC-test-uk-aq-schema`, edits are allowed for any file except under `archive/` directories. Archive files are read-only; new files may be added under `archive/` but must never be modified once created.

## Documentation Hygiene
When adding or updating agent/project notes, also update relevant files under `system_docs` if they need to stay in sync.

## Sidebar Hook Workflow
- Sidebar logic should be edited once only in a single repo/file per task.
- A git hook in `.git/hooks` propagates sidebar logic changes, so do not duplicate the same sidebar logic edits manually across repos.

## R2/Cloudflare Cache Cost Policy
- For AQI history served via R2 + Cloudflare, assume cost is primarily driven by R2 operation counts (especially Class B reads) and Worker request volume, not R2 bandwidth egress.
- Prefer stable request URLs/params for normal traffic so Cloudflare cache can return warm-cache hits.
- Use cache-buster/version params only for diagnostics, forced-refresh actions, or explicit bypass-cache testing.
- When evaluating performance/cost changes, check cache-hit behavior (`CF-Cache-Status`) and distinguish cache-hit traffic from origin-fetch traffic.

## Search Tool Preference
- Prefer `grep` for text search and file discovery; do not use `rg` unless explicitly requested.
