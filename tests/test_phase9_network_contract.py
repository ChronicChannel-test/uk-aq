from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HEX = (ROOT / "hex_map.html").read_text(encoding="utf-8")
DOC = (ROOT / "system_docs/hex-map-data-formats.md").read_text(encoding="utf-8")


def test_both_hex_controllers_use_exact_catalogue_identity() -> None:
    assert HEX.count("fetchNetworkCatalog") >= 2
    assert HEX.count("function getCatalogNetworkByCode(code)") == 2
    assert HEX.count("networkCodes.has(code)") == 2
    assert HEX.count("row?.network_label || row?.station?.network_label") >= 2


def test_old_network_remapping_and_public_fallbacks_are_absent() -> None:
    for marker in (
        'code: "breathe_london"',
        "GOVUK_REMAP_MATCHERS",
        "NETWORK_FILTER_BASE_DEFS",
        "CONNECTOR_DEFS",
        "connector_label || row?.connector_code",
    ):
        assert marker not in HEX


def test_data_format_docs_fix_catalogue_and_polling_contract() -> None:
    for marker in (
        "/api/aq/networks",
        "exact `network_code`",
        "`network_label`",
        'network_type = "aggregator"',
        "OpenAQ",
        "every minute",
        "GOV.UK AURN",
        "`breathelondon` remains `breathelondon`",
    ):
        assert marker in DOC
