"""CLI entry point: draw.io C4 diagrams -> one Structurizr DSL workspace."""

import argparse
import difflib
import os
import sys

from . import parser
from .emitter import emit
from .mapper import map_diagram
from .validate import validate


def parse_args(argv):
    cli = argparse.ArgumentParser(
        prog="drawio-structurizr",
        description="Convert C4 draw.io diagrams into one Structurizr DSL workspace.",
    )
    cli.add_argument("inputs", nargs="+", metavar="input",
                     help="input .drawio files (plain or compressed, any number of pages), merged into one workspace")
    cli.add_argument("-o", "--output", default="workspace.dsl", help="output .dsl file (default: workspace.dsl)")
    cli.add_argument("-n", "--name", default="Workspace", help="workspace name")
    cli.add_argument("-s", "--stats", action="store_true", help="print diagram statistics")
    cli.add_argument("-d", "--check-data", action="store_true",
                     help="also check that relationships name their input and return data")
    cli.add_argument("--strict", action="store_true",
                     help="treat problems as errors: do not write the output and exit with code 1")
    preview = cli.add_mutually_exclusive_group()
    preview.add_argument("--dry-run", action="store_true",
                         help="print the generated DSL instead of writing it")
    preview.add_argument("--diff", action="store_true",
                         help="print a unified diff against the existing output file instead of writing it")
    cli.add_argument("--validate", action="store_true", help="run structurizr-cli validate on the output")
    return cli.parse_args(argv)


def report(problems):
    for i, problem in enumerate(problems, 1):
        print(f"{i}. {problem}", file=sys.stderr)


def main(argv=None):
    args = parse_args(argv)

    components, relations, problems = parser.load_and_check(args.inputs, args.check_data)
    if args.stats:
        print(f"Number of components: {len(components)}", file=sys.stderr)
        print(f"Number of relations: {len(relations)}", file=sys.stderr)
    report(problems)

    if args.strict and problems:
        print(f"{len(problems)} problem(s) found; {args.output} not written (--strict)", file=sys.stderr)
        return 1

    dsl = emit(map_diagram(components, relations), args.name)

    if args.dry_run:
        sys.stdout.write(dsl)
        return 0
    if args.diff:
        old = ""
        if os.path.exists(args.output):
            with open(args.output, encoding="utf-8") as fh:
                old = fh.read()
        sys.stdout.writelines(difflib.unified_diff(
            old.splitlines(keepends=True), dsl.splitlines(keepends=True),
            fromfile=args.output, tofile=f"{args.output} (generated)"))
        return 0

    with open(args.output, "w", encoding="utf-8") as fh:
        fh.write(dsl)
    print(f"Wrote {args.output}")

    if args.validate:  # not reached with --dry-run or --diff
        ok, output = validate(args.output)
        if output:
            print(output)
        if ok is False:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
