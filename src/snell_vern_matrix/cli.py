"""
CLI entry-point for the Snell-Vern Hybrid Drive Matrix.

Provides subcommands for interacting with the SelfModel and DriveMatrix
from the command line.  Follows existing rfm CLI patterns.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional, Sequence

from .self_model import ConstraintViolation, SelfModel


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="snell-vern",
        description="Snell-Vern Hybrid Drive Matrix CLI",
    )
    sub = parser.add_subparsers(dest="command")

    # -- self-model subcommand ---------------------------------------------
    sm = sub.add_parser(
        "self-model",
        help="Interact with the sentience seed self-model",
    )
    group = sm.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--observe",
        metavar="INPUT",
        help="Observe a symbolic input pattern (string or JSON)",
    )
    group.add_argument(
        "--ask",
        action="store_true",
        help="Ask the model if it needs more data",
    )
    group.add_argument(
        "--integrate",
        metavar="JSON_DATA",
        help="Integrate new data (JSON dict) into the model",
    )
    group.add_argument(
        "--state",
        action="store_true",
        help="Print current model state as JSON",
    )

    return parser


def _run_self_model(args: argparse.Namespace) -> int:
    model = SelfModel()

    if args.observe is not None:
        result = model.observe(args.observe)
        print(json.dumps(result, sort_keys=True))
        return 0

    if args.ask:
        query = model.ask()
        if query is None:
            print("null")
        else:
            print(json.dumps(query, sort_keys=True))
        return 0

    if args.integrate is not None:
        try:
            data = json.loads(args.integrate)
        except json.JSONDecodeError as exc:
            print(f"error: invalid JSON: {exc}", file=sys.stderr)
            return 1
        try:
            result = model.integrate(data)
            # Serialise PhaseState enum for JSON output
            output = dict(result)
            output["phase_state"] = output["phase_state"].value
            output["ternary_balance"] = list(output["ternary_balance"])
            print(json.dumps(output, sort_keys=True))
            return 0
        except (ConstraintViolation, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    if args.state:
        state = model.state
        state["phase_state"] = state["phase_state"].value
        state["ternary_balance"] = list(state["ternary_balance"])
        print(json.dumps(state, sort_keys=True))
        return 0

    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry-point.  Returns exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "self-model":
        return _run_self_model(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
