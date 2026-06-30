# UK AQ Turnstile “show only if needed” plan

## Purpose

Fix the UK AQ cache-auth Turnstile flow so the widget is not hidden off-screen, does not throw local lifecycle errors, and only becomes visible when Cloudflare requires visitor interaction.

This plan is **not** about the Turnstile site key injection/placeholder issue. It is only about widget rendering, visibility, execution timing, and local/dev performance.

## Background

The hex map now uses the cache-auth path before fetching protected `/api/aq/...` data. When the page does not have a fresh cache session, the client asks Turnstile for a token, posts it to `/api/aq/session/start`, then continues with the real API request.

That is expected to add some delay on the first protected request, especially on `localhost`.

The problem is that the current widget lifecycle can create local browser errors such as:

```text
Uncaught TurnstileError: [Cloudflare Turnstile] Nothing to reset found for provided container.
Failed to execute 'postMessage' on 'DOMWindow': The target origin provided ('https://challenges.cloudflare.com') does not match the recipient window's origin ('http://localhost:8080').
```

The likely cause is not the site key. It is the widget being rendered, reset, or executed while its container is hidden, off-screen, tiny, or otherwise not a normal widget container.

Cloudflare supports two settings that match the desired behaviour:

- `appearance: "interaction-only"` means the widget becomes visible only when visitor interaction is required.
- `execution: "execute"` means the challenge runs only when the code explicitly calls `turnstile.execute(...)`.

The intended UX is:

> Most people never see the widget. If Cloudflare needs interaction, Turnstile shows it. The site should not hide it manually.

## Goals

1. Keep GitHub Pages/public behaviour working.
2. Keep local `serve.py` behaviour working.
3. Keep cache-auth behaviour working.
4. Avoid visible Turnstile UI unless Cloudflare requires interaction.
5. Remove off-screen/opacity-zero/1px widget hiding.
6. Avoid repeated Turnstile resets and duplicate widget rendering.
7. Avoid slowing normal map/chart loads beyond the required first session-start.
8. Keep the existing `fetchCacheApi()` / `getCacheAuthToken()` flow as much as possible.

## Non-goals

This plan does not change:

- Turnstile site key injection.
- Git hook placeholder replacement.
- Cloudflare Worker session validation.
- API response shape.
- Network catalogue logic.
- Map/chart data fetching logic, except where it touches auth gating.

## Implementation plan

### 1. Find the shared Turnstile code

In `hex_map.html`, find the shared cache-auth/Turnstile functions, likely around these names:

```js
ensureTurnstileScript
ensureTurnstileContainer
ensureTurnstileWidget
getTurnstileToken
getCacheAuthToken
fetchCacheApi
```

There may be duplicated controller code in `hex_map.html`. If there are two Turnstile blocks, apply the same fix to both or, ideally, collapse them to one shared implementation.

### 2. Replace the hidden/off-screen container approach

Remove any styling like this from the Turnstile container:

```js
opacity: "0"
left: "-9999px"
top: "-9999px"
width: "1px"
height: "1px"
display: "none"
pointerEvents: "none"
```

Replace it with a normal fixed-position container.

Recommended helper:

```js
function ensureTurnstileContainer() {
  let container = document.getElementById("uk-aq-turnstile-widget-shared");

  if (!container) {
    container = document.createElement("div");
    container.id = "uk-aq-turnstile-widget-shared";
    document.body.appendChild(container);
  }

  Object.assign(container.style, {
    position: "fixed",
    right: "16px",
    bottom: "16px",
    width: "300px",
    minHeight: "65px",
    zIndex: "2147483647",
    background: "transparent",
  });

  return container;
}
```

Do **not** manually hide this container after render. Let Turnstile decide whether to show anything inside it.

### 3. Render Turnstile once, with interaction-only/manual execution

Use explicit rendering and keep the widget ID returned by `turnstile.render(...)`.

Recommended shape:

