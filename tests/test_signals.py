import math

import pandas as pd
import pytest

from hanta.signals import (
    add_signals,
    atr_expansion_signal,
    percent_b_signal,
    robust_change_signal,
    rsi_signal,
    zscore_signal,
)


def test_rsi_signal_centers_around_50() -> None:
    series = pd.Series([0.0, 30.0, 50.0, 70.0, 100.0])

    result = rsi_signal(series)

    assert result.tolist() == [-1.0, -0.4, 0.0, 0.4, 1.0]


def test_percent_b_signal_centers_around_middle_band() -> None:
    series = pd.Series([-0.25, 0.0, 0.5, 1.0, 1.25])

    result = percent_b_signal(series)

    assert result.tolist() == [-1.0, -1.0, 0.0, 1.0, 1.0]


def test_zscore_signal_scales_and_clips_rolling_zscore() -> None:
    series = pd.Series([10.0, 12.0, 14.0, 16.0])

    result = zscore_signal(series, window=3, scale=2.0)

    assert math.isnan(result.iloc[0])
    assert math.isnan(result.iloc[1])
    assert result.iloc[2:].round(4).tolist() == [0.6124, 0.6124]


def test_robust_change_signal_uses_robust_score_of_changes() -> None:
    series = pd.Series([10.0, 12.0, 11.0, 15.0, 16.0])

    result = robust_change_signal(series, window=3, scale=2.0)

    assert math.isnan(result.iloc[0])
    assert math.isnan(result.iloc[1])
    assert math.isnan(result.iloc[2])
    assert result.iloc[3:].round(4).tolist() == [0.4, 0.0]


def test_atr_expansion_signal_starts_at_neutral_and_caps_at_one() -> None:
    atr = pd.Series([10.0, 10.0, 10.0, 15.0, 30.0])

    result = atr_expansion_signal(atr, window=3, threshold=1.5)

    assert math.isnan(result.iloc[0])
    assert math.isnan(result.iloc[1])
    assert result.iloc[2:].round(4).tolist() == [0.0, 0.5714, 1.0]


def test_add_signals_adds_default_signal_columns() -> None:
    df = pd.DataFrame(
        {
            "ma_slope_5": list(range(1, 41)),
            "rsi_14": [50.0] * 40,
            "macd_histogram_12_26_9": list(range(-20, 20)),
            "atr_14": [10.0] * 30 + [15.0] * 10,
            "bb_percent_b_20_2": [0.5] * 40,
            "obv": list(range(100, 140)),
        }
    )

    result = add_signals(df, zscore_window=5, atr_window=5, obv_window=5)

    assert "signal_ma_slope_5" in result.columns
    assert "signal_rsi_14" in result.columns
    assert "signal_macd_histogram_12_26_9" in result.columns
    assert "signal_atr_expansion_14" in result.columns
    assert "signal_bb_percent_b_20_2" in result.columns
    assert "signal_obv_change" in result.columns
    assert result["signal_rsi_14"].dropna().eq(0.0).all()
    assert result["signal_bb_percent_b_20_2"].dropna().eq(0.0).all()


def test_zscore_signal_rejects_invalid_scale() -> None:
    series = pd.Series([1.0])

    with pytest.raises(ValueError, match="scale must be greater than 0"):
        zscore_signal(series, scale=0.0)


def test_robust_change_signal_rejects_invalid_scale() -> None:
    series = pd.Series([1.0])

    with pytest.raises(ValueError, match="scale must be greater than 0"):
        robust_change_signal(series, scale=0.0)


def test_atr_expansion_signal_rejects_invalid_threshold() -> None:
    atr = pd.Series([1.0])

    with pytest.raises(ValueError, match="threshold must be greater than 1"):
        atr_expansion_signal(atr, threshold=1.0)
