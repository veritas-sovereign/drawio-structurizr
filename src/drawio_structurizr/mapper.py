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
    parent: "ModelElement" = field(default=None, repr=False, compare=False)


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


def _is_ancestor(element, candidate):
    while candidate is not None:
        if candidate is element:
            return True
        candidate = candidate.parent
    return False


def map_diagram(components, relations):
    """Map parsed draw.io components and relations to a ``Model``.

    Shapes with the same DSL kind and name (case-insensitive) are merged into one
    element, so an element drawn on several pages appears once. Containers and
    components merge only when their parents also have the same kind and name. The first shape
    seen supplies each attribute; later ones only fill in what is still empty.
    """
    used = set()
    by_key = {}
    element_of = {}  # draw.io id -> ModelElement
    unique = []

    def kind_and_name(comp):
        c4_type = getattr(comp, "c4Type", None) or "Software System"
        return C4_TO_DSL.get(c4_type, "softwareSystem"), _clean(getattr(comp, "c4Name", "")) or c4_type

    for comp in components.values():
        kind, name = kind_and_name(comp)
        description = _clean(getattr(comp, "c4Description", ""))
        technology = _clean(getattr(comp, "c4Technology", ""))
        key = (kind, name.lower())
        parent = components.get(getattr(comp, "parent_id", None))
        if kind in ("container", "component") and parent is not None:
            parent_kind, parent_name = kind_and_name(parent)
            key += (parent_kind, parent_name.lower())

        element = by_key.get(key)
        if element is None:
            element = ModelElement(
                id=comp.id,
                identifier=_identifier(name, used),
                kind=kind,
                name=name,
                description=description,
                technology=technology,
            )
            by_key[key] = element
            unique.append(element)
        else:
            element.description = element.description or description
            element.technology = element.technology or technology
        element_of[comp.id] = element

    for comp in components.values():
        element = element_of[comp.id]
        parent = element_of.get(getattr(comp, "parent_id", None))
        if parent is not None and element.parent is None and not _is_ancestor(element, parent):
            element.parent = parent

    model = Model()
    for element in unique:
        if element.parent is not None:
            element.parent.children.append(element)
        else:
            model.elements.append(element)

    seen = set()
    for rel in relations:
        source, target = element_of.get(rel.source), element_of.get(rel.target)
        if source is None or target is None:
            continue
        relationship = ModelRelationship(
            source=source.identifier,
            target=target.identifier,
            description=_clean(getattr(rel, "c4Description", "")),
            technology=_clean(getattr(rel, "c4Technology", "")),
        )
        signature = (relationship.source, relationship.target, relationship.description, relationship.technology)
        if signature not in seen:
            seen.add(signature)
            model.relationships.append(relationship)

    return model
