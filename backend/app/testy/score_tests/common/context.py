from dataclasses import dataclass
from functools import cached_property

import pandas as pd


@dataclass
class ScoreTestContext:
    """Shared prepared data; expensive sorts are computed at most once."""

    return_panel: pd.DataFrame
    score_observations: pd.DataFrame | None = None

    @cached_property
    def weekly_ranked(self):
        return self.return_panel.sort_values(
            [
                "timeframe",
                "horizon_weeks",
                "horizon_days",
                "start_timestamp",
                "score",
                "ticker",
            ],
            ascending=[True, True, True, True, False, True],
        )

    @cached_property
    def global_ranked(self):
        return self.return_panel.sort_values(
            [
                "timeframe",
                "horizon_weeks",
                "horizon_days",
                "score",
                "start_timestamp",
                "ticker",
            ],
            ascending=[True, True, True, False, True, True],
        )
