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
    cli.add_argument("input", help="input .drawio file (plain or compressed)")
    cli.add_argument("-o", "--output", default="workspace.dsl", help="output .dsl file (default: workspace.dsl)")
    cli.add_argument("-n", "--name", default="Workspace", help="workspace name")
    cli.add_argument("-s", "--stats", action="store_true", help="print diagram statistics")
    cli.add_argument("--validate", action="store_true", help="run structurizr-cli validate on the output")
    return cli.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    components, relations, broken = parser.load_from_xml(args.input, args.stats)
    components = parser.fill_parent_id(components)
    relations = parser.fix_broken_relations(components, relations, broken)
    relations = parser.fix_missing_relations(components, relations)

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
