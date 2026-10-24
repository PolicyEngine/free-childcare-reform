"""Command-line entry point."""

from __future__ import annotations

import argparse

from .pipeline import YEARS, fold_quintiles_into_results, run


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
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Cost each year in its own process and merge the results at write time.",
    )
    parser.add_argument(
        "--fold-quintiles",
        action="store_true",
        help=(
            "Add the quintile breakdowns to existing results by folding their "
            "decile rows, without rerunning."
        ),
    )
    args = parser.parse_args()
    if args.fold_quintiles:
        fold_quintiles_into_results()
        return
    run(args)
