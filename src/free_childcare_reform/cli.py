"""Command-line entry point."""

from __future__ import annotations

import argparse

from .pipeline import YEARS, run


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="free-childcare-reform",
        description=(
            "Cost a universal free childcare reform on the PolicyEngine UK Enhanced FRS, "
            "statically and with an extensive-margin labour supply response."
        ),
    )
    parser.add_argument(
        "--years",
        type=int,
        nargs="+",
        default=None,
        help=f"Years to cost (default: {' '.join(str(year) for year in YEARS)}).",
    )
    run(parser.parse_args())
