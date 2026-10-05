"""Phase A: element and relationship identity when merging pages and files."""

from pathlib import Path

from drawio_structurizr import parser
from drawio_structurizr.main import main
from drawio_structurizr.mapper import map_diagram
from drawio_structurizr.emitter import emit

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "identity"


def convert(name):
    components, relations, problems = parser.load_and_check([str(FIXTURES / f"{name}.drawio")])
    dsl = emit(map_diagram(components, relations, problems))
    return dsl, problems


def codes(problems):
    return [p.code for p in problems]


def test_same_c4id_different_name_merges_and_warns():
    dsl, problems = convert("same-id-different-name")
    assert dsl.count("= softwareSystem") == 1
    assert 'shop_sys = softwareSystem "Shop"' in dsl
    assert codes(problems) == ["C4-MERGE-005"]
    assert 'also drawn as "Web Shop"; kept "Shop"' in problems[0].message


def test_c4id_on_one_side_is_adopted():
    dsl, problems = convert("same-id-one-side")
    assert dsl.count("= softwareSystem") == 1
    assert 'shop_sys = softwareSystem "Shop"' in dsl
    assert problems == []


def test_same_c4id_different_kind_is_an_error(tmp_path):
    _, problems = convert("same-id-different-kind")
    errors = [p for p in problems if p.code == "C4-IDENT-001"]
    assert len(errors) == 1 and errors[0].severity == "error"
    output = tmp_path / "out.dsl"
    assert main([str(FIXTURES / "same-id-different-kind.drawio"), "-o", str(output)]) == 1
    assert not output.exists()


def test_same_name_different_c4id_is_an_error(tmp_path):
    _, problems = convert("same-name-different-id")
    errors = [p for p in problems if p.code == "C4-MERGE-001"]
    assert len(errors) == 1 and errors[0].severity == "error"
    assert "shop_a and shop_b" in errors[0].message
    assert main([str(FIXTURES / "same-name-different-id.drawio"), "-o", str(tmp_path / "out.dsl")]) == 1


def test_conflicting_description_keeps_first_and_warns():
    dsl, problems = convert("same-name-conflicting-description")
    assert dsl.count("= softwareSystem") == 1  # "Shop" and "shop " are the same name
    assert '"Sells things"' in dsl and "Sells everything" not in dsl
    assert codes(problems) == ["C4-MERGE-002"]


def test_relationships_with_same_description_merge():
    # Structurizr identifies relationships by source, target and description,
    # so these must become one relationship: tags combined, first technology kept
    dsl, problems = convert("relationships-same-description")
    assert dsl.count("customer -> shop") == 1
    assert 'customer -> shop "Orders" "HTTPS" "External,Sync"' in dsl  # tags sorted
    assert codes(problems) == ["C4-MERGE-004"]


def test_merge_warnings_reach_strict_and_report(tmp_path):
    output = tmp_path / "out.dsl"
    assert main([str(FIXTURES / "same-name-conflicting-description.drawio"), "-o", str(output), "--strict"]) == 1
    assert not output.exists()
    assert main([str(FIXTURES / "same-name-conflicting-description.drawio"), "--check"]) == 1


def test_relationships_with_same_c4id_that_differ_warn():
    dsl, problems = convert("relationship-same-id-differs")
    assert dsl.count("customer ->") == 1
    assert 'customer -> shop "Orders" "HTTPS"' in dsl
    merge = [p for p in problems if p.code.startswith("C4-MERGE")]
    assert [p.code for p in merge] == ["C4-MERGE-006"]
    assert merge[0].severity == "warning"
    assert 'kept "Orders" from customer to shop, saw "Places orders" from customer to bank' in merge[0].message
