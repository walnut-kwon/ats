from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import pandas as pd

from hanta.config import DEFAULT_ANALYSIS_CONFIG, AnalysisConfig
from hanta.data import load_ohlcv_csv
from hanta.indicators import add_indicators
from hanta.scoring import add_score
from hanta.signals import add_signals

DEFAULT_WARMUP_PERIOD = DEFAULT_ANALYSIS_CONFIG.warmup_period


def analyze_ohlcv(
    df: pd.DataFrame,
    config: Optional[AnalysisConfig] = None,
) -> pd.DataFrame:
    """Run the default indicator, signal, and scoring pipeline."""
    config = config or DEFAULT_ANALYSIS_CONFIG
    _validate_warmup_period(config.warmup_period)
    result = add_indicators(df)
    result = add_signals(result)
    result = add_score(
        result,
        signal_weights=config.scoring.signal_weights,
    )
    result = add_warmup_flag(result, warmup_period=config.warmup_period)
    return result


def analyze_csv(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    config: Optional[AnalysisConfig] = None,
) -> pd.DataFrame:
    """Load OHLCV CSV data, analyze it, and optionally write the result."""
    result = analyze_ohlcv(
        load_ohlcv_csv(input_path),
        config=config,
    )
    if output_path is not None:
        result.to_csv(output_path, index=False)
    return result


def add_warmup_flag(df: pd.DataFrame, warmup_period: int = DEFAULT_WARMUP_PERIOD) -> pd.DataFrame:
    """Add an is_warmup flag for the initial rows of an analysis result."""
    _validate_warmup_period(warmup_period)
    result = df.copy()
    result["is_warmup"] = result.index < warmup_period
    return result


def _validate_warmup_period(warmup_period: int) -> None:
    if warmup_period < 0:
        raise ValueError("warmup_period must be greater than or equal to 0")
