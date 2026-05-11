import math

import pandas as pd
import pytest

from ats.indicators import (
    add_candle_indicators,
    add_indicators,
    add_momentum_indicators,
    add_moving_average_indicators,
    add_volume_indicators,
    add_volatility_indicators,
    average_true_range,
    bollinger_bands,
    candle_ratios,
    exponential_moving_average,
    moving_average_convergence_divergence,
    moving_average_slope,
    on_balance_volume,
    relative_strength_index,
    simple_moving_average,
    true_range,
)


def test_simple_moving_average_uses_full_window() -> None:
    series = pd.Series([10.0, 20.0, 30.0, 40.0])

    result = simple_moving_average(series, window=3)

    assert math.isnan(result.iloc[0])
    assert math.isnan(result.iloc[1])
    assert result.iloc[2:].tolist() == [20.0, 30.0]


def test_exponential_moving_average_uses_expected_span() -> None:
    series = pd.Series([10.0, 20.0, 30.0, 40.0])

    result = exponential_moving_average(series, span=3)

    assert math.isnan(result.iloc[0])
    assert math.isnan(result.iloc[1])
    assert result.iloc[2:].tolist() == [22.5, 31.25]


def test_moving_average_slope_returns_per_period_change() -> None:
    series = pd.Series([10.0, 12.0, 14.0, 20.0])

    result = moving_average_slope(series, window=2)

    assert math.isnan(result.iloc[0])
    assert math.isnan(result.iloc[1])
    assert result.iloc[2:].tolist() == [2.0, 4.0]


def test_relative_strength_index_simple_uses_rolling_window() -> None:
    series = pd.Series([10.0, 11.0, 10.0, 12.0, 11.0])

    result = relative_strength_index(series, window=3, method="simple")

    assert math.isnan(result.iloc[0])
    assert math.isnan(result.iloc[1])
    assert math.isnan(result.iloc[2])
    assert result.iloc[3:].round(2).tolist() == [75.0, 50.0]


def test_relative_strength_index_wilder_smooths_previous_values() -> None:
    series = pd.Series([10.0, 11.0, 10.0, 12.0, 11.0])

    result = relative_strength_index(series, window=3, method="wilder")

    assert math.isnan(result.iloc[0])
    assert math.isnan(result.iloc[1])
    assert math.isnan(result.iloc[2])
    assert result.iloc[3:].round(2).tolist() == [75.0, 54.55]


def test_relative_strength_index_handles_all_gain_and_all_loss() -> None:
    rising = pd.Series([10.0, 11.0, 12.0, 13.0])
    falling = pd.Series([13.0, 12.0, 11.0, 10.0])

    rising_result = relative_strength_index(rising, window=3)
    falling_result = relative_strength_index(falling, window=3)

    assert rising_result.iloc[3] == 100.0
    assert falling_result.iloc[3] == 0.0


def test_relative_strength_index_handles_flat_prices() -> None:
    series = pd.Series([10.0, 10.0, 10.0, 10.0])

    result = relative_strength_index(series, window=3)

    assert result.iloc[3] == 50.0


def test_moving_average_convergence_divergence_adds_expected_columns() -> None:
    series = pd.Series([10.0, 11.0, 12.0, 11.0, 13.0, 14.0])

    result = moving_average_convergence_divergence(series, fast=2, slow=3, signal=2)

    assert result.columns.tolist() == [
        "macd_2_3_2",
        "macd_signal_2_3_2",
        "macd_histogram_2_3_2",
    ]
    assert math.isnan(result["macd_2_3_2"].iloc[0])
    assert math.isnan(result["macd_2_3_2"].iloc[1])
    assert result["macd_2_3_2"].iloc[2:].round(4).tolist() == [
        0.3056,
        0.0602,
        0.3326,
        0.4338,
    ]
    assert result["macd_signal_2_3_2"].iloc[3:].round(4).tolist() == [
        0.142,
        0.269,
        0.3789,
    ]
    assert result["macd_histogram_2_3_2"].iloc[3:].round(4).tolist() == [
        -0.0818,
        0.0635,
        0.0549,
    ]


def test_true_range_uses_intraday_and_gap_ranges() -> None:
    df = pd.DataFrame(
        {
            "high": [12.0, 15.0, 13.0],
            "low": [9.0, 11.0, 8.0],
            "close": [10.0, 14.0, 9.0],
        }
    )

    result = true_range(df)

    assert result.tolist() == [3.0, 5.0, 6.0]


def test_average_true_range_simple_uses_rolling_average() -> None:
    df = pd.DataFrame(
        {
            "high": [12.0, 15.0, 13.0, 14.0],
            "low": [9.0, 11.0, 8.0, 12.0],
            "close": [10.0, 14.0, 9.0, 13.0],
        }
    )

    result = average_true_range(df, window=3, method="simple")

    assert math.isnan(result.iloc[0])
    assert math.isnan(result.iloc[1])
    assert result.iloc[2:].round(2).tolist() == [4.67, 5.33]


