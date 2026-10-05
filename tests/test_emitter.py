"""Unit tests for the mapper and emitter, without any draw.io file."""

from types import SimpleNamespace

from drawio_structurizr.emitter import emit
from drawio_structurizr.mapper import map_diagram


def shape(id, c4Type, c4Name, parent_id=None, **extra):
    return SimpleNamespace(id=id, c4Type=c4Type, c4Name=c4Name, parent_id=parent_id, **extra)


def test_same_element_on_two_pages_is_merged():
    components = {
        "p1/a": shape("p1/a", "Software System", "Shop", c4Description="Sells things"),
        "p2/a": shape("p2/a", "SystemScopeBoundary", "shop"),
    }
    dsl = emit(map_diagram(components, []))
    assert dsl.count("softwareSystem") == 1
    assert '"Sells things"' in dsl


def test_same_container_name_in_different_systems_is_kept_apart():
    components = {
        "s1": shape("s1", "Software System", "Shop"),
        "s2": shape("s2", "Software System", "Billing"),
        "c1": shape("c1", "Container", "API", parent_id="s1"),
        "c2": shape("c2", "Container", "API", parent_id="s2"),
    }
    dsl = emit(map_diagram(components, []))
    assert "api = container" in dsl
    assert "api_2 = container" in dsl


def test_duplicate_relationships_are_merged():
    components = {"1": shape("1", "Person", "User"), "2": shape("2", "Software System", "Shop")}
    rel = SimpleNamespace(source="1", target="2", c4Description="Uses", c4Technology="")
    assert emit(map_diagram(components, [rel, rel])).count("user -> shop") == 1


def test_quotes_are_escaped():
    components = {"1": shape("1", "Person", 'The "Boss"')}
    assert 'person "The \\"Boss\\""' in emit(map_diagram(components, []))


def test_relationship_to_unknown_element_is_dropped():
    components = {"1": shape("1", "Person", "User")}
    relations = [SimpleNamespace(source="1", target="missing", c4Description="Uses", c4Technology="")]
    assert "->" not in emit(map_diagram(components, relations))


def test_empty_relationship_description_defaults_to_uses():
    components = {"1": shape("1", "Person", "User"), "2": shape("2", "Software System", "Shop")}
    relations = [SimpleNamespace(source="1", target="2", c4Description="", c4Technology="")]
    assert 'user -> shop "Uses"' in emit(map_diagram(components, relations))


def test_c4_id_is_used_as_identifier():
    components = {"1": shape("1", "Container", "Order API", c4Id="orders-api v2")}
    assert "orders-api_v2 = container" in emit(map_diagram(components, []))


def test_tags_on_elements_and_relationships():
    components = {
        "1": shape("1", "Person", "User"),
        "2": shape("2", "Software System", "Bank", c4Tags="External, Legacy"),
    }
    relations = [SimpleNamespace(source="1", target="2", c4Description="Pays", c4Technology="", c4Tags="Async")]
    dsl = emit(map_diagram(components, relations))
    assert 'bank = softwareSystem "Bank" "" "External,Legacy"' in dsl
    assert 'user -> bank "Pays" "" "Async"' in dsl
