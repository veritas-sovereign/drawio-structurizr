"""Map C4 shapes from a draw.io diagram to Structurizr DSL constructs.

Builds a small intermediate model (elements + relationships) from the objects
returned by ``parser.load_from_xml``. The emitter consumes this model.
"""

import re
from dataclasses import dataclass, field

from .problems import Problem

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
    tags: list = field(default_factory=list)
    c4_id: str = ""
    children: list = field(default_factory=list)
    parent: "ModelElement" = field(default=None, repr=False, compare=False)


@dataclass
class ModelRelationship:
    source: str
    target: str
    description: str = ""
    technology: str = ""
    tags: list = field(default_factory=list)
    c4_id: str = ""


@dataclass
class Model:
    elements: list = field(default_factory=list)  # top-level elements only
    relationships: list = field(default_factory=list)


def _clean(text):
    return (text or "").replace("\n", " ").strip()


def _tags(obj):
    return [tag.strip() for tag in _clean(getattr(obj, "c4Tags", "")).split(",") if tag.strip()]


def _unique(base, used):
    candidate, n = base, 1
    while candidate in used:
        n += 1
        candidate = f"{base}_{n}"
    used.add(candidate)
    return candidate


def _identifier(name, used):
    base = re.sub(r"\W+", "_", name).strip("_").lower() or "element"
    if base[0].isdigit():
        base = "e_" + base
    return _unique(base, used)


def _explicit_identifier(c4_id, used):
    base = re.sub(r"[^\w-]+", "_", c4_id).strip("_") or "element"
    if base[0].isdigit():
        base = "e_" + base
    return _unique(base, used)


def _is_ancestor(element, candidate):
    while candidate is not None:
        if candidate is element:
            return True
        candidate = candidate.parent
    return False


def _normalise(name):
    return name.strip().casefold()


KIND_RANK = {"person": 0, "softwareSystem": 1, "container": 2, "component": 3}


def _element_key(element):
    return (KIND_RANK.get(element.kind, 9), _normalise(element.name), element.name, element.c4_id)


def _path_key(element):
    """Sort key from the root down, so the order does not depend on the drawing."""
    path = []
    while element is not None:
        path.append(_element_key(element))
        element = element.parent
    return tuple(reversed(path))


def _label(kind, name, c4_id=""):
    return f'{kind} "{name}"' + (f" (c4Id {c4_id})" if c4_id else "")


