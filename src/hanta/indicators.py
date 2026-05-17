from __future__ import annotations

from typing import Iterable, Literal

import pandas as pd

RsiMethod = Literal["wilder", "simple"]
SmoothingMethod = Literal["wilder", "simple"]


def simple_moving_average(series: pd.Series, window: int) -> pd.Series:
    """Return the simple moving average for a series."""
    _validate_window(window)
    return series.rolling(window=window, min_periods=window).mean()


def exponential_moving_average(series: pd.Series, span: int) -> pd.Series:
    """Return the exponential moving average for a series."""
    _validate_window(span)
    # EMA uses a long exponential tail: a 60-day EMA can be computed after
    # 60 rows, but signal logic should usually treat roughly span * 3 rows as
    # warm-up before trusting the value for backtests or trading decisions.
    return series.ewm(span=span, adjust=False, min_periods=span).mean()


def moving_average_slope(series: pd.Series, window: int) -> pd.Series:
    """Return the per-period slope of a moving average series."""
    _validate_window(window)
    return (series - series.shift(window)) / window


def relative_strength_index(
    series: pd.Series,
    window: int = 14,
    method: RsiMethod = "wilder",
) -> pd.Series:
    """Return RSI using Wilder smoothing or a simple rolling average."""
    _validate_window(window)
    if method not in ("wilder", "simple"):
        raise ValueError("method must be one of: wilder, simple")

    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    if method == "wilder":
        # Wilder RSI seeds the first average with a simple rolling average,
        # then smooths subsequent values with alpha=1/window. Like EMA, it has
        # a long tail, so downstream signal logic should apply a warm-up period
        # before treating early values as reliable.
        average_gain = _wilder_smoothed_average(gain, window)
        average_loss = _wilder_smoothed_average(loss, window)
    else:
        average_gain = gain.rolling(window=window, min_periods=window).mean()
        average_loss = loss.rolling(window=window, min_periods=window).mean()

    relative_strength = average_gain / average_loss
    rsi = 100 - (100 / (1 + relative_strength))
    rsi = rsi.mask((average_loss == 0) & (average_gain > 0), 100.0)
    rsi = rsi.mask((average_gain == 0) & (average_loss > 0), 0.0)
    rsi = rsi.mask((average_gain == 0) & (average_loss == 0), 50.0)
    return rsi


