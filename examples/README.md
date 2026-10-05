# Examples

| File | What it shows |
| --- | --- |
| `shop.drawio` | A clean diagram: person, system boundary, containers, a component and an external system. Passes every check. |
| `shop-compressed.drawio` | The same diagram saved in draw.io's compressed format. Produces identical output. |
| `broken.drawio` | Five problems the checks report, plus an arrow touching "Stock DB" without being attached, which the parser repairs. |

Run from this directory after `pip install -e ..`:

```bash
drawio-structurizr shop.drawio -o shop.dsl -s
python -m drawio_structurizr.parser -i broken.drawio -o broken.xlsx -d -s
```

`broken.drawio` has containers outside any software system, so its `.dsl` output is not a valid Structurizr workspace. It exists to exercise the checks.
