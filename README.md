<div align="center">

# drawio-structurizr

### Turn draw.io C4 diagrams into checked, version-controlled Structurizr models

<br>

[![Full documentation](https://img.shields.io/badge/📖_full_documentation-github.com%2Fveritas--sovereign%2Fdrawio--structurizr-2f7ed8?style=for-the-badge&labelColor=555555)](https://github.com/veritas-sovereign/drawio-structurizr#readme)

<br>

🚀 [Quick Start](#quick-start) · 📋 [Diagram Conventions](#diagram-conventions) · ⚠️ [Limitations](#limitations) · 🧪 [Examples](examples/README.md) · 📝 [Changelog](CHANGELOG.md)

<br>

[![License: MIT](https://img.shields.io/badge/License-MIT-c9a227)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9%2B-3776ab?logo=python&logoColor=white)](pyproject.toml)
[![Output](https://img.shields.io/badge/Output-Structurizr%20DSL-438dd5)](https://docs.structurizr.com/dsl)
[![Output](https://img.shields.io/badge/Output-Excel-217346)](#validate-and-export-to-excel)
[![Input](https://img.shields.io/badge/Input-draw.io%20C4-f08705?logo=diagramsdotnet&logoColor=white)](https://www.drawio.com/blog/c4-modelling)
[![Tests](https://github.com/veritas-sovereign/drawio-structurizr/actions/workflows/test.yml/badge.svg)](https://github.com/veritas-sovereign/drawio-structurizr/actions/workflows/test.yml)
[![Last commit](https://img.shields.io/github/last-commit/veritas-sovereign/drawio-structurizr)](https://github.com/veritas-sovereign/drawio-structurizr/commits)

</div>

---

## Overview

`drawio-structurizr` reads C4 diagrams drawn with draw.io's C4 shape library and:

- **checks** them for missing descriptions, technologies and data flow details
- **repairs** arrows that touch a shape without being attached to it
- **converts** them to a [Structurizr DSL](https://docs.structurizr.com/dsl) workspace, with system landscape, container and component views
- **exports** elements and relationships to an Excel workbook

Both compressed and uncompressed `.drawio` files are supported, and every page of a file is read. Several files can be converted into one workspace. An element drawn on several pages or files (for example a context page and a container page) appears once.

## Quick Start

```bash
git clone https://github.com/veritas-sovereign/drawio-structurizr.git
cd drawio-structurizr
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
drawio-structurizr examples/shop.drawio -o shop.dsl
```

Paste `shop.dsl` into the [Structurizr DSL editor](https://structurizr.com/dsl) to see the diagrams.

## Initial setup

### Prerequisites

| Requirement | Version | Needed for |
| --- | --- | --- |
| Python | 3.9 or later | everything |
| git | any | cloning the repository |
| [draw.io](https://www.drawio.com/) desktop or web | any | drawing diagrams |
| [structurizr-cli](https://docs.structurizr.com/cli) | any | optional `--validate` step ([setup](#validating-with-structurizr-cli)) |
| Java | 17 or later | structurizr-cli only |

### Install

1. Clone the repository and enter it:

   ```bash
   git clone https://github.com/veritas-sovereign/drawio-structurizr.git
   cd drawio-structurizr
   ```

2. Create and activate a virtual environment. `.venv/` is already git-ignored.

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate          # Windows: .venv\Scripts\activate
   ```

3. Install the package. Add `[dev]` to also install pytest.

   ```bash
   pip install -e .                   # or: pip install -e '.[dev]'
   ```

4. Check the install:

   ```bash
   drawio-structurizr --help
   ```

5. Optional: install structurizr-cli to validate generated workspaces. See [Validating with structurizr-cli](#validating-with-structurizr-cli) for other platforms and Docker.

   ```bash
   brew install structurizr-cli       # macOS
   ```

To use the code without installing it, run `pip install -r requirements.txt` and prefix commands with `PYTHONPATH=src`.

Once a release is published, you can also install from PyPI with `pip install drawio-structurizr`, or use the [Docker image](#docker), which needs neither Python nor Java.

## Usage

The project provides three commands. Run them from any directory once the package is installed.

### Convert to Structurizr DSL

```bash
drawio-structurizr <input.drawio>... [-o workspace.dsl] [-n NAME] [-s] [-d] [--strict]
                   [--check | --dry-run | --diff] [--validate | --validate-required] [--export FORMAT]... [--export-dir DIR] [--report FILE]
```

| Option | Meaning |
| --- | --- |
| `input` | one or more draw.io files; all pages of all files are merged into one workspace |
| `-o`, `--output` | output DSL file (default `workspace.dsl`) |
| `-n`, `--name` | workspace name (default `Workspace`) |
| `-s`, `--stats` | print element and relationship counts |
| `-d`, `--check-data` | also check that relationships name their input and return data |
| `--strict` | treat warnings as errors too: do not write the output, exit with code 1 |
| `--dry-run` | print the generated DSL to stdout instead of writing it |
| `--check` | only run the checks: write nothing, exit with code 1 if there are problems (used by the [pre-commit hook](#pre-commit-hook)) |
| `--diff` | print a unified diff between the existing output file and the newly generated DSL, without writing |
| `--validate` | check the output with [structurizr-cli](#validating-with-structurizr-cli); skipped if it is not available |
| `--validate-required` | like `--validate`, but if no validator is available, fail before writing anything and list what was checked. Cannot be combined with `--check`, `--dry-run` or `--diff`. |
| `--export FORMAT` | also export the workspace with structurizr-cli; repeatable. `json`, `plantuml`, `plantuml/c4plantuml`, `mermaid`, `dot`, `ilograph`, `websequencediagrams`. Fails if structurizr-cli is not available. |
| `--export-dir DIR` | folder for exported files (default: next to the output file) |
| `--report FILE` | write the problems and element and relationship counts as JSON |

The [checks](#checks) always run. Problems are printed to stderr as a numbered list, each with a code and a severity, for example `[C4-HIER-001] error: …`. **Errors** always stop the output, because Structurizr would reject it; **warnings** stop it only with `--strict`.

Example:

```bash
drawio-structurizr examples/shop.drawio -o shop.dsl -n "Online Shop" -s --validate
drawio-structurizr examples/broken.drawio -d --strict      # 7 problems, exit code 1, nothing written
drawio-structurizr context.drawio containers.drawio -o workspace.dsl   # merge several files
drawio-structurizr examples/shop.drawio -o shop.dsl --diff   # review changes before overwriting
```

Problems, statistics and the "Wrote" line never go to stdout with `--dry-run` or `--diff`, so their output can be redirected to a file or piped.

More examples:

```bash
drawio-structurizr model.drawio -o workspace.dsl --export mermaid --export plantuml/c4plantuml --export-dir diagrams
drawio-structurizr model.drawio --check -d --report report.json
```

`--report` writes:

```json
{
  "inputs": ["model.drawio"],
  "elements": 4,
  "relationships": 2,
  "problemCount": 1,
  "errorCount": 0,
  "warningCount": 1,
  "problems": [
    { "number": 1, "code": "C4-ELEM-002", "severity": "warning", "message": "Container \"Web App\" has no technology" }
  ]
}
```

### Validate and export to Excel

```bash
python -m drawio_structurizr.parser -i <input.drawio> -o <output.xlsx> -d -s
```

| Option | Meaning |
| --- | --- |
| `-i` | draw.io file to read |
| `-o` | Excel file to write elements and relationships to |
| `-d` | also check that relationships name their input and return data |
| `-s` | print element and relationship counts |

Problems are printed as a numbered list. This command also writes `workspace.dsl` to the current directory, using the parser's own DSL exporter.

Example, using the sample that contains deliberate mistakes:

```bash
python -m drawio_structurizr.parser -i examples/broken.drawio -o broken.xlsx -d -s
```

### Dump cell values

```bash
python -m drawio_structurizr.dump -i <input.drawio>
```

Prints the raw cell values of an uncompressed diagram. Useful for debugging.

### Typical workflow

1. Draw the diagram in draw.io with the C4 shapes (see [Diagram conventions](#diagram-conventions)).
2. Review what would change:
   `drawio-structurizr model.drawio -o workspace.dsl --diff`
3. Generate the workspace with every check enforced, and fix what it reports until it succeeds:
   `drawio-structurizr model.drawio -o workspace.dsl -d --strict --validate`
4. In the repository that holds your architecture, commit the `.drawio` file and the generated `workspace.dsl` together.

### Pre-commit hook

This repository is also a [pre-commit](https://pre-commit.com/) hook. In the repository that holds your diagrams, add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/veritas-sovereign/drawio-structurizr
    rev: v0.2.0   # a released tag
    hooks:
      - id: drawio-structurizr-check
        args: [-d]   # optional: also check input and return data
```

The hook runs `drawio-structurizr --check` on the changed `.drawio` files and blocks the commit if any problem is found.

> **Note:** this hook checks **diagrams**, not DSL. It never runs structurizr-cli, so a syntax error in a hand-edited `workspace.dsl` passes it. Add one of the hooks below to validate `.dsl` files too.

**Validate `.dsl` files with Docker** (no Java needed; requires Docker and a published image):

```yaml
  - repo: local
    hooks:
      - id: structurizr-validate
        name: validate Structurizr workspaces
        language: docker_image
        entry: >-
          --entrypoint sh ghcr.io/veritas-sovereign/drawio-structurizr:0.2
          -c 'for f in "$@"; do structurizr-cli validate -workspace "$f" || exit 1; done' --
        files: \.dsl$
```

**Validate `.dsl` files with a local structurizr-cli:**

```yaml
  - repo: local
    hooks:
      - id: structurizr-validate
        name: validate Structurizr workspaces
        language: system
        entry: >-
          sh -c 'for f in "$@"; do structurizr-cli validate -workspace "$f" || exit 1; done' --
        files: \.dsl$
```

structurizr-cli validates one workspace per run, so both hooks loop over the changed files and stop at the first invalid one. With `docker_image`, pre-commit mounts the repository into the container and runs it as your user. Use `structurizr.sh` in place of `structurizr-cli` if you installed the CLI from the zip.

### Docker

The image contains Python, Java and a pinned structurizr-cli (v2025.11.09, checked against its SHA-256), so `--validate` and `--export` work without installing anything else:

```bash
docker run --rm -v "$PWD:/work" ghcr.io/veritas-sovereign/drawio-structurizr:0.2 \
  model.drawio -o workspace.dsl --validate --export mermaid
```

On Linux, add `--user "$(id -u):$(id -g)"`, otherwise the files are written as user 10001.

Images are published to GitHub Container Registry for `linux/amd64` and `linux/arm64` when a `v*` tag is pushed, each with an SBOM (software bill of materials) attached. To build locally: `docker build -t drawio-structurizr .`

#### What is pinned

| Part | Pinned to | Kept up to date by |
| --- | --- | --- |
| Base image | `python:3.12-slim-bookworm` by digest | Dependabot, weekly pull request for a new digest (stays on Python 3.12) |
| structurizr-cli | v2025.11.09 and the SHA-256 of its zip (`ARG` defaults in the `Dockerfile`) | by hand: the upstream project is archived, so no new releases are expected |
| GitHub Actions used by the workflows | major version tags (`@v4`, `@v6`, …) | Dependabot, weekly grouped pull request |
| Java (`default-jre-headless`) and Debian packages | not pinned | whatever Debian bookworm ships when the image is built |

Because Debian packages are not pinned, two builds of the same commit can differ in OS packages. Each published image tag is fixed once pushed, so pull a released tag (or its digest) when you need the exact same toolchain later.

To change the structurizr-cli version, download the new `structurizr-cli.zip`, run `shasum -a 256 structurizr-cli.zip`, and update both `ARG` lines. The build fails if the checksum does not match, including when the upstream file is changed or removed.

## Validating with structurizr-cli

[structurizr-cli](https://docs.structurizr.com/cli) is the official command-line tool for Structurizr DSL workspaces. The `--validate` option uses it to check that the generated `.dsl` file parses and is a valid model.

### Is it free?

Yes. structurizr-cli is open source under the Apache 2.0 license and can be used commercially. `validate` and `export` run entirely on your machine and need no account. Only its `push` and `pull` commands talk to the paid Structurizr cloud service or on-premises server, and this project does not use them.

> **Note:** the upstream repository, [structurizr/cli](https://github.com/structurizr/cli), is archived. The last release is v2025.11.09, which still works. Homebrew has deprecated the formula and will disable it on 2027-02-17; after that, use the manual download or Docker. `--validate` falls back to Docker automatically, so it keeps working without a local install.

### Install

All options except Docker need Java 17 or later. Check with `java -version`.

**macOS (Homebrew):**

```bash
brew install structurizr-cli
structurizr-cli --help
```

**macOS, Linux or Windows (manual download):**

1. Download `structurizr-cli.zip` from the [latest release](https://github.com/structurizr/cli/releases/latest).
2. Unzip it, for example to `~/tools/structurizr-cli`.
3. Add that folder to your `PATH`. On macOS or Linux:

   ```bash
   echo 'export PATH="$HOME/tools/structurizr-cli:$PATH"' >> ~/.zshrc
   source ~/.zshrc
   structurizr.sh --help
   ```

   On Windows, add the folder to `PATH` in System Properties and run `structurizr.bat --help`.

**Docker (no Java needed):**

```bash
docker pull structurizr/cli
docker run --rm -v "$PWD:/usr/local/structurizr" structurizr/cli validate -workspace shop.dsl
```

`--validate` uses this image automatically when no local CLI is installed and Docker is running. The first run downloads the image.

### How `--validate` finds it

`drawio-structurizr` tries these in order and uses the first that is available:

1. A local CLI on `PATH`, named `structurizr-cli`, `structurizr.sh` or `structurizr`:

   ```bash
   <cli> validate -workspace <output.dsl>
   ```

2. Docker, if `docker` is on `PATH` and the Docker daemon is running. The output file's folder is mounted into the container:

   ```bash
   docker run --rm -v <output folder>:/usr/local/structurizr structurizr/cli validate -workspace <output file name>
   ```

3. Neither: validation is skipped.

| Result | What you see | Exit code |
| --- | --- | --- |
| No CLI and Docker not running | `structurizr-cli not found and Docker not running; skipping validation` | 0 |
| No CLI and Docker not running, with `--validate-required` | an error listing what was checked; nothing is written | 1 |
| Workspace is valid | the CLI's output | 0 |
| Workspace is invalid | the CLI's error message | 1 |

The `.dsl` file is written in every case. With `--validate`, a missing validator skips the check rather than failing, so CI jobs without Java or Docker still pass. Use `--validate-required` when validation must happen.

### Run it directly

```bash
structurizr-cli validate -workspace shop.dsl                       # check the workspace
structurizr-cli export -workspace shop.dsl -format plantuml        # export to PlantUML
structurizr-cli export -workspace shop.dsl -format mermaid         # export to Mermaid
```

Use `structurizr.sh` instead of `structurizr-cli` if you installed it manually.

## Diagram conventions

In draw.io, open **More Shapes**, enable **C4**, and build the diagram from those shapes. Shapes from other libraries are ignored unless you give them C4 properties (see [Using shapes from other libraries](#using-shapes-from-other-libraries)).

| C4 shape (`c4Type`) | Structurizr DSL |
| --- | --- |
| Person | `person` |
| Software System | `softwareSystem` |
| Container | `container` |
| Component | `component` |
| SystemScopeBoundary | `softwareSystem` that holds the shapes drawn inside it |
| ContainerScopeBoundary | `container` that holds the shapes drawn inside it |
| Relationship | `->` |

- **Nesting comes from position.** A shape drawn inside another shape's box on the same page becomes its child. If it sits inside several boxes, the smallest one is its parent.
- **The same element on several pages is merged.** Shapes with the same type and name (ignoring case) become one element; a boundary and a software system with the same name count as the same type. Containers and components merge only when their parents also match, so two containers called "API" in different systems stay separate. The first shape found supplies the description and technology; later ones only fill gaps.
- **Attach every arrow** to a shape at both ends. Arrows that only touch a shape are repaired where possible.
- **Relationship descriptions** name the data passed in each direction:

  ```
  action name (passed data): returned data [technologies]
  ```

  For example: `Register order (subscriber, product): order [gRPC]`. Put the technology in the relationship's `c4Technology` field, or end the description with `[technology]`: when `c4Technology` is empty, a trailing `[...]` is moved into it.

  This format is only checked when you pass `-d` to the parser, and only produces warnings. Conversion to DSL works with any description.

### Optional properties

Add these with **Edit Data** on any C4 shape or relationship:

| Property | On | Effect |
| --- | --- | --- |
| `c4Id` | elements | used as the DSL identifier instead of one made from the name, so renaming the element does not change it. Characters other than letters, digits, `_` and `-` become `_`. |
| `c4Tags` | elements and relationships | comma-separated [tags](https://docs.structurizr.com/dsl/language#tags), for styles and filtered views. Tags from merged shapes are combined. |

`c4Id` does not affect merging, which is always by type and name.

### Using shapes from other libraries

The tool reads a shape only if it has a `c4Type` property. Shapes from other libraries (AWS, Azure, Kubernetes, plain boxes) have none and are skipped. You can add the properties to any shape:

1. Select the shape and choose **Edit Data** from the right-click menu (Cmd+M on macOS, Ctrl+M elsewhere).
2. Add these properties, then click **Apply**:

   | Property | Example |
   | --- | --- |
   | `c4Type` | `Container` (or `Person`, `Software System`, `Component`) |
   | `c4Name` | `Order Handler` |
   | `c4Description` | `Processes orders` |
   | `c4Technology` | `AWS Lambda` |

3. The shape keeps its icon and is now converted like a C4 shape.

To avoid repeating this, set up one shape per type, save them to a custom library (**File → New Library**), and draw from that library.

Plain draw.io arrows (not the C4 Relationship shape) are accepted if both ends are attached to C4 shapes. Their label becomes the description, and a trailing `[...]` becomes the technology.

### Checks

| Code | Severity | Check | Applies to |
| --- | --- | --- | --- |
| `C4-HIER-001` | error | A container is drawn inside a software system or system boundary | containers |
| `C4-HIER-002` | error | A component is drawn inside a container or container boundary | components |
| `C4-HIER-003` | error | People and software systems are not drawn inside another element | people, software systems, system boundaries |
| `C4-TYPE-001` | warning | The `c4Type` is one the tool knows; other shapes are skipped | all C4 shapes |
| `C4-ELEM-001` | warning | Description is filled in | elements, except people and boundaries |
| `C4-ELEM-002` | warning | Technology is filled in | containers and components |
| `C4-ELEM-003` | warning | Has at least one relationship, directly or through a parent | elements, except people and boundaries |
| `C4-REL-001` | warning | Technology is filled in | relationships not involving a person |
| `C4-REL-002` | warning | Input data `( … )` is named | relationships not involving a person (with `-d`) |
| `C4-REL-003` | warning | Return data `): …` is named | relationships not involving a person (with `-d`) |
| `C4-REL-004` | warning | Both ends are C4 elements; otherwise the relationship is dropped | relationships |
| `C4-REL-005` | warning | Arrow is attached at both ends or can be repaired; otherwise it is dropped | C4 relationships |

Errors mean Structurizr would reject the output, so nothing is written. The known `c4Type` values are `Person`, `Software System`, `Container`, `Component`, `SystemScopeBoundary` and `ContainerScopeBoundary`.

## Limitations

- **Layout is not preserved.** Structurizr DSL describes the model, not positions, and the generated views use `autoLayout`. Element placement from draw.io does not carry over; only elements, nesting and relationships do. You can arrange the views again in Structurizr after import. Views use Structurizr's default styling; no theme is set, so validation needs no network access.
- **Only C4 properties are read.** Shapes without a `c4Type` are skipped. Diagrams drawn from another template need their shapes updated first (see [Using shapes from other libraries](#using-shapes-from-other-libraries)), or the tool extended: `parser.py` to read the extra shapes and `mapper.py` to map them.
- **Nesting is based on position.** A shape must sit fully inside its parent's box on the same page.
- **Merging is by name.** Two different elements with the same type and name are merged into one. Rename one of them.
- **structurizr-cli is archived upstream.** See [the note above](#is-it-free); Docker keeps `--validate` working.
- **Two DSL exporters.** `python -m drawio_structurizr.parser` still writes `workspace.dsl` with its older exporter. Prefer the `drawio-structurizr` command, whose output this README describes.

## Examples

| File | What it shows |
| --- | --- |
| [`shop.drawio`](examples/shop.drawio) | A clean diagram that passes every check |
| [`shop-compressed.drawio`](examples/shop-compressed.drawio) | The same diagram in compressed format |
| [`multipage.drawio`](examples/multipage.drawio) | A context page and a container page, merged into one workspace; uses `c4Id` and `c4Tags` |
| [`broken.drawio`](examples/broken.drawio) | Seven warnings and one repaired arrow; still produces valid DSL |

## Testing

```bash
pip install -e '.[dev]'
pytest
```

The tests run the samples in `examples/` end to end and cover the mapper and emitter on their own.

## Project structure

```
drawio-structurizr/
├── src/
│   └── drawio_structurizr/      Python package
│       ├── __init__.py          package version
│       ├── main.py              drawio-structurizr command
│       ├── parser.py            reads .drawio files, runs checks, exports Excel and legacy DSL
│       ├── mapper.py            maps C4 shapes to Structurizr DSL constructs
│       ├── emitter.py           writes a .dsl file from the mapped model
│       ├── validate.py          optional structurizr-cli validation
│       └── dump.py              prints the cell values of a diagram
├── examples/
│   ├── README.md                what each sample covers
│   ├── shop.drawio              clean sample
│   ├── shop-compressed.drawio   same sample, compressed
│   ├── multipage.drawio         two pages merged into one workspace
│   └── broken.drawio            sample with deliberate mistakes
├── tests/
│   ├── test_examples.py         end-to-end tests on the samples
│   ├── test_emitter.py          mapper and emitter unit tests
│   └── test_validate.py         choice of local CLI, Docker or skip
├── .github/
│   ├── dependabot.yml           weekly updates for the base image digest and GitHub Actions
│   └── workflows/
│       ├── test.yml             runs pytest on Python 3.9 and 3.13
│       ├── publish-image.yml    builds and smoke-tests the Docker image; pushes it to GHCR on v* tags
│       └── publish-pypi.yml     builds the package; publishes it to PyPI on v* tags
├── Dockerfile                   image with Python, Java and a pinned structurizr-cli, on a digest-pinned base
├── .dockerignore
├── .pre-commit-hooks.yaml       the drawio-structurizr-check pre-commit hook
├── pyproject.toml               package metadata and drawio-structurizr command
├── requirements.txt             runtime dependencies
├── CHANGELOG.md
├── LICENSE
├── .editorconfig
├── .gitattributes
└── .gitignore
```

The package lives under `src/` so it can only be imported once installed, and so it is not mistaken for a second copy of the repository folder.

Output you generate while trying the tool in this repository (`.dsl` files at the top level or in `examples/`, and any `.xlsx`) is git-ignored.

### How a conversion works

```
.drawio ──► parser.py ──► mapper.py ──► emitter.py ──► workspace.dsl ──► validate.py (optional)
             read,          C4 shapes      DSL text                       structurizr-cli
             repair,        to model
             check
```

## Naming conventions

- **Repository, distribution and command:** `drawio-structurizr` (kebab-case)
- **Python package:** `drawio_structurizr` (snake_case), in `src/`
- **Modules:** short snake_case nouns, without a `drawio_` prefix, since the package name already provides it
- **Product name in prose:** "draw.io"; in code and file extensions: `drawio`
- **C4 terms:** element, relationship, software system, container, component, person

## Contributing

Issues and pull requests are welcome at [veritas-sovereign/drawio-structurizr](https://github.com/veritas-sovereign/drawio-structurizr). Run `pytest` before opening a pull request (GitHub Actions runs it too), and add a sample to `examples/` when you change how diagrams are read.

## License

Released under the [MIT License](LICENSE).
