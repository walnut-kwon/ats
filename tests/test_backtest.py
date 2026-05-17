import pandas as pd
import pytest

from hanta.backtest import (
    add_backtest_columns,
    add_forward_return,
    summarize_backtest,
    thresholded_linear_position,
)


def test_add_forward_return_adds_requested_period_return() -> None:
    df = pd.DataFrame({"close": [100.0, 110.0, 121.0]})

    result = add_forward_return(df, periods=1)

    assert result["forward_return_1"].round(4).tolist()[:2] == [0.1, 0.1]


def test_thresholded_linear_position_scales_long_only_exposure() -> None:
    score = pd.Series([-20.0, 0.0, 15.0, 30.0, 65.0, 100.0, 150.0])

    result = thresholded_linear_position(score)

    assert result.round(4).tolist() == [0.0, 0.0, 0.15, 0.3, 0.65, 1.0, 1.0]


def test_add_backtest_columns_uses_prior_day_position() -> None:
    df = pd.DataFrame(
        {
            "close": [100.0, 110.0, 99.0, 108.9],
            "score": [0.0, 30.0, 100.0, 0.0],
        }
    )

    result = add_backtest_columns(df)

    assert result["target_position"].tolist() == [0.0, 0.3, 1.0, 0.0]
    assert result["position"].tolist() == [0.0, 0.0, 0.3, 1.0]
    assert result["asset_return"].round(4).tolist() == [0.0, 0.1, -0.1, 0.1]
    assert result["strategy_return"].round(4).tolist() == [0.0, 0.0, -0.03, 0.1]
    assert result["cumulative_strategy_return"].round(4).tolist() == [
        0.0,
        0.0,
        -0.03,
        0.067,
    ]
    assert result["drawdown"].round(4).tolist() == [0.0, 0.0, -0.03, 0.0]


def test_summarize_backtest_returns_compact_metrics() -> None:
    result = add_backtest_columns(
        pd.DataFrame(
            {
                "close": [100.0, 110.0, 99.0, 108.9],
                "score": [0.0, 30.0, 100.0, 0.0],
            }
        )
    )

    summary = summarize_backtest(result)

    assert round(summary["strategy_total_return"], 4) == 0.067
    assert round(summary["benchmark_total_return"], 4) == 0.089
    assert round(summary["max_drawdown"], 4) == -0.03
    assert round(summary["win_rate"], 4) == 0.5
    assert round(summary["average_position"], 4) == 0.325
    assert round(summary["exposure"], 4) == 0.5


def test_thresholded_linear_position_rejects_invalid_thresholds() -> None:
    with pytest.raises(ValueError, match="position thresholds must satisfy"):
        thresholded_linear_position(pd.Series([1.0]), threshold=0.0)


def test_thresholded_linear_position_rejects_invalid_positions() -> None:
    with pytest.raises(ValueError, match="positions must satisfy"):
        thresholded_linear_position(pd.Series([1.0]), threshold_position=1.1)


def test_add_backtest_columns_rejects_missing_columns() -> None:
    with pytest.raises(ValueError, match="Missing required columns: score"):
        add_backtest_columns(pd.DataFrame({"close": [100.0]}), score_column="score")
