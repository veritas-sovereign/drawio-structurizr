"""Map C4 shapes from a draw.io diagram to Structurizr DSL constructs.

Builds a small intermediate model (elements + relationships) from the objects
returned by ``parser.load_from_xml``. The emitter consumes this model.
"""

import re
from dataclasses import dataclass, field

# draw.io C4 shape type -> Structurizr DSL keyword
C4_TO_DSL = {
    "Person": "person",
    "Software System": "softwareSystem",
    "Container": "container",
    "Component": "component",
    "SystemScopeBoundary": "softwareSystem",
    "ContainerScopeBoundary": "container",
}


@dataclass
class ModelElement:
    id: str
    identifier: str
    kind: str
    name: str
    description: str = ""
    technology: str = ""
    children: list = field(default_factory=list)


@dataclass
class ModelRelationship:
    source: str
    target: str
    description: str = ""
    technology: str = ""


@dataclass
class Model:
    elements: list = field(default_factory=list)  # top-level elements only
    relationships: list = field(default_factory=list)


def _clean(text):
    return (text or "").replace("\n", " ").strip()


def _identifier(name, used):
    base = re.sub(r"\W+", "_", name).strip("_").lower() or "element"
    if base[0].isdigit():
        base = "e_" + base
    candidate, n = base, 1
    while candidate in used:
        n += 1
        candidate = f"{base}_{n}"
    used.add(candidate)
    return candidate


def map_diagram(components, relations):
    """Map parsed draw.io components and relations to a ``Model``."""
    used = set()
    by_id = {}

    for comp in components.values():
        c4_type = getattr(comp, "c4Type", None) or "Software System"
        name = _clean(getattr(comp, "c4Name", "")) or c4_type
        by_id[comp.id] = ModelElement(
            id=comp.id,
            identifier=_identifier(name, used),
            kind=C4_TO_DSL.get(c4_type, "softwareSystem"),
            name=name,
            description=_clean(getattr(comp, "c4Description", "")),
            technology=_clean(getattr(comp, "c4Technology", "")),
        )

    model = Model()
    for comp in components.values():
        element = by_id[comp.id]
        parent = by_id.get(getattr(comp, "parent_id", None))
        if parent is not None:
            parent.children.append(element)
        else:
            model.elements.append(element)

    for rel in relations:
        if rel.source in by_id and rel.target in by_id:
            model.relationships.append(ModelRelationship(
                source=by_id[rel.source].identifier,
                target=by_id[rel.target].identifier,
                description=_clean(getattr(rel, "c4Description", "")),
                technology=_clean(getattr(rel, "c4Technology", "")),
            ))

    return model
