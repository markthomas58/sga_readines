from __future__ import annotations

import argparse
import json
import sys

from sga_readiness.checker import run_checks
from sga_readiness.models import CheckStatus

# ANSI color codes
_GREEN = "\033[32m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_CYAN = "\033[36m"
_BOLD = "\033[1m"
_RESET = "\033[0m"

_STATUS_COLORS = {
    CheckStatus.PASS: _GREEN,
    CheckStatus.FAIL: _RED,
    CheckStatus.WARN: _YELLOW,
    CheckStatus.SKIP: _CYAN,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sga-readiness",
        description="Service/infrastructure readiness assessment tool",
    )
    sub = parser.add_subparsers(dest="command")

    check_parser = sub.add_parser("check", help="Run readiness checks")
    check_parser.add_argument(
        "--config",
        default="readiness.yaml",
        help="Path to readiness config file (default: readiness.yaml)",
    )
    check_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    check_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed check output",
    )

    args = parser.parse_args(argv)

    if args.command != "check":
        parser.print_help()
        return 1

    try:
        report = run_checks(args.config)
    except (FileNotFoundError, ValueError) as e:
        print(f"{_RED}Error: {e}{_RESET}", file=sys.stderr)
        return 1

    if args.format == "json":
        _print_json(report)
    else:
        _print_text(report, verbose=args.verbose)

    return 0 if report.passed else 1


def _print_text(report, *, verbose: bool = False) -> None:
    for result in report.results:
        color = _STATUS_COLORS.get(result.status, _RESET)
        status = f"[{result.status.value}]"
        line = f"  {color}{status:6s}{_RESET} {result.name}"
        if verbose:
            line += f"  ({result.duration_ms:.0f}ms)"
            if result.message:
                line += f" — {result.message}"
        print(line)

    print()
    color = _GREEN if report.passed else _RED
    print(f"{_BOLD}{color}{report.summary()}{_RESET}")


def _print_json(report) -> None:
    data = {
        "passed": report.passed,
        "summary": report.summary(),
        "results": [
            {
                "name": r.name,
                "status": r.status.value,
                "message": r.message,
                "duration_ms": round(r.duration_ms, 2),
            }
            for r in report.results
        ],
    }
    print(json.dumps(data, indent=2))


def cli() -> None:
    sys.exit(main())


if __name__ == "__main__":
    cli()