def test_average_true_range_wilder_smooths_previous_values() -> None:
    df = pd.DataFrame(
        {
            "high": [12.0, 15.0, 13.0, 14.0],
            "low": [9.0, 11.0, 8.0, 12.0],
            "close": [10.0, 14.0, 9.0, 13.0],
        }
    )

    result = average_true_range(df, window=3, method="wilder")

    assert math.isnan(result.iloc[0])
    assert math.isnan(result.iloc[1])
    assert result.iloc[2:].round(2).tolist() == [4.67, 4.78]


def test_bollinger_bands_uses_population_std_by_default() -> None:
    series = pd.Series([10.0, 12.0, 14.0, 16.0])

    result = bollinger_bands(series, window=3, multiplier=2.0)

    assert result.columns.tolist() == [
        "bb_middle_3_2",
        "bb_upper_3_2",
        "bb_lower_3_2",
        "bb_bandwidth_3_2",
        "bb_percent_b_3_2",
    ]
    assert math.isnan(result["bb_middle_3_2"].iloc[0])
    assert math.isnan(result["bb_middle_3_2"].iloc[1])
    assert result["bb_middle_3_2"].iloc[2:].round(4).tolist() == [12.0, 14.0]
    assert result["bb_upper_3_2"].iloc[2:].round(4).tolist() == [15.266, 17.266]
    assert result["bb_lower_3_2"].iloc[2:].round(4).tolist() == [8.734, 10.734]
    assert result["bb_bandwidth_3_2"].iloc[2:].round(4).tolist() == [0.5443, 0.4666]
    assert result["bb_percent_b_3_2"].iloc[2:].round(4).tolist() == [0.8062, 0.8062]


def test_bollinger_bands_formats_decimal_multiplier_in_columns() -> None:
    series = pd.Series([10.0, 12.0, 14.0])

    result = bollinger_bands(series, window=3, multiplier=1.5)

    assert "bb_middle_3_1_5" in result.columns
    assert "bb_percent_b_3_1_5" in result.columns


def test_on_balance_volume_accumulates_signed_volume() -> None:
    close = pd.Series([10.0, 11.0, 11.0, 9.0, 12.0])
    volume = pd.Series([100.0, 200.0, 300.0, 400.0, 500.0])

    result = on_balance_volume(close, volume)

    assert result.tolist() == [0.0, 200.0, 200.0, -200.0, 300.0]


def test_candle_ratios_breaks_candle_into_body_and_shadows() -> None:
    df = pd.DataFrame(
        {
            "open": [10.0, 14.0],
            "high": [15.0, 16.0],
            "low": [9.0, 10.0],
            "close": [13.0, 11.0],
        }
    )

    result = candle_ratios(df)

    assert result.columns.tolist() == [
        "candle_body_ratio",
        "candle_upper_shadow_ratio",
        "candle_lower_shadow_ratio",
    ]
    assert result["candle_body_ratio"].round(4).tolist() == [0.5, 0.5]
    assert result["candle_upper_shadow_ratio"].round(4).tolist() == [0.3333, 0.3333]
    assert result["candle_lower_shadow_ratio"].round(4).tolist() == [0.1667, 0.1667]


def test_candle_ratios_uses_nan_for_zero_range_candles() -> None:
    df = pd.DataFrame(
        {
            "open": [10.0],
            "high": [10.0],
            "low": [10.0],
            "close": [10.0],
        }
    )

    result = candle_ratios(df)

    assert math.isnan(result["candle_body_ratio"].iloc[0])
    assert math.isnan(result["candle_upper_shadow_ratio"].iloc[0])
    assert math.isnan(result["candle_lower_shadow_ratio"].iloc[0])


def test_add_moving_average_indicators_adds_named_columns() -> None:
    df = pd.DataFrame({"close": [10.0, 20.0, 30.0, 40.0]})

    result = add_moving_average_indicators(df, windows=(2,))

    assert "sma_2" in result.columns
    assert "ema_2" in result.columns
    assert "ma_slope_2" in result.columns
    assert result["sma_2"].iloc[1:].tolist() == [15.0, 25.0, 35.0]


def test_add_momentum_indicators_adds_rsi_column() -> None:
    df = pd.DataFrame({"close": [10.0, 11.0, 10.0, 12.0, 11.0]})

    result = add_momentum_indicators(
        df,
        rsi_window=3,
        rsi_method="simple",
        macd_fast=2,
        macd_slow=3,
        macd_signal=2,
    )

    assert "rsi_3" in result.columns
    assert "macd_2_3_2" in result.columns
    assert "macd_signal_2_3_2" in result.columns
    assert "macd_histogram_2_3_2" in result.columns
    assert result["rsi_3"].iloc[3:].round(2).tolist() == [75.0, 50.0]


