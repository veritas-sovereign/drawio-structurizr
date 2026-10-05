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


def _views(model: Model):
    lines = [
        f"{INDENT * 2}systemLandscape {{",
        f"{INDENT * 3}include *",
        f"{INDENT * 3}autoLayout",
        f"{INDENT * 2}}}",
    ]

    def walk(element):
        view = {"softwareSystem": "container", "container": "component"}.get(element.kind)
        if view and element.children:
            lines.extend([
                f"{INDENT * 2}{view} {element.identifier} {{",
                f"{INDENT * 3}include *",
                f"{INDENT * 3}autoLayout",
                f"{INDENT * 2}}}",
            ])
        for child in element.children:
            walk(child)

    for element in model.elements:
        walk(element)
    lines.append(f"{INDENT * 2}theme default")
    return lines


def emit(model: Model, name="Workspace"):
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
    lines += [f"{INDENT}}}", "", f"{INDENT}views {{", *_views(model), f"{INDENT}}}", "}"]
    return "\n".join(lines) + "\n"


def write(model: Model, path, name="Workspace"):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(emit(model, name))
