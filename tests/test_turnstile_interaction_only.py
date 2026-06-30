from pathlib import Path


HTML = (Path(__file__).resolve().parents[1] / "hex_map.html").read_text(
    encoding="utf-8"
)
START = HTML.index("if (!window.ukAqSharedAuth)")
END = HTML.index("const ACCESS_LOGIN_REDIRECT_KEY", START)
AUTH = HTML[START:END]


def test_turnstile_container_is_visible_when_interaction_is_required() -> None:
    for marker in (
        'right: "16px"',
        'bottom: "16px"',
        'width: "300px"',
        'minHeight: "65px"',
        'zIndex: "2147483647"',
    ):
        assert marker in AUTH

    for forbidden in (
        'left: "-10000px"',
        'top: "-10000px"',
        'width: "1px"',
        'height: "1px"',
        'opacity: "0"',
        'pointerEvents: "none"',
        'display: "none"',
        "uk-aq-turnstile-hidden",
    ):
        assert forbidden not in AUTH


def test_turnstile_renders_once_with_manual_interaction_only_execution() -> None:
    assert 'appearance: "interaction-only"' in AUTH
    assert 'execution: "execute"' in AUTH
    assert 'theme: "auto"' in AUTH
    assert "if (turnstileWidgetId !== null) return turnstileWidgetId;" in AUTH
    assert "turnstileApi.execute(widgetId);" in AUTH
    assert "turnstileApi.remove" not in AUTH
    assert "turnstileApi.reset" not in AUTH


def test_turnstile_and_session_requests_remain_single_flight() -> None:
    assert "if (!turnstileTokenInflight)" in AUTH
    assert "if (!cacheAuthInflight)" in AUTH
    assert "if (!forceRefresh && hasFreshCacheAuthToken()) return cacheAuthToken;" in AUTH
    assert '"CF-Turnstile-Token": turnstileToken' in AUTH


def test_turnstile_debug_logs_never_include_token_values() -> None:
    for event in (
        "turnstile-widget-rendered",
        "turnstile-execute-started",
        "turnstile-token-received",
        "session-started",
    ):
        assert event in AUTH
    assert 'turnstileDebugLog("turnstile-token-received", token)' not in AUTH
