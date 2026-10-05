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
    assert any('"Export ledger (date): ledger" dropped: it does not connect two C4 elements' in p for p in problems)
    assert any('"Send invoice (order): invoice" dropped: its arrow is not attached' in p for p in problems)


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
    assert 'order_api -> payment_provider "Charge card (order): receipt" "gRPC"' in dsl
    assert parser.load_and_check([str(EXAMPLES / "multipage.drawio")], True)[2] == []
