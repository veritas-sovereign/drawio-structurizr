# Examples

| File | What it shows |
| --- | --- |
| `shop.drawio` | A clean diagram: person, system boundary, containers, a component and an external system. Passes every check. |
| `shop-compressed.drawio` | The same diagram saved in draw.io's compressed format. Produces identical output. |
| `multipage.drawio` | A system context page and a container page. Shared elements are merged, technologies are written as `[...]` at the end of descriptions, Order API has a `c4Id`, and Payment Provider has a `c4Tags` tag. |
| `broken.drawio` | Seven warnings the checks report (including a relationship to a plain shape and an arrow that cannot be repaired), plus an arrow touching "Stock DB" without being attached, which is repaired. |

Run from this directory after `pip install drawio-structurizr` (or `pip install -e ..` from a checkout):

```bash
drawio-structurizr shop.drawio -o shop.dsl -s
drawio-structurizr multipage.drawio -o multipage.dsl
drawio-structurizr shop.drawio multipage.drawio -o merged.dsl --dry-run
drawio-structurizr broken.drawio -o broken.dsl -d
```

`broken.drawio` produces a valid workspace despite its warnings. Diagrams that break the C4 nesting rules (for example a container outside any software system) are in `tests/fixtures/hierarchy/`; they stop with an error and write nothing.
