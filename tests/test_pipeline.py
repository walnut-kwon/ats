from pathlib import Path

import pandas as pd

from hanta.cli import summarize_analysis, summarize_backtest_rows
from hanta.pipeline import analyze_csv, analyze_ohlcv


def test_analyze_ohlcv_runs_full_pipeline() -> None:
    df = pd.DataFrame(
        {
            "date": pd.date_range("2025-01-01", periods=80, freq="D"),
            "open": range(100, 180),
            "high": range(102, 182),
            "low": range(99, 179),
            "close": range(101, 181),
            "volume": range(1000, 1080),
        }
    )

    result = analyze_ohlcv(df)

    assert "rsi_14" in result.columns
    assert "signal_rsi_14" in result.columns
    assert "score" in result.columns


def test_analyze_csv_can_write_output(tmp_path: Path) -> None:
    input_path = Path("data/sample/sample_ohlcv.csv")
    output_path = tmp_path / "analysis.csv"

    result = analyze_csv(input_path, output_path=output_path)
    written = pd.read_csv(output_path)

    assert output_path.exists()
    assert len(result) == len(written)
    assert "score" in written.columns


def test_summarize_analysis_returns_human_readable_columns() -> None:
    result = analyze_csv("data/sample/sample_ohlcv.csv")

    summary = summarize_analysis(result)

    assert summary.columns.tolist() == [
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
    ]


def test_summarize_backtest_rows_returns_human_readable_columns() -> None:
    df = pd.DataFrame(
        {
            "date": ["2025-01-01"],
            "close": [100.0],
            "score": [30.0],
            "target_position": [0.3],
            "position": [0.0],
            "asset_return": [0.0],
            "strategy_return": [0.0],
            "cumulative_strategy_return": [0.0],
            "drawdown": [0.0],
            "extra": [1.0],
        }
    )

    summary = summarize_backtest_rows(df)

    assert summary.columns.tolist() == [
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