def map_diagram(components, relations, problems=None):
    """Map parsed draw.io components and relations to a ``Model``.

    Elements drawn more than once (on several pages or in several files) are
    merged into one:

    * Two shapes with a ``c4Id`` are the same element when their ``c4Id``s
      match, whatever their names.
    * Otherwise shapes are the same when kind, normalised name
      (``strip().casefold()``) and resolved parent all match. A shape with a
      ``c4Id`` merges this way with shapes without one, and the element takes
      the ``c4Id``.

    The first shape seen supplies name, description and technology; later
    shapes fill gaps, and differences are reported as warnings. Tags are
    combined. Conflicts that Structurizr would reject are reported as errors.

    Relationships are the same when they have the same ``c4Id``, or the same
    source, target and description (which is how Structurizr identifies them).
    Relationships with the same ``c4Id`` but a different source, target or
    description are still merged, keeping the first, and reported.

    A ``c4Id`` becomes the DSL identifier (characters that are not allowed are
    replaced); otherwise the identifier comes from the name. Problems found
    while merging are appended to ``problems`` when a list is given.
    """
    if problems is None:
        problems = []

    def add(code, severity, message):
        problems.append(Problem(code, severity, message))

    def kind_and_name(comp):
        c4_type = getattr(comp, "c4Type", None) or "Software System"
        return C4_TO_DSL.get(c4_type, "softwareSystem"), _clean(getattr(comp, "c4Name", "")) or c4_type

    def raw_depth(comp):
        depth, seen = 0, set()
        while getattr(comp, "parent_id", None) in components and comp.id not in seen:
            seen.add(comp.id)
            comp, depth = components[comp.parent_id], depth + 1
        return depth

    by_name = {}   # (id of resolved parent, kind, normalised name) -> ModelElement
    by_c4_id = {}  # c4Id -> ModelElement
    element_of = {}  # draw.io id -> ModelElement
    unique = []

    # parents first, so each shape's parent is already resolved
    for comp in sorted(components.values(), key=raw_depth):
        kind, name = kind_and_name(comp)
        c4_id = _clean(getattr(comp, "c4Id", ""))
        description = _clean(getattr(comp, "c4Description", ""))
        technology = _clean(getattr(comp, "c4Technology", ""))
        parent = element_of.get(getattr(comp, "parent_id", None))
        name_key = (id(parent), kind, _normalise(name))

        element = None
        if c4_id and c4_id in by_c4_id:
            element = by_c4_id[c4_id]
            if element.kind != kind:
                add("C4-IDENT-001", "error",
                    f"c4Id {c4_id} is used by {_label(element.kind, element.name)} and by {_label(kind, name)}; "
                    "one c4Id cannot name elements of different kinds")
                element = None
            else:
                if _normalise(element.name) != _normalise(name):
                    add("C4-MERGE-005", "warning",
                        f'{_label(kind, element.name, c4_id)} is also drawn as "{name}"; kept "{element.name}"')
                if parent is not None and element.parent is not None and parent is not element.parent:
                    add("C4-IDENT-002", "warning",
                        f"{_label(kind, element.name, c4_id)} is drawn inside {_label(element.parent.kind, element.parent.name)} "
                        f'and inside {_label(parent.kind, parent.name)}; kept "{element.parent.name}"')
        elif name_key in by_name:
            candidate = by_name[name_key]
            if c4_id and candidate.c4_id and candidate.c4_id != c4_id:
                add("C4-MERGE-001", "error",
                    f"{_label(kind, name)} is drawn twice with different c4Ids ({candidate.c4_id} and {c4_id}); "
                    "Structurizr does not allow two elements with the same name here. Use one c4Id or rename one")
            else:
                element = candidate

        if element is None:
            element = ModelElement(id=comp.id, identifier="", kind=kind, name=name,
                                   description=description, technology=technology, parent=parent)
            unique.append(element)
            by_name.setdefault(name_key, element)
        else:
            if description and element.description and description != element.description:
                add("C4-MERGE-002", "warning",
                    f'{_label(kind, element.name)} has different descriptions; kept "{element.description}", saw "{description}"')
            if technology and element.technology and technology != element.technology:
                add("C4-MERGE-003", "warning",
                    f'{_label(kind, element.name)} has different technologies; kept "{element.technology}", saw "{technology}"')
            element.description = element.description or description
            element.technology = element.technology or technology
            if element.parent is None and parent is not None and not _is_ancestor(element, parent):
                element.parent = parent

        if c4_id and not element.c4_id:
            element.c4_id = c4_id
        if element.c4_id:
            by_c4_id.setdefault(element.c4_id, element)
        element.tags += [tag for tag in _tags(comp) if tag not in element.tags]
        element_of[comp.id] = element

    # Output order is canonical, not drawing order: identifiers (including the
    # _2 suffixes for clashes), elements, children, tags and relationships are
    # all sorted, so shuffling shapes or pages gives byte-identical DSL.
    # Merging above still runs in drawing order ("first shape wins").
    unique.sort(key=_path_key)

    # explicit ids claim their identifiers first, so they are used verbatim
    used = set()
    for element in unique:
        if element.c4_id:
            element.identifier = _explicit_identifier(element.c4_id, used)
    for element in unique:
        if not element.c4_id:
            element.identifier = _identifier(element.name, used)

    model = Model()
    for element in unique:  # already sorted, so children lists are sorted too
        element.tags.sort()
        if element.parent is not None:
            element.parent.children.append(element)
        else:
            model.elements.append(element)

    def depth(element):
        n = 0
        while element.parent is not None:
            n, element = n + 1, element.parent
        return n

    # Structurizr creates implied relationships between parents when a nested
    # relationship is defined, and rejects an explicit one defined afterwards
    # with the same description. Emitting outer relationships first avoids that.
    resolved = []
    for rel in relations:
        source, target = element_of.get(rel.source), element_of.get(rel.target)
        if source is not None and target is not None:
            resolved.append((depth(source) + depth(target), rel, source, target))
    resolved.sort(key=lambda item: item[0])

    by_signature = {}  # (source, target, description) -> ModelRelationship
    rel_by_c4_id = {}
    for _, rel, source, target in resolved:
        description = _clean(getattr(rel, "c4Description", ""))
        technology = _clean(getattr(rel, "c4Technology", ""))
        c4_id = _clean(getattr(rel, "c4Id", ""))
        signature = (source.identifier, target.identifier, description)
        label = f'Relationship "{description or "Uses"}" from {_label(source.kind, source.name)} to {_label(target.kind, target.name)}'

        relationship = rel_by_c4_id.get(c4_id) if c4_id else None
        if relationship is not None and (relationship.source, relationship.target, relationship.description) != signature:
            add("C4-MERGE-006", "warning",
                f"Relationships with c4Id {c4_id} differ: kept "
                f'"{relationship.description or "Uses"}" from {relationship.source} to {relationship.target}, '
                f'saw "{description or "Uses"}" from {source.identifier} to {target.identifier}')
        if relationship is None and signature in by_signature:
            relationship = by_signature[signature]
            if c4_id and relationship.c4_id and relationship.c4_id != c4_id:
                add("C4-MERGE-001", "error",
                    f"{label} is drawn twice with different c4Ids ({relationship.c4_id} and {c4_id}); "
                    "Structurizr does not allow two relationships with the same source, target and description")
                continue

        if relationship is None:
            relationship = ModelRelationship(source=source.identifier, target=target.identifier,
                                             description=description, technology=technology, c4_id=c4_id)
            model.relationships.append(relationship)
            by_signature.setdefault(signature, relationship)
        else:
            if technology and relationship.technology and technology != relationship.technology:
                add("C4-MERGE-004", "warning",
                    f'{label} has different technologies; kept "{relationship.technology}", saw "{technology}"')
            relationship.technology = relationship.technology or technology
            relationship.c4_id = relationship.c4_id or c4_id
        if relationship.c4_id:
            rel_by_c4_id.setdefault(relationship.c4_id, relationship)
        relationship.tags += [tag for tag in _tags(rel) if tag not in relationship.tags]

    # Outer relationships first (see above), then a canonical order.
    depth_of = {element.identifier: depth(element) for element in unique}
    for relationship in model.relationships:
        relationship.tags.sort()
    model.relationships.sort(key=lambda r: (depth_of[r.source] + depth_of[r.target], r.source, r.target,
                                            r.c4_id, r.description, r.technology))
    return model
