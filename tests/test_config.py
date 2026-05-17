import pytest

from hanta.config import (
    AnalysisConfig,
    BacktestConfig,
    DEFAULT_ANALYSIS_CONFIG,
    DEFAULT_BACKTEST_CONFIG,
    DEFAULT_SIGNAL_WEIGHTS,
    ScoringConfig,
    normalize_weights,
    with_signal_weights,
)


def test_analysis_config_contains_default_warmup_and_scoring() -> None:
    config = AnalysisConfig()

    assert config.warmup_period == 90
    assert config.scoring.signal_weights["signal_rsi_14"] == DEFAULT_SIGNAL_WEIGHTS[
        "signal_rsi_14"
    ]
    assert DEFAULT_ANALYSIS_CONFIG == config


def test_backtest_config_contains_default_position_parameters() -> None:
    config = BacktestConfig()

    assert config.floor == 0.0
    assert config.threshold == 30.0
    assert config.threshold_position == 0.3
    assert config.max_position == 1.0
    assert DEFAULT_BACKTEST_CONFIG == config


def test_with_signal_weights_builds_analysis_config() -> None:
    config = with_signal_weights({"signal_rsi_14": 1.0}, warmup_period=60)

    assert config.warmup_period == 60
    assert config.scoring == ScoringConfig(signal_weights={"signal_rsi_14": 1.0})


def test_normalize_weights_scales_to_one() -> None:
    result = normalize_weights({"a": 2.0, "b": 1.0})

    assert result == {"a": 2 / 3, "b": 1 / 3}


def test_normalize_weights_rejects_empty_or_zero_total() -> None:
    with pytest.raises(ValueError, match="signal weights must sum to a positive value"):
        normalize_weights({"a": 0.0})
