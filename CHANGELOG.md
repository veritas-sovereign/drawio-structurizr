# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

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
