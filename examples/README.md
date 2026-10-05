# Examples

| File | What it shows |
| --- | --- |
| `shop.drawio` | A clean diagram: person, system boundary, containers, a component and an external system. Passes every check. |
| `shop-compressed.drawio` | The same diagram saved in draw.io's compressed format. Produces identical output. |
| `multipage.drawio` | A system context page and a container page. Shared elements are merged, technologies are written as `[...]` at the end of descriptions, Order API has a `c4Id`, and Payment Provider has a `c4Tags` tag. |
| `broken.drawio` | Seven problems the checks report (including a relationship to a plain shape and an arrow that cannot be repaired), plus an arrow touching "Stock DB" without being attached, which is repaired. |

Run from this directory after `pip install -e ..`:

```bash
drawio-structurizr shop.drawio -o shop.dsl -s
drawio-structurizr multipage.drawio -o multipage.dsl
drawio-structurizr shop.drawio multipage.drawio -o merged.dsl --dry-run
drawio-structurizr broken.drawio -o broken.dsl -d
```

`broken.drawio` has containers outside any software system, so its `.dsl` output is not a valid Structurizr workspace. It exists to exercise the checks.
