from __future__ import annotations

from typing import Iterable

import pandas as pd

from hanta.scalers import centered_min_max_scale, clip_signal, rolling_robust_score, rolling_zscore


def rsi_signal(series: pd.Series) -> pd.Series:
    """Convert RSI to a centered momentum signal."""
    return clip_signal(centered_min_max_scale(series, center=50.0, width=50.0))


def percent_b_signal(series: pd.Series) -> pd.Series:
    """Convert Bollinger percent-b to a centered location signal."""
    return clip_signal(centered_min_max_scale(series, center=0.5, width=0.5))


def zscore_signal(series: pd.Series, window: int = 30, scale: float = 2.0) -> pd.Series:
    """Convert an unbounded series to a clipped rolling z-score signal."""
    if scale <= 0:
        raise ValueError("scale must be greater than 0")

    return clip_signal(rolling_zscore(series, window=window) / scale)


def robust_change_signal(
    series: pd.Series,
    window: int = 30,
    scale: float = 2.0,
) -> pd.Series:
    """Convert one-period changes to a clipped robust rolling signal."""
    if scale <= 0:
        raise ValueError("scale must be greater than 0")

    return clip_signal(rolling_robust_score(series.diff(), window=window) / scale)


def atr_expansion_signal(
    atr: pd.Series,
    window: int = 20,
    threshold: float = 1.5,
) -> pd.Series:
    """Convert ATR expansion ratio to a 0.0 to 1.0 volatility signal."""
    if threshold <= 1:
        raise ValueError("threshold must be greater than 1")

    baseline = atr.rolling(window=window, min_periods=window).mean()
    ratio = atr / baseline
    signal = (ratio - 1) / (threshold - 1)
    return signal.clip(lower=0, upper=1)


def ma_alignment_signal(
    fast_ma: pd.Series,
    medium_ma: pd.Series,
    slow_ma: pd.Series,
) -> pd.Series:
    """Convert moving-average ordering to a pairwise alignment signal."""
    fast_medium = _pairwise_order_signal(fast_ma, medium_ma)
    medium_slow = _pairwise_order_signal(medium_ma, slow_ma)
    return (fast_medium + medium_slow) / 2


def add_signals(
    df: pd.DataFrame,
    zscore_window: int = 30,
    atr_window: int = 20,
    obv_window: int = 30,
) -> pd.DataFrame:
    """Add normalized signal columns in the -1.0 to 1.0 range."""
    result = df.copy()

    _add_zscore_signals(
        result,
        columns=_matching_columns(result, prefixes=("ma_slope_", "macd_histogram_")),
        window=zscore_window,
    )
    _add_rsi_signals(result, _matching_columns(result, prefixes=("rsi_",)))
    _add_percent_b_signals(result, _matching_columns(result, prefixes=("bb_percent_b_",)))
    _add_ma_alignment_signal(result, fast=5, medium=20, slow=60)

    if "atr_14" in result.columns:
        result["signal_atr_expansion_14"] = atr_expansion_signal(
            result["atr_14"],
            window=atr_window,
        )

    if "obv" in result.columns:
        result["signal_obv_change"] = robust_change_signal(
            result["obv"],
            window=obv_window,
        )

    return result


def _add_zscore_signals(
    df: pd.DataFrame,
    columns: Iterable[str],
    window: int,
) -> None:
    for column in columns:
        df[f"signal_{column}"] = zscore_signal(df[column], window=window)


def _add_rsi_signals(df: pd.DataFrame, columns: Iterable[str]) -> None:
    for column in columns:
        df[f"signal_{column}"] = rsi_signal(df[column])


def _add_percent_b_signals(df: pd.DataFrame, columns: Iterable[str]) -> None:
    for column in columns:
        df[f"signal_{column}"] = percent_b_signal(df[column])


def _add_ma_alignment_signal(df: pd.DataFrame, fast: int, medium: int, slow: int) -> None:
    columns = (f"sma_{fast}", f"sma_{medium}", f"sma_{slow}")
    if not all(column in df.columns for column in columns):
        return

    df[f"signal_ma_alignment_{fast}_{medium}_{slow}"] = ma_alignment_signal(
        df[columns[0]],
        df[columns[1]],
        df[columns[2]],
    )


def _matching_columns(df: pd.DataFrame, prefixes: tuple[str, ...]) -> list[str]:
    return [column for column in df.columns if column.startswith(prefixes)]


def _pairwise_order_signal(left: pd.Series, right: pd.Series) -> pd.Series:
    signal = pd.Series(0.0, index=left.index)
    signal = signal.mask(left > right, 1.0)
    signal = signal.mask(left < right, -1.0)
    return signal.mask(left.isna() | right.isna())
