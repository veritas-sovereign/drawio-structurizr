"""End-to-end tests against the sample diagrams in examples/."""

from pathlib import Path

import pytest

from drawio_structurizr import parser
from drawio_structurizr.main import main

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def convert(name, tmp_path):
    output = tmp_path / f"{name}.dsl"
    assert main([str(EXAMPLES / f"{name}.drawio"), "-o", str(output)]) == 0
    return output.read_text()


def run_checks(name):
    components, relations, broken = parser.load_from_xml(str(EXAMPLES / f"{name}.drawio"), False)
    components = parser.fill_parent_id(components)
    relations = parser.fix_broken_relations(components, relations, broken)
    relations = parser.fix_missing_relations(components, relations)
    i = parser.check_relations(components, relations, 1, True)
    return parser.check_components(components, relations, i) - 1


def test_shop_converts_to_nested_workspace(tmp_path):
    dsl = convert("shop", tmp_path)
    assert 'customer = person "Customer"' in dsl
    assert 'online_shop = softwareSystem "Online Shop"' in dsl
    assert 'order_api = container "Order API" "Accepts and stores orders" "Python, FastAPI" {' in dsl
    assert 'order_service = component "Order Service"' in dsl
    assert 'web_app -> order_api "Register order (subscriber, product): order" "JSON/HTTPS"' in dsl
    assert "container online_shop {" in dsl
    assert "component order_api {" in dsl


def test_compressed_file_gives_same_output(tmp_path):
    assert convert("shop-compressed", tmp_path) == convert("shop", tmp_path)


def test_shop_passes_all_checks():
    assert run_checks("shop") == 0


def test_broken_reports_every_problem(capsys):
    assert run_checks("broken") == 5
    out = capsys.readouterr().out
    assert '"Create order"' in out
    assert 'Container "Web App"' in out
    assert 'Container "Report Job" has no incoming or outgoing relationships' in out
    assert 'Container "Web App" has no technology' in out
    assert "does not name its input data" in out


def test_broken_repairs_unattached_arrow(tmp_path):
    assert 'order_api -> stock_db "Reserve stock (order): reservation" "JDBC"' in convert("broken", tmp_path)


@pytest.mark.parametrize("name", ["shop", "shop-compressed", "broken"])
def test_legacy_excel_export(name, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    parser.main(["-i", str(EXAMPLES / f"{name}.drawio"), "-o", "out.xlsx"])
    assert (tmp_path / "out.xlsx").stat().st_size > 0
    assert (tmp_path / "workspace.dsl").exists()


def test_broken_reports_dropped_relationships():
    problems = parser.load_and_check([str(EXAMPLES / "broken.drawio")], True)[2]
    assert len(problems) == 7
    assert all(p.severity == "warning" for p in problems)
    assert any(p.code == "C4-REL-004" and '"Export ledger (date): ledger" dropped' in p.message for p in problems)
    assert any(p.code == "C4-REL-005" and '"Send invoice (order): invoice" dropped' in p.message for p in problems)


def test_strict_mode_fails_and_writes_nothing(tmp_path):
    output = tmp_path / "broken.dsl"
    assert main([str(EXAMPLES / "broken.drawio"), "-o", str(output), "--strict"]) == 1
    assert not output.exists()
    assert main([str(EXAMPLES / "shop.drawio"), "-o", str(output), "-d", "--strict"]) == 0


def test_multipage_reads_every_page_and_merges_elements(tmp_path):
    dsl = convert("multipage", tmp_path)
    assert dsl.count('= person "Customer"') == 1
    assert dsl.count('= softwareSystem "Online Shop" "Sells products to customers" {') == 1
    assert 'web_app = container "Web App"' in dsl
    assert 'customer -> online_shop "Places orders" "HTTPS"' in dsl
    assert 'customer -> web_app "Browses and orders" "HTTPS"' in dsl
    assert 'orders_api = container "Order API"' in dsl  # c4Id is used as the identifier
    assert 'orders_api -> payment_provider "Charge card (order): receipt" "gRPC"' in dsl
    assert 'payment_provider = softwareSystem "Payment Provider" "External card payment gateway" "External"' in dsl
    assert parser.load_and_check([str(EXAMPLES / "multipage.drawio")], True)[2] == []


def test_several_files_are_merged_into_one_workspace(tmp_path):
    output = tmp_path / "workspace.dsl"
    files = [str(EXAMPLES / "shop.drawio"), str(EXAMPLES / "multipage.drawio")]
    assert main(files + ["-o", str(output)]) == 0
    dsl = output.read_text()
    assert dsl.count('= softwareSystem "Online Shop"') == 1
    assert dsl.count('= container "Order API"') == 1
    assert 'order_service = component "Order Service"' in dsl
    assert 'customer -> online_shop "Places orders" "HTTPS"' in dsl


def test_dry_run_prints_and_writes_nothing(tmp_path, capsys):
    output = tmp_path / "shop.dsl"
    assert main([str(EXAMPLES / "shop.drawio"), "-o", str(output), "--dry-run"]) == 0
    assert not output.exists()
    assert capsys.readouterr().out.startswith('workspace "Workspace" {')


def test_diff_shows_changes_against_existing_output(tmp_path, capsys):
    output = tmp_path / "shop.dsl"
    main([str(EXAMPLES / "shop.drawio"), "-o", str(output)])
    output.write_text(output.read_text().replace('"React"', '"Vue"'))
    capsys.readouterr()
    assert main([str(EXAMPLES / "shop.drawio"), "-o", str(output), "--diff"]) == 0
    diff = capsys.readouterr().out
    assert '-            web_app = container "Web App" "Product catalogue and checkout" "Vue"' in diff
    assert '+            web_app = container "Web App" "Product catalogue and checkout" "React"' in diff
    assert '"Vue"' in output.read_text()


def test_check_writes_nothing_and_sets_exit_code(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main([str(EXAMPLES / "broken.drawio"), "--check"]) == 1
    assert main([str(EXAMPLES / "shop.drawio"), "--check"]) == 0
    assert list(tmp_path.iterdir()) == []


def test_report_is_written_as_json(tmp_path):
    import json
    report = tmp_path / "report.json"
    main([str(EXAMPLES / "broken.drawio"), "-d", "--check", "--report", str(report)])
    data = json.loads(report.read_text())
    assert data["problemCount"] == 7
    assert data["problems"][0]["number"] == 1
    assert data["elements"] == 5


def test_outer_relationships_come_first(tmp_path):
    # Structurizr rejects an explicit relationship that an earlier nested one already implied
    output = tmp_path / "merged.dsl"
    main([str(EXAMPLES / "shop.drawio"), str(EXAMPLES / "multipage.drawio"), "-o", str(output)])
    lines = output.read_text().splitlines()
    outer = lines.index('        online_shop -> payment_provider "Charge card (order): receipt" "gRPC"')
    nested = lines.index('        order_service -> payment_provider "Charge card (order): receipt" "gRPC"')
    assert outer < nested
