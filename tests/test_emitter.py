"""Unit tests for the mapper and emitter, without any draw.io file."""

from types import SimpleNamespace

from drawio_structurizr.emitter import emit
from drawio_structurizr.mapper import map_diagram


def shape(id, c4Type, c4Name, parent_id=None, **extra):
    return SimpleNamespace(id=id, c4Type=c4Type, c4Name=c4Name, parent_id=parent_id, **extra)


def test_duplicate_names_get_unique_identifiers():
    components = {"1": shape("1", "Container", "API"), "2": shape("2", "Container", "API")}
    dsl = emit(map_diagram(components, []))
    assert "api = container" in dsl
    assert "api_2 = container" in dsl


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
