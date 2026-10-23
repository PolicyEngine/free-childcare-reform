"""Command-line entry point."""

from __future__ import annotations

import argparse

from .pipeline import YEARS, run


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="free-childcare-reform",
        description=(
            "Cost a universal free childcare reform on PolicyEngine UK Microcosm, "
            "statically and with a labour supply response on both the participation and "
            "hours margins."
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
