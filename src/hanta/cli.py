from __future__ import annotations

import argparse
from pathlib import Path

from hanta.pipeline import analyze_csv

SUMMARY_COLUMNS = (
    "date",
    "close",
    "score",
    "score_trend",
    "score_momentum",
    "score_volatility",
    "score_volume",
    "signal_ma_slope_20",
    "signal_rsi_14",
    "signal_macd_histogram_12_26_9",
    "signal_atr_expansion_14",
    "signal_bb_percent_b_20_2",
    "signal_obv_change",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hanta research toolkit")
    parser.add_argument("--version", action="store_true", help="show package version")
    subparsers = parser.add_subparsers(dest="command")

    analyze_parser = subparsers.add_parser("analyze", help="analyze an OHLCV CSV file")
    analyze_parser.add_argument("input", type=Path, help="input OHLCV CSV path")
    analyze_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="optional output CSV path",
    )
    analyze_parser.add_argument(
        "--tail",
        type=int,
        default=5,
        help="number of trailing rows to print",
    )
    analyze_parser.add_argument(
        "--full",
        action="store_true",
        help="print all analysis columns instead of the summary view",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.version:
        from hanta import __version__

        print(__version__)
        return

    if args.command == "analyze":
        result = analyze_csv(args.input, output_path=args.output)
        display = result if args.full else summarize_analysis(result)
        print(display.tail(args.tail).to_string(index=False))
        return

    parser.print_help()


def summarize_analysis(df):
    """Return the default human-readable analysis columns."""
    columns = [column for column in SUMMARY_COLUMNS if column in df.columns]
    return df[columns]
