import math

import pandas as pd
import pytest

from hanta.scalers import (
    centered_min_max_scale,
    clip_signal,
    min_max_scale,
    rolling_robust_score,
    rolling_zscore,
    squash_signal,
)


def test_min_max_scale_uses_fixed_bounds() -> None:
    series = pd.Series([0.0, 50.0, 100.0])

    result = min_max_scale(series, min_value=0.0, max_value=100.0)

    assert result.tolist() == [0.0, 0.5, 1.0]


def test_centered_min_max_scale_uses_center_and_width() -> None:
    series = pd.Series([0.0, 50.0, 100.0])

    result = centered_min_max_scale(series, center=50.0, width=50.0)

    assert result.tolist() == [-1.0, 0.0, 1.0]


def test_rolling_zscore_uses_population_std_by_default() -> None:
    series = pd.Series([10.0, 12.0, 14.0])

    result = rolling_zscore(series, window=3)

    assert math.isnan(result.iloc[0])
    assert math.isnan(result.iloc[1])
    assert round(result.iloc[2], 4) == 1.2247


def test_rolling_zscore_masks_near_zero_std() -> None:
    series = pd.Series([10.0, 10.0, 10.0])

    result = rolling_zscore(series, window=3)

    assert math.isnan(result.iloc[2])


def test_rolling_robust_score_uses_median_and_iqr() -> None:
    series = pd.Series([10.0, 11.0, 12.0, 100.0])

    result = rolling_robust_score(series, window=4)

    assert math.isnan(result.iloc[0])
    assert math.isnan(result.iloc[1])
    assert math.isnan(result.iloc[2])
    assert round(result.iloc[3], 4) == 3.8065


def test_rolling_robust_score_masks_near_zero_iqr() -> None:
    series = pd.Series([10.0, 10.0, 10.0])

    result = rolling_robust_score(series, window=3)

    assert math.isnan(result.iloc[2])


def test_clip_signal_clips_to_limit() -> None:
    series = pd.Series([-3.0, -0.5, 0.5, 3.0])

    result = clip_signal(series, limit=1.0)

    assert result.tolist() == [-1.0, -0.5, 0.5, 1.0]


def test_squash_signal_uses_tanh() -> None:
    series = pd.Series([-2.0, 0.0, 2.0])

    result = squash_signal(series, scale=2.0)

    assert result.round(4).tolist() == [-0.7616, 0.0, 0.7616]


def test_min_max_scale_rejects_invalid_bounds() -> None:
    series = pd.Series([1.0])

    with pytest.raises(ValueError, match="min_value must be less than max_value"):
        min_max_scale(series, min_value=1.0, max_value=1.0)


def test_centered_min_max_scale_rejects_invalid_width() -> None:
    series = pd.Series([1.0])

    with pytest.raises(ValueError, match="width must be greater than 0"):
        centered_min_max_scale(series, center=0.0, width=0.0)


def test_rolling_zscore_rejects_invalid_window() -> None:
    series = pd.Series([1.0])

    with pytest.raises(ValueError, match="window must be at least 1"):
        rolling_zscore(series, window=0)


def test_rolling_robust_score_rejects_invalid_quantiles() -> None:
    series = pd.Series([1.0])

    with pytest.raises(ValueError, match="quantiles must satisfy"):
        rolling_robust_score(series, window=1, lower_quantile=0.75, upper_quantile=0.25)


def test_clip_signal_rejects_invalid_limit() -> None:
    series = pd.Series([1.0])

    with pytest.raises(ValueError, match="limit must be greater than 0"):
        clip_signal(series, limit=0.0)


def test_squash_signal_rejects_invalid_scale() -> None:
    series = pd.Series([1.0])

    with pytest.raises(ValueError, match="scale must be greater than 0"):
        squash_signal(series, scale=0.0)
