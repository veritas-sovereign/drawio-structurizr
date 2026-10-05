"""Phase B: output order does not depend on the order shapes or pages are drawn in."""

import random
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace

import pytest

from drawio_structurizr import validate
from drawio_structurizr.emitter import emit
from drawio_structurizr.main import main
from drawio_structurizr.mapper import map_diagram

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def shuffled_copy(source, target, seed):
    """Write ``source`` with its pages and the shapes on each page in a random order."""
    rng = random.Random(seed)
    tree = ET.parse(source)
    mxfile = tree.getroot()
    pages = list(mxfile)
    rng.shuffle(pages)
    for page in pages:
        mxfile.remove(page)
    for page in pages:
        mxfile.append(page)
        root = page.find("mxGraphModel/root")
        cells = list(root)
        rng.shuffle(cells)
        for cell in cells:
            root.remove(cell)
        for cell in cells:
            root.append(cell)
    tree.write(target, encoding="utf-8")


def convert(path, output):
    assert main([str(path), "-o", str(output)]) == 0
    return output.read_bytes()


@pytest.mark.parametrize("sample", ["shop", "multipage", "broken"])
@pytest.mark.parametrize("seed", [1, 2, 3])
def test_shuffled_shapes_and_pages_give_identical_output(sample, seed, tmp_path):
    original = convert(EXAMPLES / f"{sample}.drawio", tmp_path / "original.dsl")
    shuffled_copy(EXAMPLES / f"{sample}.drawio", tmp_path / "shuffled.drawio", seed)
    assert convert(tmp_path / "shuffled.drawio", tmp_path / "shuffled.dsl") == original


def shape(id, c4Type, c4Name, parent_id=None):
    return SimpleNamespace(id=id, c4Type=c4Type, c4Name=c4Name, parent_id=parent_id)


def test_identifier_suffixes_do_not_depend_on_order():
    shapes = [shape("s1", "Software System", "Shop"), shape("s2", "Software System", "Billing"),
              shape("c1", "Container", "API", "s1"), shape("c2", "Container", "API", "s2")]
    forward = emit(map_diagram({s.id: s for s in shapes}, []))
    backward = emit(map_diagram({s.id: s for s in reversed(shapes)}, []))
    assert forward == backward
    # Billing sorts before Shop, so its container gets the plain name
    assert forward.index("billing = softwareSystem") < forward.index("api = container") < forward.index("shop = softwareSystem")


def test_outer_relationships_still_come_first(tmp_path):
    # regression for 24c01d1: sorting must keep outer relationships before nested ones
    output = tmp_path / "merged.dsl"
    main([str(EXAMPLES / "shop.drawio"), str(EXAMPLES / "multipage.drawio"), "-o", str(output)])
    lines = output.read_text().splitlines()
    outer = lines.index('        online_shop -> payment_provider "Charge card (order): receipt" "gRPC"')
    nested = lines.index('        order_service -> payment_provider "Charge card (order): receipt" "gRPC"')
    assert outer < nested


@pytest.mark.skipif(not validate.is_available(), reason="needs structurizr-cli or a running Docker")
def test_merged_workspace_passes_structurizr_validation(tmp_path):
    # the 24c01d1 failure only shows up in Structurizr itself, so check with the real validator
    output = tmp_path / "merged.dsl"
    main([str(EXAMPLES / "shop.drawio"), str(EXAMPLES / "multipage.drawio"), "-o", str(output)])
    ok, message = validate.validate(str(output))
    assert ok, message
