from __future__ import annotations

from typing import Dict, Optional

import pandas as pd

from hanta.config import DEFAULT_BACKTEST_CONFIG, BacktestConfig


def add_forward_return(df: pd.DataFrame, periods: int = 1) -> pd.DataFrame:
    """Add a simple forward return column for signal validation."""
    result = df.copy()
    result[f"forward_return_{periods}"] = result["close"].shift(-periods) / result["close"] - 1
    return result


def thresholded_linear_position(
    score: pd.Series,
    floor: float = 0.0,
    threshold: float = 30.0,
    threshold_position: float = 0.3,
    max_position: float = 1.0,
) -> pd.Series:
    """Convert score to a long-only target position with smooth rebalancing."""
    _validate_position_parameters(floor, threshold, threshold_position, max_position)

    position = pd.Series(0.0, index=score.index)
    below_threshold = score.between(floor, threshold, inclusive="left")
    above_threshold = score >= threshold

    position = position.mask(
        below_threshold,
        threshold_position * (score - floor) / (threshold - floor),
    )
    position = position.mask(
        above_threshold,
        threshold_position
        + (max_position - threshold_position) * (score - threshold) / (100 - threshold),
    )
    return position.clip(lower=0.0, upper=max_position)


def add_backtest_columns(
    df: pd.DataFrame,
    score_column: str = "score",
    price_column: str = "close",
    config: Optional[BacktestConfig] = None,
) -> pd.DataFrame:
    """Add long-only backtest columns using score-derived target positions."""
    config = config or DEFAULT_BACKTEST_CONFIG
    _validate_required_columns(df, (score_column, price_column))
    result = df.copy()
    result["target_position"] = thresholded_linear_position(
        result[score_column],
        floor=config.floor,
        threshold=config.threshold,
        threshold_position=config.threshold_position,
        max_position=config.max_position,
    )
    result["position"] = result["target_position"].shift(1).fillna(0.0)
    result["asset_return"] = result[price_column].pct_change().fillna(0.0)
    result["strategy_return"] = result["position"] * result["asset_return"]
    result["cumulative_asset_return"] = (1 + result["asset_return"]).cumprod() - 1
    result["cumulative_strategy_return"] = (1 + result["strategy_return"]).cumprod() - 1
    result["strategy_equity"] = 1 + result["cumulative_strategy_return"]
    result["drawdown"] = result["strategy_equity"] / result["strategy_equity"].cummax() - 1
    return result


def summarize_backtest(df: pd.DataFrame) -> Dict[str, float]:
    """Return a compact summary for a dataframe with backtest columns."""
    _validate_required_columns(
        df,
        (
            "asset_return",
            "strategy_return",
            "cumulative_asset_return",
            "cumulative_strategy_return",
            "drawdown",
            "position",
        ),
    )
    active_returns = df.loc[df["position"] > 0, "strategy_return"]
    return {
        "strategy_total_return": float(df["cumulative_strategy_return"].iloc[-1]),
        "benchmark_total_return": float(df["cumulative_asset_return"].iloc[-1]),
        "max_drawdown": float(df["drawdown"].min()),
        "win_rate": float((active_returns > 0).mean()) if not active_returns.empty else 0.0,
        "average_position": float(df["position"].mean()),
        "exposure": float((df["position"] > 0).mean()),
    }


def _validate_position_parameters(
    floor: float,
    threshold: float,
    threshold_position: float,
    max_position: float,
) -> None:
    if not 0 <= floor < threshold < 100:
        raise ValueError("position thresholds must satisfy 0 <= floor < threshold < 100")
    if not 0 <= threshold_position <= max_position <= 1:
        raise ValueError("positions must satisfy 0 <= threshold_position <= max_position <= 1")


def _validate_required_columns(df: pd.DataFrame, columns: tuple[str, ...]) -> None:
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
