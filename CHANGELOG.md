# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed

- Relationships between the same elements with the same description but different technologies were both emitted, which Structurizr rejects. They are now merged (Structurizr identifies relationships by source, target and description), keeping the first technology and combining tags.
- Element names are compared with `strip().casefold()` instead of `lower()`.
- Merged workspaces could fail Structurizr validation with "relationship already exists": a nested relationship implies one between the parents, which then clashed with an explicit one defined later. Outer relationships are now written first.

### Changed

- Generated workspaces no longer set `theme default`, which made structurizr-cli fetch the theme over the network.
- Check messages and the default relationship label are now in English instead of Russian.
- `--validate` falls back to the `structurizr/cli` Docker image when no local structurizr-cli is installed and Docker is running.
- `drawio-structurizr` now runs the checks and prints problems to stderr. New options: `-d/--check-data` and `--strict` (exit code 1 and no output when problems are found).
- When a shape sits inside several boxes, the smallest one is its parent. Previously it depended on the order of shapes in the file.
- A trailing `[technology]` in a relationship description is moved to the technology when `c4Technology` is empty.

### Added

- Hierarchy checks that stop the output with an error, even without `--strict`: a container outside a software system (`C4-HIER-001`), a component outside a container (`C4-HIER-002`), and a person or software system inside another element (`C4-HIER-003`). Structurizr would reject such output.
- Every problem has a code and a severity (`error` or `warning`), shown on the terminal and in `--report` (`code`, `severity`, `errorCount`, `warningCount`).
- Shapes with an unknown `c4Type` are skipped with a warning (`C4-TYPE-001`) instead of becoming software systems.
- `tests/fixtures/hierarchy/` fixtures.
- Merging uses `c4Id` when both shapes have one, so an element can be renamed on one page without splitting it; a `c4Id` on only one shape is adopted. Relationships can carry a `c4Id` too.
- Merge conflicts are reported: `C4-IDENT-001` (one `c4Id` on different kinds, error), `C4-IDENT-002` (different parents), `C4-MERGE-001` (same name, different `c4Id`s, error), `C4-MERGE-002`/`003` (different description/technology), `C4-MERGE-004` (different relationship technology), `C4-MERGE-005` (different names for one `c4Id`). They appear in `--report` and count for `--strict` and `--check`.
- A `systemContext` view for each top-level software system with a relationship crossing its boundary (directly or through its containers and components), keyed `<identifier>-context`. `--no-context-views` turns them off.
- `--validate-required`: like `--validate`, but fails before writing anything when no validator is available, listing what was checked (structurizr-cli on `PATH`, Docker installed and running).
- Every page of a `.drawio` file is read. Previously only the first page was, and the rest were silently ignored.
- Elements that appear on several pages are merged into one; duplicate relationships are merged too.
- Relationships that are dropped (pointing at a plain shape, or with an arrow that cannot be repaired) are reported.
- Several input files can be given; they are merged into one workspace.
- `--dry-run` prints the generated DSL, and `--diff` prints a unified diff against the existing output file; neither writes anything.
- `c4Id` property sets an element's DSL identifier; `c4Tags` adds tags to elements and relationships.
- `--export FORMAT` (repeatable) and `--export-dir` export the workspace with structurizr-cli to JSON, PlantUML, C4-PlantUML, Mermaid, DOT, Ilograph or WebSequenceDiagrams.
- `--report FILE` writes problems and counts as JSON.
- `--check` runs the checks only, for scripts and the new `drawio-structurizr-check` pre-commit hook (`.pre-commit-hooks.yaml`).
- Dockerfile with Python, Java and a checksum-pinned structurizr-cli; `publish-image` workflow smoke-tests it and pushes multi-arch images to GHCR on `v*` tags.
- The image smoke test also checks that `--check` exits with code 1 and writes nothing, and runs the README's Docker pre-commit hook command; published images carry an SBOM.
- README: pre-commit hooks that validate `.dsl` files with Docker or a local structurizr-cli, and a note that `drawio-structurizr-check` covers diagrams only.
- Docker base image pinned by digest, with Dependabot (`.github/dependabot.yml`) proposing weekly updates for it and for the GitHub Actions versions. README documents what is pinned and how to update the structurizr-cli pin.
- `publish-pypi` workflow builds the package and publishes it to PyPI with trusted publishing on `v*` tags.
- `examples/multipage.drawio` sample.
- GitHub Actions workflow running pytest on Python 3.9 and 3.13.
- README sections on limitations (including that draw.io layout is not preserved) and on using shapes from other draw.io libraries.

## [0.1.0] - 2026-10-05

### Added

- `drawio-structurizr` command that converts a C4 draw.io diagram to a Structurizr DSL workspace (`mapper.py`, `emitter.py`, `main.py`).
- Optional `--validate` step using structurizr-cli (`validate.py`).
- C4 system and container boundary shapes are mapped to `softwareSystem` and `container`.
- Sample diagrams in `examples/`: a clean model, its compressed copy, and a model with deliberate mistakes.
- pytest suite covering the samples end to end and the mapper and emitter.
- Packaging with `pyproject.toml`, MIT license, `.gitignore`, `.gitattributes` and `.editorconfig`.

### Changed

- Scripts moved into the `drawio_structurizr` package under `src/`: `drawio_parser.py` is now `parser.py`, and `drawio_print.py` is now `dump.py`. Run them with `python -m drawio_structurizr.parser` and `python -m drawio_structurizr.dump`.

### Fixed

- Arrows that touch a shape without being attached are now repaired. The repair previously read the arrow's overall position, which is always (0, 0), instead of its end point.
- Removed unused `tkinter` and `select` imports that crashed the scripts on Python builds without Tk.

[Unreleased]: https://github.com/veritas-sovereign/drawio-structurizr/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/veritas-sovereign/drawio-structurizr/releases/tag/v0.1.0
