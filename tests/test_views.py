"""Phase E: a System Context view for each top-level software system with outside relationships."""

from pathlib import Path

from drawio_structurizr.main import main

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "views"
EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def convert(path, tmp_path, *flags):
    output = tmp_path / "out.dsl"
    assert main([str(path), "-o", str(output), *flags]) == 0
    return output.read_text()


def test_context_view_per_connected_system(tmp_path):
    dsl = convert(FIXTURES / "person-to-system-to-system.drawio", tmp_path)
    assert "systemLandscape {" in dsl
    # the key comes from the identifier, so it only uses characters Structurizr accepts
    assert 'systemContext order_payment_api "order_payment_api-context" "Order & Payment API - System Context" {' in dsl
    assert 'systemContext bank "bank-context" "Bank - System Context" {' in dsl
    assert dsl.count("systemContext") == 2


def test_lone_system_gets_no_context_view(tmp_path):
    dsl = convert(FIXTURES / "lone-system.drawio", tmp_path)
    assert "systemLandscape {" in dsl
    assert "systemContext" not in dsl


def test_relationships_of_nested_elements_count(tmp_path):
    # in shop.drawio only the containers inside Online Shop have relationships
    dsl = convert(EXAMPLES / "shop.drawio", tmp_path)
    assert 'systemContext online_shop "online_shop-context" "Online Shop - System Context" {' in dsl
    assert 'systemContext payment_provider "payment_provider-context"' in dsl


def test_context_views_can_be_switched_off(tmp_path):
    dsl = convert(FIXTURES / "person-to-system-to-system.drawio", tmp_path, "--no-context-views")
    assert "systemContext" not in dsl
