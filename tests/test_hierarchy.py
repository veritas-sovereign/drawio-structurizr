"""Phase C: shapes must nest the way Structurizr allows; unknown shape types are skipped."""

import json
from pathlib import Path

from drawio_structurizr import parser
from drawio_structurizr.main import main

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "hierarchy"


def problems(name):
    return parser.load_and_check([str(FIXTURES / f"{name}.drawio")])[2]


def codes(name):
    return [p.code for p in problems(name)]


def test_container_outside_system():
    errors = [p for p in problems("container-outside-system") if p.code == "C4-HIER-001"]
    assert len(errors) == 1
    assert errors[0].severity == "error"
    assert 'Container "API" is outside any software system' in errors[0].message


def test_component_outside_container():
    errors = [p for p in problems("component-outside-container") if p.code == "C4-HIER-002"]
    assert len(errors) == 1
    assert 'Component "Order Service" is inside SystemScopeBoundary "Shop"' in errors[0].message


def test_system_inside_another_element():
    errors = [p for p in problems("nested-system") if p.code == "C4-HIER-003"]
    assert len(errors) == 1
    assert 'Software System "Payments" is inside SystemScopeBoundary "Shop"' in errors[0].message


def test_errors_stop_output_without_strict(tmp_path):
    for name in ("container-outside-system", "component-outside-container", "nested-system"):
        output = tmp_path / f"{name}.dsl"
        assert main([str(FIXTURES / f"{name}.drawio"), "-o", str(output)]) == 1
        assert not output.exists()


def test_unknown_type_is_skipped_with_a_warning(tmp_path):
    assert codes("unknown-type") == ["C4-TYPE-001"]
    output = tmp_path / "out.dsl"
    assert main([str(FIXTURES / "unknown-type.drawio"), "-o", str(output)]) == 0
    assert "Orders queue" not in output.read_text()


def test_report_carries_code_and_severity(tmp_path):
    report = tmp_path / "report.json"
    main([str(FIXTURES / "container-outside-system.drawio"), "--check", "--report", str(report)])
    data = json.loads(report.read_text())
    assert data["errorCount"] == 1
    assert {"code": "C4-HIER-001", "severity": "error"}.items() <= data["problems"][0].items()
