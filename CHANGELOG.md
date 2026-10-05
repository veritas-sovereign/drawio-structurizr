# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed

- Check messages and the default relationship label are now in English instead of Russian.
- `--validate` falls back to the `structurizr/cli` Docker image when no local structurizr-cli is installed and Docker is running.

- `drawio-structurizr` now runs the checks and prints problems to stderr. New options: `-d/--check-data` and `--strict` (exit code 1 and no output when problems are found).
- When a shape sits inside several boxes, the smallest one is its parent. Previously it depended on the order of shapes in the file.
- A trailing `[technology]` in a relationship description is moved to the technology when `c4Technology` is empty.

### Added

- Every page of a `.drawio` file is read. Previously only the first page was, and the rest were silently ignored.
- Elements that appear on several pages are merged into one; duplicate relationships are merged too.
- Relationships that are dropped (pointing at a plain shape, or with an arrow that cannot be repaired) are reported.
- Several input files can be given; they are merged into one workspace.
- `--dry-run` prints the generated DSL, and `--diff` prints a unified diff against the existing output file; neither writes anything.
- `c4Id` property sets an element's DSL identifier; `c4Tags` adds tags to elements and relationships.
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
