"""CLI entry point: draw.io C4 diagrams -> one Structurizr DSL workspace."""

import argparse
import difflib
import json
import os
import sys

from . import parser
from .emitter import emit
from .mapper import map_diagram
from .validate import EXPORT_FORMATS, export, validate


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
                     help="treat warnings as errors too: do not write the output and exit with code 1")
    preview = cli.add_mutually_exclusive_group()
    preview.add_argument("--check", action="store_true",
                         help="only run the checks: write nothing, exit with code 1 if there are problems")
    preview.add_argument("--dry-run", action="store_true",
                         help="print the generated DSL instead of writing it")
    preview.add_argument("--diff", action="store_true",
                         help="print a unified diff against the existing output file instead of writing it")
    cli.add_argument("--validate", action="store_true", help="run structurizr-cli validate on the output")
    cli.add_argument("--export", action="append", default=[], choices=EXPORT_FORMATS, metavar="FORMAT",
                     help="also export the workspace with structurizr-cli; repeatable. "
                          "One of: " + ", ".join(EXPORT_FORMATS))
    cli.add_argument("--export-dir", help="folder for exported files (default: next to the output file)")
    cli.add_argument("--report", metavar="FILE", help="write the checks and statistics as JSON to FILE")
    return cli.parse_args(argv)


def report(problems):
    for i, problem in enumerate(problems, 1):
        print(f"{i}. {problem}", file=sys.stderr)


def write_report(path, inputs, components, relations, problems):
    data = {
        "inputs": inputs,
        "elements": len(components),
        "relationships": len(relations),
        "problemCount": len(problems),
        "errorCount": sum(p.severity == "error" for p in problems),
        "warningCount": sum(p.severity == "warning" for p in problems),
        "problems": [{"number": i, **problem.as_dict()} for i, problem in enumerate(problems, 1)],
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def main(argv=None):
    args = parse_args(argv)

    components, relations, problems = parser.load_and_check(args.inputs, args.check_data)
    if args.stats:
        print(f"Number of components: {len(components)}", file=sys.stderr)
        print(f"Number of relations: {len(relations)}", file=sys.stderr)
    report(problems)
    if args.report:
        write_report(args.report, args.inputs, components, relations, problems)

    if args.check:
        return 1 if problems else 0
    errors = [p for p in problems if p.severity == "error"]
    if errors:
        print(f"{len(errors)} error(s) found; {args.output} not written", file=sys.stderr)
        return 1
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

    status = 0
    if args.validate:  # not reached with --check, --dry-run or --diff
        ok, output = validate(args.output)
        if output:
            print(output)
        if ok is False:
            status = 1

    export_dir = args.export_dir or os.path.dirname(os.path.abspath(args.output))
    for fmt in args.export:
        ok, output = export(args.output, fmt, export_dir)
        if output:
            print(output)
        if ok is not True:
            status = 1
        else:
            print(f"Exported {fmt} to {export_dir}")
    return status


if __name__ == "__main__":
    sys.exit(main())