```js
let turnstileWidgetId = null;
let turnstileTokenPromise = null;
let turnstileTokenResolve = null;
let turnstileTokenReject = null;

async function ensureTurnstileWidget() {
  if (!turnstileSiteKey) {
    throw new Error("Missing Turnstile site key. Add ?turnstile_site_key=... to the URL.");
  }

  await ensureTurnstileScript();

  const container = ensureTurnstileContainer();

  if (turnstileWidgetId !== null) {
    return turnstileWidgetId;
  }

  turnstileWidgetId = window.turnstile.render(container, {
    sitekey: turnstileSiteKey,
    appearance: "interaction-only",
    execution: "execute",
    theme: "auto",
    callback: (token) => {
      const resolve = turnstileTokenResolve;
      clearTurnstilePromiseHandlers();
      if (resolve) resolve(token);
    },
    "error-callback": (errorCode) => {
      const reject = turnstileTokenReject;
      clearTurnstilePromiseHandlers();
      if (reject) reject(new Error(`Turnstile failed: ${errorCode || "unknown error"}`));
    },
    "expired-callback": () => {
      // Token expired before use. The next auth attempt should execute again.
    },
    "timeout-callback": () => {
      const reject = turnstileTokenReject;
      clearTurnstilePromiseHandlers();
      if (reject) reject(new Error("Turnstile challenge timed out."));
    },
  });

  return turnstileWidgetId;
}

function clearTurnstilePromiseHandlers() {
  turnstileTokenPromise = null;
  turnstileTokenResolve = null;
  turnstileTokenReject = null;
}
```

### 4. Execute only when a token is actually needed

Only call Turnstile from `getCacheAuthToken()` when there is no fresh cache auth token/session.

Recommended `getTurnstileToken()` shape:

```js
async function getTurnstileToken() {
  const widgetId = await ensureTurnstileWidget();

  if (turnstileTokenPromise) {
    return turnstileTokenPromise;
  }

  turnstileTokenPromise = new Promise((resolve, reject) => {
    turnstileTokenResolve = resolve;
    turnstileTokenReject = reject;
  });

  try {
    window.turnstile.execute(widgetId);
  } catch (error) {
    clearTurnstilePromiseHandlers();
    throw error;
  }

  return turnstileTokenPromise;
}
```

Important points:

- Do not execute Turnstile on page load.
- Do not execute Turnstile for every chart/map request.
- Do not execute Turnstile when `hasFreshCacheAuthToken()` is already true.
- Reuse the existing in-flight promise so multiple simultaneous API calls do not start multiple challenges.

### 5. Stop resetting by container

The console error:

```text
Nothing to reset found for provided container
```

suggests the code may be calling `turnstile.reset(container)` when Turnstile does not recognise that container as an active widget.

Change any reset calls so they only happen if a real `turnstileWidgetId` exists:

```js
function resetTurnstileWidgetIfReady() {
  if (turnstileWidgetId === null || !window.turnstile) {
    return;
  }

  try {
    window.turnstile.reset(turnstileWidgetId);
  } catch (error) {
    console.warn("Turnstile reset skipped", error);
  }
}
```

Use this sparingly. Prefer simply calling `execute(widgetId)` again on the next auth attempt. Do not reset on every normal successful request.

### 6. Keep the cache auth flow unchanged

`getCacheAuthToken()` should still:

1. Return the existing token if it is fresh.
2. Request a Turnstile token only when needed.
3. POST `/api/aq/session/start`.
4. Store the returned cache auth/session hint.
5. Return the token/session value expected by `fetchCacheApi()`.

Do not change the `/api/aq/session/start` contract in this task.

### 7. Add lightweight debug logs

Keep or add debug logs around the auth path, but make them low-noise:

```js
websiteDebugLog("turnstile-widget-rendered", { widgetId: turnstileWidgetId !== null });
websiteDebugLog("turnstile-execute-started", {});
websiteDebugLog("turnstile-token-received", {});
websiteDebugLog("session-started", {});
```

Do not log the Turnstile token itself.

### 8. Testing checklist

#### Local `serve.py`

Open:

```text
http://localhost:8080/uk-aq/hex_map.html?map=UK
```

Check DevTools Console:

- No `Missing Turnstile site key`.
- No `Nothing to reset found for provided container`.
- No repeated `postMessage` origin errors.
- No repeated `session/start` loop.

Check DevTools Network:

- `/api/aq/session/start` should happen once on first protected request.
- Later `/api/aq/...` calls should not repeatedly restart the session while the cache session is fresh.
- Opening a chart should not trigger repeated Turnstile challenges unless the session expired or was rejected.

Check UI:

- Normally, no Turnstile widget should be visible.
- If Cloudflare requires interaction, the widget should appear at bottom-right and be usable.
- The map should still load after successful session start.
- Chart loading should not be repeatedly aborted by auth restarts.

#### GitHub Pages/public site

Check the deployed GH Pages site:

