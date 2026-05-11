from __future__ import annotations

import pandas as pd


def add_signals(df: pd.DataFrame) -> pd.DataFrame:
    """Add normalized signal columns in the -1.0 to 1.0 range."""
    result = df.copy()
    # Signal conversion rules will be added after indicators are implemented.
    return result
