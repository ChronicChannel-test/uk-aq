# UK AQ Beta to Live Plan

## Goal

Run the **live UK AQ system** behind a protected beta hostname first, then move it to the public production URL later with as little change as possible.

Example:

- **Beta:** `uk-aq-beta.chronicillnesschannel.co.uk/uk-aq`
- **Live:** `chronicillnesschannel.co.uk/uk-aq`

The whole beta subdomain can sit behind **Cloudflare Zero Trust / Access**. The live site would not use that protection.

---

## Recommended Approach

### 1. Keep beta and live as separate hostnames

Use a dedicated beta hostname for the live system while it is under test.

Recommended:

- `uk-aq-beta.chronicillnesschannel.co.uk`
- app path: `/uk-aq`

Then later switch to:

- `chronicillnesschannel.co.uk`
- app path: `/uk-aq`

Keeping `/uk-aq` the same in both environments reduces launch risk.

### 2. Put the entire beta subdomain behind Cloudflare Access

That gives you:

- private testing
- easy sharing with approved users
- no need to protect the public live hostname later

### 3. Make hostname-dependent settings configurable

Do **not** hardcode beta URLs anywhere. Put them behind environment variables or config.

---

## What Should Be Configurable

Check these before launch:

- site base URL
- API base URL
- asset / static file URL base
- redirects
- login / auth callback URLs
- CORS allowlists
- Content Security Policy allowlists
- sitemap URL
- canonical URLs
- robots rules
- cookie domain / cookie security settings
- any webhook callback URLs
- any generated links in emails or docs

If all of those are config-based, moving from beta to live is easy.

---

## Suggested Environment Model

### Beta environment

- hostname: `uk-aq-beta.chronicillnesschannel.co.uk`
- path: `/uk-aq`
- protected by Cloudflare Access
- uses live repos / live databases only if you are intentionally testing the real live stack

### Live environment

- hostname: `chronicillnesschannel.co.uk`
- path: `/uk-aq`
- no Cloudflare Access in front of the public app
- same app build or same deployment process, but with production hostname config

---

## Rollout Plan

## Phase 1 — Prepare beta hostname

1. Create DNS for `uk-aq-beta.chronicillnesschannel.co.uk`.
2. Point it to the hosting target.
3. Confirm SSL works correctly.
4. Confirm the app can serve correctly on that hostname.

## Phase 2 — Protect beta with Cloudflare Access

1. Create a Cloudflare Access app for the beta hostname.
2. Put the whole hostname behind login.
3. Limit access to only the people who need to test.
4. Confirm that unauthenticated users cannot reach beta.

## Phase 3 — Test the live stack on beta

Use beta to test:

- page routing
- API calls
- database connectivity
- auth or session behaviour if relevant
- cache behaviour
- asset loading
- mobile and desktop layout
- any cron, ingest, or background dependencies that affect the frontend

Also test that deep links work properly, for example:

- `/uk-aq`
- `/uk-aq/map`
- `/uk-aq/stations/...`

## Phase 4 — Prepare live hostname

Before launch:

1. Add production hostname config.
2. Update any allowlists and callback URLs.
3. Check SEO-related settings.
4. Check any cookie settings.
5. Confirm no beta hostname is exposed in visible UI or network config.

## Phase 5 — Go live

1. Point `chronicillnesschannel.co.uk/uk-aq` to the production app.
2. Remove any beta-only settings from the live deployment.
3. Confirm the live hostname works without Cloudflare Access.
4. Smoke test key routes.

## Phase 6 — Post-launch cleanup

After launch you can either:

- keep beta alive for future pre-release testing, or
- redirect beta to live

Keeping beta is usually useful.

---

## Best Practice Notes

### Prefer whole-hostname ownership

This is usually cleaner:

- `uk-aq-beta.chronicillnesschannel.co.uk`

than relying on many mixed apps under the same hostname.

But if you want the app under `/uk-aq`, that is still fine.

### Avoid hardcoded absolute URLs

These are the biggest source of pain when moving from beta to live.

Prefer:

- relative links where possible
- config-driven absolute URLs where required

### Keep beta and live deployment steps identical

The fewer manual differences, the safer the go-live.

---

## Main Risks

### 1. Hardcoded beta hostname leaks into live

Examples:

- JS config still points to beta API
- canonical URLs still point to beta
- images/assets load from beta

### 2. Access or auth rules break launch

If anything depends on the beta hostname being behind Access, make sure production does not accidentally inherit that dependency.

### 3. Cookies scoped wrongly

Cookies set for the beta host will not automatically behave the same on the live host.

### 4. Path handling issues

If the app expects `/` but is actually served under `/uk-aq`, routing and assets can break.

---

## Practical Recommendation

This is the clean setup:

- **Beta:** `uk-aq-beta.chronicillnesschannel.co.uk/uk-aq`
- **Live:** `chronicillnesschannel.co.uk/uk-aq`
- protect the whole beta subdomain with Cloudflare Access
- do not protect the live hostname
- keep all hostname-sensitive values configurable
- reuse the same deployment pattern for both

That gives you a safe private staging route before public launch.

---

## Launch Checklist

- beta hostname resolves correctly
- beta SSL works
- Cloudflare Access works on beta
- app works under `/uk-aq`
- all routes work on beta
- no hardcoded beta URLs remain
- production hostname config ready
- cookies checked
- CORS checked
- CSP checked
- sitemap / canonical / robots checked
- live route smoke-tested after cutover

---

## Bottom Line

Yes — this is a sensible setup.

You can absolutely:

1. run the live UK AQ system first on a protected beta subdomain
2. test it there behind Cloudflare Zero Trust / Access
3. then move it to `chronicillnesschannel.co.uk/uk-aq` later

The key to making the move smooth is keeping hostname-related settings configurable and testing everything under the final `/uk-aq` path from the start.