def moving_average_convergence_divergence(
    series: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """Return MACD line, signal line, and histogram."""
    _validate_macd_windows(fast, slow, signal)
    fast_ema = exponential_moving_average(series, fast)
    slow_ema = exponential_moving_average(series, slow)
    macd_line = fast_ema - slow_ema
    signal_line = exponential_moving_average(macd_line, signal)
    histogram = macd_line - signal_line
    suffix = f"{fast}_{slow}_{signal}"
    return pd.DataFrame(
        {
            f"macd_{suffix}": macd_line,
            f"macd_signal_{suffix}": signal_line,
            f"macd_histogram_{suffix}": histogram,
        },
        index=series.index,
    )


def true_range(df: pd.DataFrame) -> pd.Series:
    """Return true range from high, low, and previous close."""
    _validate_columns(df, ("high", "low", "close"))
    previous_close = df["close"].shift(1)
    ranges = pd.DataFrame(
        {
            "high_low": df["high"] - df["low"],
            "high_previous_close": (df["high"] - previous_close).abs(),
            "low_previous_close": (df["low"] - previous_close).abs(),
        },
        index=df.index,
    )
    return ranges.max(axis=1)


def average_true_range(
    df: pd.DataFrame,
    window: int = 14,
    method: SmoothingMethod = "wilder",
) -> pd.Series:
    """Return ATR using Wilder smoothing or a simple rolling average."""
    _validate_window(window)
    if method not in ("wilder", "simple"):
        raise ValueError("method must be one of: wilder, simple")

    tr = true_range(df)
    if method == "wilder":
        return _wilder_smoothed_average(tr, window)
    return tr.rolling(window=window, min_periods=window).mean()


def bollinger_bands(
    series: pd.Series,
    window: int = 20,
    multiplier: float = 2.0,
    ddof: int = 0,
) -> pd.DataFrame:
    """Return Bollinger Bands, bandwidth, and percent-b."""
    _validate_window(window)
    if multiplier <= 0:
        raise ValueError("multiplier must be greater than 0")

    middle = simple_moving_average(series, window)
    rolling_std = series.rolling(window=window, min_periods=window).std(ddof=ddof)
    upper = middle + (multiplier * rolling_std)
    lower = middle - (multiplier * rolling_std)
    band_range = upper - lower
    suffix = f"{window}_{_format_number_for_column(multiplier)}"
    return pd.DataFrame(
        {
            f"bb_middle_{suffix}": middle,
            f"bb_upper_{suffix}": upper,
            f"bb_lower_{suffix}": lower,
            f"bb_bandwidth_{suffix}": band_range / middle,
            f"bb_percent_b_{suffix}": (series - lower) / band_range,
        },
        index=series.index,
    )


def on_balance_volume(close: pd.Series, volume: pd.Series) -> pd.Series:
    """Return On-Balance Volume."""
    direction = close.diff().fillna(0).apply(_sign)
    return (direction * volume).cumsum()


def candle_ratios(df: pd.DataFrame) -> pd.DataFrame:
    """Return candle body and shadow ratios in the 0.0 to 1.0 range."""
    _validate_columns(df, ("open", "high", "low", "close"))
    candle_range = df["high"] - df["low"]
    open_close_max = df[["open", "close"]].max(axis=1)
    open_close_min = df[["open", "close"]].min(axis=1)
    safe_range = candle_range.mask(candle_range == 0)

    return pd.DataFrame(
        {
            "candle_body_ratio": (df["close"] - df["open"]).abs() / safe_range,
            "candle_upper_shadow_ratio": (df["high"] - open_close_max) / safe_range,
            "candle_lower_shadow_ratio": (open_close_min - df["low"]) / safe_range,
        },
        index=df.index,
    )


def add_moving_average_indicators(
    df: pd.DataFrame,
    windows: Iterable[int] = (5, 20, 60),
    price_column: str = "close",
) -> pd.DataFrame:
    """Add SMA, EMA, and SMA slope columns for each requested window."""
    result = df.copy()
    _validate_price_column(result, price_column)

    for window in windows:
        _validate_window(window)
        sma_column = f"sma_{window}"
        ema_column = f"ema_{window}"
        slope_column = f"ma_slope_{window}"

        result[sma_column] = simple_moving_average(result[price_column], window)
        result[ema_column] = exponential_moving_average(result[price_column], window)
        result[slope_column] = moving_average_slope(result[sma_column], window)

    return result


def add_momentum_indicators(
    df: pd.DataFrame,
    rsi_window: int = 14,
    rsi_method: RsiMethod = "wilder",
    macd_fast: int = 12,
    macd_slow: int = 26,
    macd_signal: int = 9,
    price_column: str = "close",
) -> pd.DataFrame:
    """Add momentum indicator columns."""
    result = df.copy()
    _validate_price_column(result, price_column)
    result[f"rsi_{rsi_window}"] = relative_strength_index(
        result[price_column],
        window=rsi_window,
        method=rsi_method,
    )
    macd = moving_average_convergence_divergence(
        result[price_column],
        fast=macd_fast,
        slow=macd_slow,
        signal=macd_signal,
    )
    return result.join(macd)


def add_volatility_indicators(
    df: pd.DataFrame,
    atr_window: int = 14,
    atr_method: SmoothingMethod = "wilder",
    bb_window: int = 20,
    bb_multiplier: float = 2.0,
    price_column: str = "close",
) -> pd.DataFrame:
    """Add volatility indicator columns."""
    result = df.copy()
    _validate_price_column(result, price_column)
    result["true_range"] = true_range(result)
    result[f"atr_{atr_window}"] = average_true_range(
        result,
        window=atr_window,
        method=atr_method,
    )
    bands = bollinger_bands(
        result[price_column],
        window=bb_window,
        multiplier=bb_multiplier,
    )
    return result.join(bands)


def add_volume_indicators(
    df: pd.DataFrame,
    price_column: str = "close",
    volume_column: str = "volume",
) -> pd.DataFrame:
    """Add volume indicator columns."""
    result = df.copy()
    _validate_price_column(result, price_column)
    _validate_columns(result, (volume_column,))
    result["obv"] = on_balance_volume(result[price_column], result[volume_column])
    return result


def add_candle_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add candle shape indicator columns."""
    result = df.copy()
    return result.join(candle_ratios(result))


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add the default technical indicator set to OHLCV data."""
    result = add_moving_average_indicators(df)
    result = add_momentum_indicators(result)
    result = add_volatility_indicators(result)
    result = add_volume_indicators(result)
    result = add_candle_indicators(result)
    return result


def _validate_window(window: int) -> None:
    if window < 1:
        raise ValueError("window must be at least 1")


def _validate_macd_windows(fast: int, slow: int, signal: int) -> None:
    _validate_window(fast)
    _validate_window(slow)
    _validate_window(signal)
    if fast >= slow:
        raise ValueError("fast must be less than slow")


def _validate_price_column(df: pd.DataFrame, price_column: str) -> None:
    if price_column not in df.columns:
        raise ValueError(f"Missing price column: {price_column}")


def _validate_columns(df: pd.DataFrame, columns: Iterable[str]) -> None:
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")


def _format_number_for_column(value: float) -> str:
    formatted = f"{value:g}"
    return formatted.replace(".", "_")


def _sign(value: float) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def _wilder_smoothed_average(series: pd.Series, window: int) -> pd.Series:
    rolling_average = series.rolling(window=window, min_periods=window).mean()
    result = pd.Series(index=series.index, dtype="float64")

    first_valid_position = rolling_average.first_valid_index()
    if first_valid_position is None:
        return result

    start = series.index.get_loc(first_valid_position)
    result.iloc[start] = rolling_average.iloc[start]

    for position in range(start + 1, len(series)):
        previous = result.iloc[position - 1]
        current = series.iloc[position]
        result.iloc[position] = ((previous * (window - 1)) + current) / window

    return result
