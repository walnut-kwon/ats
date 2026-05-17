from __future__ import annotations

from typing import List, Mapping, Optional, Sequence

import pandas as pd

DEFAULT_SIGNAL_GROUPS = {
    "trend": ("signal_ma_slope_",),
    "momentum": ("signal_rsi_", "signal_macd_histogram_"),
    "volatility": ("signal_atr_expansion_", "signal_bb_percent_b_"),
    "volume": ("signal_obv_change",),
}

DEFAULT_GROUP_WEIGHTS = {
    "trend": 0.35,
    "momentum": 0.35,
    "volatility": 0.15,
    "volume": 0.15,
}


def add_score(
    df: pd.DataFrame,
    signal_columns: Optional[List[str]] = None,
    signal_groups: Mapping[str, Sequence[str]] = DEFAULT_SIGNAL_GROUPS,
    group_weights: Mapping[str, float] = DEFAULT_GROUP_WEIGHTS,
) -> pd.DataFrame:
    """Add group scores and a final -100 to +100 weighted score column."""
    result = df.copy()

    if signal_columns is not None:
        result["score"] = _simple_signal_score(result, signal_columns)
        return result

    group_score_columns = _add_group_scores(result, signal_groups)
    if not group_score_columns:
        all_signal_columns = [column for column in result.columns if column.startswith("signal_")]
        result["score"] = _simple_signal_score(result, all_signal_columns)
        return result

    _validate_group_weights(group_weights)
    result["score"] = _weighted_group_score(result, group_score_columns, group_weights)
    return result


def _add_group_scores(
    df: pd.DataFrame,
    signal_groups: Mapping[str, Sequence[str]],
) -> list[str]:
    group_score_columns = []
    for group, prefixes in signal_groups.items():
        columns = _matching_columns(df, prefixes)
        if not columns:
            continue

        score_column = f"score_{group}"
        df[score_column] = df[columns].mean(axis=1)
        group_score_columns.append(score_column)

    return group_score_columns


def _weighted_group_score(
    df: pd.DataFrame,
    group_score_columns: Sequence[str],
    group_weights: Mapping[str, float],
) -> pd.Series:
    score_frame = df[list(group_score_columns)]
    weights = pd.Series(
        {
            score_column: group_weights[score_column.removeprefix("score_")]
            for score_column in group_score_columns
        }
    )
    weighted_sum = score_frame.mul(weights).sum(axis=1, min_count=1)
    available_weight = score_frame.notna().mul(weights).sum(axis=1)
    return (weighted_sum / available_weight).mul(100).clip(-100, 100)


def _simple_signal_score(df: pd.DataFrame, signal_columns: Sequence[str]) -> pd.Series:
    if not signal_columns:
        return pd.Series(0.0, index=df.index)

    return df[list(signal_columns)].mean(axis=1).mul(100).clip(-100, 100)


def _matching_columns(df: pd.DataFrame, prefixes: Sequence[str]) -> list[str]:
    return [column for column in df.columns if column.startswith(tuple(prefixes))]


def _validate_group_weights(group_weights: Mapping[str, float]) -> None:
    for group, weight in group_weights.items():
        if weight <= 0:
            raise ValueError(f"group weight must be greater than 0: {group}")
