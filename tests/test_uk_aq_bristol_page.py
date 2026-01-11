from pathlib import Path


def test_bristol_chart_elements_present() -> None:
    content = Path("web/uk_aq_bristol.html").read_text(encoding="utf-8")
    markers = [
        'id="line-chart"',
        'id="station-select"',
        'id="window-select"',
        'id="chart-refresh"',
        'id="chart-status"',
        'id="chart-error"',
        'id="chart-tooltip"',
    ]
    for marker in markers:
        assert marker in content
