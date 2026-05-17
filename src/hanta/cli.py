from __future__ import annotations

import argparse
from pathlib import Path

from hanta.backtest import add_backtest_columns, summarize_backtest
from hanta.pipeline import analyze_csv

SUMMARY_COLUMNS = (
    "date",
    "close",
    "score",
    "score_trend",
    "score_momentum",
    "score_volatility",
    "score_volume",
    "signal_ma_alignment_5_20_60",
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

    backtest_parser = subparsers.add_parser("backtest", help="backtest an OHLCV CSV file")
    backtest_parser.add_argument("input", type=Path, help="input OHLCV CSV path")
    backtest_parser.add_argument(
        "--tail",
        type=int,
        default=5,
        help="number of trailing rows to print",
    )
    backtest_parser.add_argument(
        "--threshold",
        type=float,
        default=30.0,
        help="score where position reaches threshold-position",
    )
    backtest_parser.add_argument(
        "--threshold-position",
        type=float,
        default=0.3,
        help="target position at threshold score",
    )
    backtest_parser.add_argument(
        "--max-position",
        type=float,
        default=1.0,
        help="maximum long exposure",
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

    if args.command == "backtest":
        result = add_backtest_columns(
            analyze_csv(args.input),
            threshold=args.threshold,
            threshold_position=args.threshold_position,
            max_position=args.max_position,
        )
        print(_format_backtest_summary(summarize_backtest(result)))
        print()
        print(summarize_backtest_rows(result).tail(args.tail).to_string(index=False))
        return

    parser.print_help()


def summarize_analysis(df):
    """Return the default human-readable analysis columns."""
    columns = [column for column in SUMMARY_COLUMNS if column in df.columns]
    return df[columns]


def summarize_backtest_rows(df):
    """Return the default human-readable backtest columns."""
    columns = [
        "date",
        "close",
        "score",
        "target_position",
        "position",
        "asset_return",
        "strategy_return",
        "cumulative_strategy_return",
        "drawdown",
    ]
    return df[[column for column in columns if column in df.columns]]


def _format_backtest_summary(summary):
    lines = ["Backtest summary"]
    for key, value in summary.items():
        lines.append(f"{key}: {value:.4f}")
    return "\n".join(lines)
