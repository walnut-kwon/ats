import pandas as pd

from ats.scoring import add_score


def test_add_score_uses_signal_columns() -> None:
    df = pd.DataFrame(
        {
            "signal_trend": [1.0, -1.0],
            "signal_momentum": [0.5, -0.5],
        }
    )

    result = add_score(df)

    assert result["score"].tolist() == [75.0, -75.0]
