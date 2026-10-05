"""Generate a Structurizr DSL workspace from the intermediate model."""

from .mapper import Model, ModelElement

INDENT = "    "


def _quote(text):
    return '"' + text.replace('"', '\\"') + '"'


def _emit_element(element: ModelElement, depth, lines):
    pad = INDENT * depth
    args = [_quote(element.name), _quote(element.description)]
    if element.kind in ("container", "component"):
        args.append(_quote(element.technology))
    if element.tags:
        args.append(_quote(",".join(element.tags)))
    header = f"{pad}{element.identifier} = {element.kind} {' '.join(args)}"
    if element.children:
        lines.append(header + " {")
        for child in element.children:
            _emit_element(child, depth + 1, lines)
        lines.append(pad + "}")
    else:
        lines.append(header)


def _identifiers(element):
    """The identifiers of an element and everything nested inside it."""
    found = {element.identifier}
    for child in element.children:
        found |= _identifiers(child)
    return found


def _has_external_relationship(system, relationships):
    inside = _identifiers(system)
    return any((rel.source in inside) != (rel.target in inside) for rel in relationships)


def _view(header):
    return [
        f"{INDENT * 2}{header} {{",
        f"{INDENT * 3}include *",
        f"{INDENT * 3}autoLayout",
        f"{INDENT * 2}}}",
    ]


def _views(model: Model, context_views=True):
    lines = _view("systemLandscape")

    def walk(element):
        if context_views and element.kind == "softwareSystem" and element.parent is None \
                and _has_external_relationship(element, model.relationships):
            # key must match [a-zA-Z0-9_-]; identifiers already do
            lines.extend(_view(f"systemContext {element.identifier} {_quote(element.identifier + '-context')} "
                               f"{_quote(element.name + ' - System Context')}"))
        view = {"softwareSystem": "container", "container": "component"}.get(element.kind)
        if view and element.children:
            lines.extend(_view(f"{view} {element.identifier}"))
        for child in element.children:
            walk(child)

    for element in model.elements:
        walk(element)
    return lines


def emit(model: Model, name="Workspace", context_views=True):
    """Return the DSL text for ``model``."""
    lines = [f"workspace {_quote(name)} {{", f"{INDENT}model {{"]
    for element in model.elements:
        _emit_element(element, 2, lines)
    if model.relationships:
        lines.append("")
    for rel in model.relationships:
        args = [_quote(rel.description or "Uses")]
        if rel.technology or rel.tags:
            args.append(_quote(rel.technology))
        if rel.tags:
            args.append(_quote(",".join(rel.tags)))
        lines.append(f"{INDENT * 2}{rel.source} -> {rel.target} {' '.join(args)}")
    lines += [f"{INDENT}}}", "", f"{INDENT}views {{", *_views(model, context_views), f"{INDENT}}}", "}"]
    return "\n".join(lines) + "\n"


def write(model: Model, path, name="Workspace", context_views=True):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(emit(model, name, context_views))