def test_add_volatility_indicators_adds_true_range_and_atr() -> None:
    df = pd.DataFrame(
        {
            "high": [12.0, 15.0, 13.0, 14.0],
            "low": [9.0, 11.0, 8.0, 12.0],
            "close": [10.0, 14.0, 9.0, 13.0],
        }
    )

    result = add_volatility_indicators(df, atr_window=3, atr_method="simple")

    assert "true_range" in result.columns
    assert "atr_3" in result.columns
    assert "bb_middle_20_2" in result.columns
    assert "bb_percent_b_20_2" in result.columns
    assert result["atr_3"].iloc[2:].round(2).tolist() == [4.67, 5.33]


def test_add_volume_indicators_adds_obv() -> None:
    df = pd.DataFrame(
        {
            "close": [10.0, 11.0, 11.0, 9.0, 12.0],
            "volume": [100.0, 200.0, 300.0, 400.0, 500.0],
        }
    )

    result = add_volume_indicators(df)

    assert "obv" in result.columns
    assert result["obv"].tolist() == [0.0, 200.0, 200.0, -200.0, 300.0]


def test_add_candle_indicators_adds_candle_ratio_columns() -> None:
    df = pd.DataFrame(
        {
            "open": [10.0],
            "high": [15.0],
            "low": [9.0],
            "close": [13.0],
        }
    )

    result = add_candle_indicators(df)

    assert "candle_body_ratio" in result.columns
    assert "candle_upper_shadow_ratio" in result.columns
    assert "candle_lower_shadow_ratio" in result.columns
    assert result["candle_body_ratio"].iloc[0] == 0.5


def test_add_indicators_adds_default_moving_average_columns() -> None:
    df = pd.DataFrame(
        {
            "open": list(range(1, 81)),
            "high": list(range(2, 82)),
            "low": list(range(0, 80)),
            "close": list(range(1, 81)),
            "volume": list(range(100, 180)),
        }
    )

    result = add_indicators(df)

    assert {
        "sma_5",
        "ema_20",
        "ma_slope_60",
        "rsi_14",
        "macd_12_26_9",
        "macd_signal_12_26_9",
        "macd_histogram_12_26_9",
        "true_range",
        "atr_14",
        "bb_middle_20_2",
        "bb_upper_20_2",
        "bb_lower_20_2",
        "bb_bandwidth_20_2",
        "bb_percent_b_20_2",
        "obv",
        "candle_body_ratio",
        "candle_upper_shadow_ratio",
        "candle_lower_shadow_ratio",
    }.issubset(result.columns)


def test_add_moving_average_indicators_rejects_missing_price_column() -> None:
    df = pd.DataFrame({"open": [10.0, 20.0]})

    with pytest.raises(ValueError, match="Missing price column: close"):
        add_moving_average_indicators(df)


def test_add_momentum_indicators_rejects_missing_price_column() -> None:
    df = pd.DataFrame({"open": [10.0, 20.0]})

    with pytest.raises(ValueError, match="Missing price column: close"):
        add_momentum_indicators(df)


def test_true_range_rejects_missing_columns() -> None:
    df = pd.DataFrame({"high": [10.0], "close": [9.0]})

    with pytest.raises(ValueError, match="Missing required columns: low"):
        true_range(df)


def test_add_volume_indicators_rejects_missing_volume_column() -> None:
    df = pd.DataFrame({"close": [10.0, 20.0]})

    with pytest.raises(ValueError, match="Missing required columns: volume"):
        add_volume_indicators(df)


def test_candle_ratios_rejects_missing_columns() -> None:
    df = pd.DataFrame({"high": [10.0], "low": [8.0], "close": [9.0]})

    with pytest.raises(ValueError, match="Missing required columns: open"):
        candle_ratios(df)


def test_simple_moving_average_rejects_invalid_window() -> None:
    series = pd.Series([10.0, 20.0])

    with pytest.raises(ValueError, match="window must be at least 1"):
        simple_moving_average(series, window=0)


def test_relative_strength_index_rejects_unknown_method() -> None:
    series = pd.Series([10.0, 20.0])

    with pytest.raises(ValueError, match="method must be one of"):
        relative_strength_index(series, method="unknown")  # type: ignore[arg-type]


def test_moving_average_convergence_divergence_rejects_invalid_windows() -> None:
    series = pd.Series([10.0, 20.0])

    with pytest.raises(ValueError, match="fast must be less than slow"):
        moving_average_convergence_divergence(series, fast=3, slow=3, signal=2)


def test_average_true_range_rejects_unknown_method() -> None:
    df = pd.DataFrame({"high": [10.0], "low": [8.0], "close": [9.0]})

    with pytest.raises(ValueError, match="method must be one of"):
        average_true_range(df, method="unknown")  # type: ignore[arg-type]


def test_bollinger_bands_rejects_invalid_multiplier() -> None:
    series = pd.Series([10.0, 20.0])

    with pytest.raises(ValueError, match="multiplier must be greater than 0"):
        bollinger_bands(series, multiplier=0)
