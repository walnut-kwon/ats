from __future__ import annotations

from typing import List, Mapping, Optional, Sequence

import pandas as pd

from hanta.config import DEFAULT_SIGNAL_WEIGHTS


def add_score(
    df: pd.DataFrame,
    signal_columns: Optional[List[str]] = None,
    signal_weights: Mapping[str, float] = DEFAULT_SIGNAL_WEIGHTS,
) -> pd.DataFrame:
    """Add a final -100 to +100 weighted score."""
    result = df.copy()

    if signal_columns is not None:
        result["score"] = _simple_signal_score(result, signal_columns)
        return result

    _validate_signal_weights(signal_weights)
    weighted_columns = [column for column in signal_weights if column in result.columns]
    if weighted_columns:
        result["score"] = _weighted_signal_score(result, signal_weights, weighted_columns)
        return result

    all_signal_columns = [column for column in result.columns if column.startswith("signal_")]
    result["score"] = _simple_signal_score(result, all_signal_columns)
    return result


def _weighted_signal_score(
    df: pd.DataFrame,
    signal_weights: Mapping[str, float],
    signal_columns: Sequence[str],
) -> pd.Series:
    score_frame = df[list(signal_columns)]
    weights = pd.Series({column: signal_weights[column] for column in signal_columns})
    weighted_sum = score_frame.mul(weights).sum(axis=1, min_count=1)
    available_weight = score_frame.notna().mul(weights).sum(axis=1)
    return (weighted_sum / available_weight).mul(100).clip(-100, 100)


def _simple_signal_score(df: pd.DataFrame, signal_columns: Sequence[str]) -> pd.Series:
    if not signal_columns:
        return pd.Series(0.0, index=df.index)

    return df[list(signal_columns)].mean(axis=1).mul(100).clip(-100, 100)
def _validate_signal_weights(signal_weights: Mapping[str, float]) -> None:
    for signal, weight in signal_weights.items():
        if weight <= 0:
            raise ValueError(f"signal weight must be greater than 0: {signal}")