- Initial map load works.
- Normal visitors do not see Turnstile.
- If interaction is required, the Turnstile widget appears instead of being hidden.
- Protected `/api/aq/...` requests continue to work.
- No local-only assumptions were added.

### 9. Rollback plan

If the change causes issues, rollback only the Turnstile container/render/execute changes and leave the existing cache API/session logic untouched.

A safe temporary fallback is:

- Keep `appearance: "interaction-only"`.
- Keep `execution: "execute"`.
- Revert to previous `getCacheAuthToken()` logic.
- Do not reintroduce off-screen or opacity-zero hiding.

## Codex prompt

```text
You are working in the UK AQ website repo.

Task: Fix the Turnstile widget lifecycle for the hex map cache-auth flow so the widget appears only if Cloudflare requires interaction, without hiding it off-screen or causing local lifecycle errors.

Context:
- This is NOT about the Turnstile site key placeholder/injection issue.
- The page currently uses Turnstile before starting a cache session for protected /api/aq requests.
- Local dev has shown errors such as:
  - [Cloudflare Turnstile] Nothing to reset found for provided container.
  - postMessage target origin challenges.cloudflare.com does not match localhost.
- The likely cause is that the Turnstile widget is rendered/executed/reset while its container is hidden, off-screen, tiny, display:none, or opacity:0.
- Cloudflare supports:
  - appearance: "interaction-only"
  - execution: "execute"
- Desired behaviour: most users never see Turnstile; if Cloudflare requires interaction, Turnstile appears normally and can be used.

Files to inspect:
- hex_map.html
- any shared JS used by hex_map.html for cache-auth, Turnstile, or fetchCacheApi
- do not modify serve.py unless strictly necessary

Implementation requirements:
1. Find the Turnstile/cache-auth functions, likely named:
   - ensureTurnstileScript
   - ensureTurnstileContainer
   - ensureTurnstileWidget
   - getTurnstileToken
   - getCacheAuthToken
   - fetchCacheApi

2. Replace the hidden/off-screen Turnstile container with a normal fixed-position container:
   - position: fixed
   - right: 16px
   - bottom: 16px
   - width: 300px
   - min-height: 65px
   - z-index: 2147483647
   - background: transparent
   Do not set display:none, opacity:0, left:-9999px, top:-9999px, width:1px, height:1px, or pointer-events:none on the widget container.

3. Render the widget once and store the widget ID returned by turnstile.render(...).

4. Render with:
   - sitekey: turnstileSiteKey
   - appearance: "interaction-only"
   - execution: "execute"
   - theme: "auto"
   - callback
   - error-callback
   - expired-callback
   - timeout-callback

5. Only call turnstile.execute(widgetId) when getCacheAuthToken() actually needs a new Turnstile token because there is no fresh cache auth/session token.

6. Preserve single-flight behaviour:
   - If multiple API calls ask for auth at the same time, they should share one in-flight Turnstile token promise/session-start promise.
   - Do not execute multiple Turnstile challenges concurrently.

7. Avoid reset errors:
   - Do not call turnstile.reset(container).
   - If reset is needed, only call turnstile.reset(widgetId) when widgetId is not null and window.turnstile exists.
   - Prefer not resetting after normal successful use.

8. Keep the existing cache session/start contract unchanged:
   - Turnstile token is still posted to /api/aq/session/start.
   - Do not change Worker/API endpoints.
   - Do not change data loading logic except where auth gating requires it.

9. Add small debug logs if the project already has websiteDebugLog:
   - turnstile-widget-rendered
   - turnstile-execute-started
   - turnstile-token-received
   - session-started
   Do not log the actual Turnstile token.

10. If hex_map.html contains duplicated Turnstile/cache-auth blocks, update all copies or consolidate safely without changing behaviour.

Acceptance tests:
- Local URL http://localhost:8080/uk-aq/hex_map.html?map=UK loads the map.
- The console no longer shows:
  - Nothing to reset found for provided container
  - repeated Turnstile postMessage origin errors
- Network tab shows /api/aq/session/start only when there is no fresh cache session.
- Normal users do not see the Turnstile widget.
- If Cloudflare requires interaction, the widget appears bottom-right and is usable.
- GH Pages deployed site still works.
- Protected /api/aq requests still work.
- No Turnstile token is logged.
```

## References

Cloudflare Turnstile widget configuration docs:
https://developers.cloudflare.com/turnstile/get-started/client-side-rendering/widget-configurations/
