from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd


def min_max_scale(
    series: pd.Series,
    min_value: float,
    max_value: float,
) -> pd.Series:
    """Scale values to the 0.0 to 1.0 range using a fixed min/max."""
    if min_value >= max_value:
        raise ValueError("min_value must be less than max_value")

    return (series - min_value) / (max_value - min_value)


def centered_min_max_scale(
    series: pd.Series,
    center: float,
    width: float,
) -> pd.Series:
    """Scale values around a center point to an unbounded centered range."""
    if width <= 0:
        raise ValueError("width must be greater than 0")

    return (series - center) / width


def rolling_zscore(
    series: pd.Series,
    window: int,
    min_periods: Optional[int] = None,
    ddof: int = 0,
    epsilon: float = 1e-12,
) -> pd.Series:
    """Return a rolling z-score for a series."""
    _validate_window(window)
    min_periods = min_periods or window
    mean = series.rolling(window=window, min_periods=min_periods).mean()
    std = series.rolling(window=window, min_periods=min_periods).std(ddof=ddof)
    return (series - mean) / _mask_near_zero(std, epsilon)


def rolling_robust_score(
    series: pd.Series,
    window: int,
    min_periods: Optional[int] = None,
    lower_quantile: float = 0.25,
    upper_quantile: float = 0.75,
    epsilon: float = 1e-12,
) -> pd.Series:
    """Return a rolling robust score using median and IQR."""
    _validate_window(window)
    _validate_quantiles(lower_quantile, upper_quantile)
    min_periods = min_periods or window
    rolling = series.rolling(window=window, min_periods=min_periods)
    median = rolling.median()
    lower = rolling.quantile(lower_quantile)
    upper = rolling.quantile(upper_quantile)
    iqr = upper - lower
    return (series - median) / _mask_near_zero(iqr, epsilon)


def clip_signal(series: pd.Series, limit: float = 1.0) -> pd.Series:
    """Clip values to the -limit to +limit range."""
    if limit <= 0:
        raise ValueError("limit must be greater than 0")

    return series.clip(lower=-limit, upper=limit)


def squash_signal(series: pd.Series, scale: float = 1.0) -> pd.Series:
    """Squash values smoothly to the -1.0 to +1.0 range with tanh."""
    if scale <= 0:
        raise ValueError("scale must be greater than 0")

    return pd.Series(np.tanh(series / scale), index=series.index)


def _mask_near_zero(series: pd.Series, epsilon: float) -> pd.Series:
    return series.mask(series.abs() <= epsilon)


def _validate_window(window: int) -> None:
    if window < 1:
        raise ValueError("window must be at least 1")


def _validate_quantiles(lower_quantile: float, upper_quantile: float) -> None:
    if not 0 <= lower_quantile < upper_quantile <= 1:
        raise ValueError("quantiles must satisfy 0 <= lower < upper <= 1")
