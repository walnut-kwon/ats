from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import pandas as pd

from hanta.data import load_ohlcv_csv
from hanta.indicators import add_indicators
from hanta.scoring import add_score
from hanta.signals import add_signals


def analyze_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """Run the default indicator, signal, and scoring pipeline."""
    result = add_indicators(df)
    result = add_signals(result)
    result = add_score(result)
    return result


def analyze_csv(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
) -> pd.DataFrame:
    """Load OHLCV CSV data, analyze it, and optionally write the result."""
    result = analyze_ohlcv(load_ohlcv_csv(input_path))
    if output_path is not None:
        result.to_csv(output_path, index=False)
    return result
