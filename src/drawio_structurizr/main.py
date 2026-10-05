"""CLI entry point: draw.io C4 diagram -> Structurizr DSL."""

import argparse
import sys

from . import parser
from .emitter import write
from .mapper import map_diagram
from .validate import validate


def parse_args(argv):
    cli = argparse.ArgumentParser(
        prog="drawio-structurizr",
        description="Convert a C4 draw.io diagram into a Structurizr DSL workspace.",
    )
    cli.add_argument("input", help="input .drawio file (plain or compressed, any number of pages)")
    cli.add_argument("-o", "--output", default="workspace.dsl", help="output .dsl file (default: workspace.dsl)")
    cli.add_argument("-n", "--name", default="Workspace", help="workspace name")
    cli.add_argument("-s", "--stats", action="store_true", help="print diagram statistics")
    cli.add_argument("-d", "--check-data", action="store_true",
                     help="also check that relationships name their input and return data")
    cli.add_argument("--strict", action="store_true",
                     help="treat problems as errors: do not write the output and exit with code 1")
    cli.add_argument("--validate", action="store_true", help="run structurizr-cli validate on the output")
    return cli.parse_args(argv)


def report(problems):
    for i, problem in enumerate(problems, 1):
        print(f"{i}. {problem}", file=sys.stderr)


def main(argv=None):
    args = parse_args(argv)

    components, relations, problems = parser.load_and_check([args.input], args.check_data)
    if args.stats:
        print(f"Number of components: {len(components)}", file=sys.stderr)
        print(f"Number of relations: {len(relations)}", file=sys.stderr)
    report(problems)

    if args.strict and problems:
        print(f"{len(problems)} problem(s) found; {args.output} not written (--strict)", file=sys.stderr)
        return 1

    write(map_diagram(components, relations), args.output, args.name)
    print(f"Wrote {args.output}")

    if args.validate:
        ok, output = validate(args.output)
        if output:
            print(output)
        if ok is False:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
