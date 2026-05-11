from __future__ import annotations

from pathlib import Path
from typing import Union

import pandas as pd

OHLCV_COLUMNS = ("date", "open", "high", "low", "close", "volume")


def validate_ohlcv_columns(df: pd.DataFrame) -> None:
    """Validate that a dataframe contains the required OHLCV columns."""
    missing = [column for column in OHLCV_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required OHLCV columns: {', '.join(missing)}")


def load_ohlcv_csv(path: Union[str, Path]) -> pd.DataFrame:
    """Load OHLCV data from a CSV file."""
    df = pd.read_csv(path)
    validate_ohlcv_columns(df)
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)
