import pandas as pd
import pytest

from ats.data import validate_ohlcv_columns


def test_validate_ohlcv_columns_accepts_required_columns() -> None:
    df = pd.DataFrame(
        columns=["date", "open", "high", "low", "close", "volume"]
    )

    validate_ohlcv_columns(df)


def test_validate_ohlcv_columns_rejects_missing_columns() -> None:
    df = pd.DataFrame(columns=["date", "open", "high"])

    with pytest.raises(ValueError, match="low, close, volume"):
        validate_ohlcv_columns(df)
