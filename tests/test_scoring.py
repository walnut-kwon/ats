import pandas as pd
import pytest

from hanta.scoring import DEFAULT_GROUP_WEIGHTS, add_score


def test_add_score_uses_explicit_signal_columns_as_simple_average() -> None:
    df = pd.DataFrame(
        {
            "signal_trend": [1.0, -1.0],
            "signal_momentum": [0.5, -0.5],
        }
    )

    result = add_score(df, signal_columns=["signal_trend", "signal_momentum"])

    assert result["score"].tolist() == [75.0, -75.0]


def test_add_score_adds_group_scores_and_weighted_score() -> None:
    df = pd.DataFrame(
        {
            "signal_ma_slope_5": [1.0, -1.0],
            "signal_ma_slope_20": [0.5, -0.5],
            "signal_ma_alignment_5_20_60": [1.0, -1.0],
            "signal_rsi_14": [0.0, 0.0],
            "signal_macd_histogram_12_26_9": [1.0, -1.0],
            "signal_atr_expansion_14": [1.0, 1.0],
            "signal_bb_percent_b_20_2": [0.0, 0.0],
            "signal_obv_change": [0.5, -0.5],
        }
    )

    result = add_score(df)

    assert result["score_trend"].tolist() == [0.8333333333333334, -0.8333333333333334]
    assert result["score_momentum"].tolist() == [0.5, -0.5]
    assert result["score_volatility"].tolist() == [0.5, 0.5]
    assert result["score_volume"].tolist() == [0.5, -0.5]
    assert result["score"].round(2).tolist() == [61.67, -46.67]


def test_add_score_renormalizes_weights_when_group_score_is_nan() -> None:
    df = pd.DataFrame(
        {
            "signal_ma_slope_20": [1.0],
            "signal_rsi_14": [float("nan")],
        }
    )

    result = add_score(df)

    assert result["score"].tolist() == [100.0]


def test_add_score_falls_back_to_simple_average_when_no_default_groups_match() -> None:
    df = pd.DataFrame({"signal_custom": [1.0, -0.5]})

    result = add_score(df)

    assert result["score"].tolist() == [100.0, -50.0]


def test_add_score_returns_zero_when_no_signals_exist() -> None:
    df = pd.DataFrame({"close": [10.0, 20.0]})

    result = add_score(df)

    assert result["score"].tolist() == [0.0, 0.0]


def test_add_score_accepts_custom_group_weights() -> None:
    df = pd.DataFrame(
        {
            "signal_ma_slope_20": [1.0],
            "signal_rsi_14": [0.0],
        }
    )

    result = add_score(
        df,
        group_weights={**DEFAULT_GROUP_WEIGHTS, "trend": 0.8, "momentum": 0.2},
    )

    assert result["score"].tolist() == [80.0]


def test_add_score_rejects_invalid_group_weight() -> None:
    df = pd.DataFrame({"signal_ma_slope_20": [1.0]})

    with pytest.raises(ValueError, match="group weight must be greater than 0"):
        add_score(df, group_weights={**DEFAULT_GROUP_WEIGHTS, "trend": 0.0})
