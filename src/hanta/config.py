from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Mapping

DEFAULT_SIGNAL_WEIGHTS = {
    "signal_ma_alignment_5_20_60": 0.15,
    "signal_ma_slope_5": 0.08,
    "signal_ma_slope_20": 0.12,
    "signal_ma_slope_60": 0.10,
    "signal_rsi_14": 0.18,
    "signal_macd_histogram_12_26_9": 0.17,
    "signal_atr_expansion_14": 0.08,
    "signal_bb_percent_b_20_2": 0.07,
    "signal_obv_change": 0.05,
}


@dataclass(frozen=True)
class ScoringConfig:
    """Configuration for weighted signal scoring."""

    signal_weights: Mapping[str, float] = field(
        default_factory=lambda: dict(DEFAULT_SIGNAL_WEIGHTS)
    )


@dataclass(frozen=True)
class AnalysisConfig:
    """Configuration for the default analysis pipeline."""

    warmup_period: int = 90
    scoring: ScoringConfig = field(default_factory=ScoringConfig)


@dataclass(frozen=True)
class BacktestConfig:
    """Configuration for the default long-only backtest."""

    floor: float = 0.0
    threshold: float = 30.0
    threshold_position: float = 0.3
    max_position: float = 1.0


DEFAULT_ANALYSIS_CONFIG = AnalysisConfig()
DEFAULT_BACKTEST_CONFIG = BacktestConfig()


def with_signal_weights(weights: Mapping[str, float], warmup_period: int = 90) -> AnalysisConfig:
    """Build an analysis config with custom exact signal weights."""
    return AnalysisConfig(
        warmup_period=warmup_period,
        scoring=ScoringConfig(signal_weights=dict(weights)),
    )


def normalize_weights(weights: Mapping[str, float]) -> Dict[str, float]:
    """Return a copy of weights normalized to sum to 1.0."""
    total = sum(weights.values())
    if total <= 0:
        raise ValueError("signal weights must sum to a positive value")
    return {signal: weight / total for signal, weight in weights.items()}
