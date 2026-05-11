from __future__ import annotations

import pandas as pd


def add_forward_return(df: pd.DataFrame, periods: int = 1) -> pd.DataFrame:
    """Add a simple forward return column for signal validation."""
    result = df.copy()
    result[f"forward_return_{periods}"] = result["close"].shift(-periods) / result["close"] - 1
    return result
