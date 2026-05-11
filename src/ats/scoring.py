from __future__ import annotations

from typing import List, Optional

import pandas as pd


def add_score(df: pd.DataFrame, signal_columns: Optional[List[str]] = None) -> pd.DataFrame:
    """Add a final score column from normalized signal columns."""
    result = df.copy()
    signal_columns = signal_columns or [
        column for column in result.columns if column.startswith("signal_")
    ]
    if not signal_columns:
        result["score"] = 0.0
        return result

    result["score"] = result[signal_columns].mean(axis=1).mul(100).clip(-100, 100)
    return result
