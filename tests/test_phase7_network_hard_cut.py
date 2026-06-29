from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEX = (ROOT / "hex_map.html").read_text(encoding="utf-8")
SENSORS_MAP = (ROOT / "sensors_map.html").read_text(encoding="utf-8")
SENSORS_CHART = (ROOT / "sensors_chart.html").read_text(encoding="utf-8")


def test_hex_map_uses_network_catalog_for_public_filters() -> None:
    assert "/networks" in HEX
    assert "NETWORK_CATALOG_URL" in HEX
    assert "fetchNetworkCatalog" in HEX
    assert "networkCatalogDefs.map" in HEX
    assert "NETWORK_FILTER_BASE_DEFS" not in HEX


def test_hex_map_filters_exact_catalog_network_codes_without_remaps() -> None:
    assert "resolveNetworkCode(row)" in HEX
    assert "resolveNetworkLabel(row)" in HEX
    assert "function getActiveNetworkCodes" in HEX
    assert "networkCodes.has(code)" in HEX
    assert 'code: "breathe_london"' not in HEX
    assert "GOVUK_REMAP_MATCHERS" not in HEX
    assert "GOVUK_AURN_CODE" not in HEX


def test_hex_map_public_identity_does_not_use_membership_or_connector_fallbacks() -> None:
    forbidden = [
        "resolveNetworkMemberships",
        "station_network_memberships",
        "network_memberships",
        "NETWORK_FILTER_BASE_DEFS",
        "CONNECTOR_DEFS",
        "getConnectorLabelByCode",
    ]
    for marker in forbidden:
        assert marker not in HEX


def test_catalog_network_type_is_retained_for_aggregator_badges() -> None:
    assert "network_type: row?.network_type || null" in HEX
    assert 'network_type === "aggregator"' in HEX


def test_sensors_map_uses_catalog_network_code_shards_not_connector_shards() -> None:
    assert "/networks" in SENSORS_MAP
    assert "fetchNetworkCatalog" in SENSORS_MAP
    assert 'url.searchParams.set("network_code", networkCode)' in SENSORS_MAP
    assert "connector_probe_max" not in SENSORS_MAP
    assert 'url.searchParams.set("connector_id"' not in SENSORS_MAP


def test_public_display_names_use_network_label_only() -> None:
    assert 'return normalizeText(row?.network_label) || "Unknown";' in SENSORS_MAP
    assert 'return String(row.network_label || "").trim() || "Unknown";' in SENSORS_CHART
    for content in (SENSORS_MAP, SENSORS_CHART):
        assert "station_network_memberships" not in content
        assert "network_memberships" not in content
        assert "connector_label || row?.connector_code" not in content
        assert "connector_label || row.connector_code" not in content


def test_no_routine_cache_buster_for_network_catalog() -> None:
    for content in (HEX, SENSORS_MAP):
        assert "cache_buster" not in content
        assert "cachebuster" not in content.lower()
        for line in content.splitlines():
            if "NETWORK_CATALOG_URL" in line or "/networks" in line:
                assert "Date.now()" not in line
                assert "Math.random" not in line


def test_hex_map_user_facing_network_paths_do_not_fall_back_to_connector_labels() -> None:
    forbidden_patterns = [
        "resolvePrimaryNetworkLabel(row) || resolveConnectorLabel",
        "resolvePrimaryNetworkLabel(entry.row) || resolveConnectorLabel",
        "highestNetwork = resolveConnectorLabel",
        "highestNetwork: resolveConnectorLabel",
    ]
    for pattern in forbidden_patterns:
        assert pattern not in HEX
    assert 'resolvePrimaryNetworkLabel(entry.row) || "Unknown network"' in HEX
    assert 'resolvePrimaryNetworkLabel(h.row) || "Unknown network"' in HEX
