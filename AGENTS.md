# AGENTS

## Main Repo
- `CIC-test-uk-aq-ingest` is the main repo for this project and the default starting point for cross-repo work.

## Planning Requests
When proposing plans, offer more than one option when possible, list pros/cons for each, and recommend which to pick with a brief rationale.

## Notes
- PM2.5 outlier handling: edge functions already drop any station whose latest PM2.5 reading is above 500 µg/m³. The hex map keeps a frontend safety net at the same threshold (`MAX_VALID_PM25_VALUE = 500`) to guard against regressions or stale caches. If this duplicate guard ever causes issues, it can be removed safely once backend filtering is trusted.

## Archive
Files in `archive/` can be referenced for context but must never be modified once created. Adding new files/directories under `archive/` is allowed.

## External Archive Policy
For `/Users/mikehinford/Library/CloudStorage/Dropbox/Projects/CIC Website/CIC Air Quality Networks/CIC-test-uk-aq-schema/uk-aq-schema`, edits are allowed for any file except under `archive/` directories. Archive files are read-only; new files may be added under `archive/` but must never be modified once created.

## Documentation Hygiene
When adding or updating agent/project notes, also update relevant files under `system_docs` if they need to stay in sync.
