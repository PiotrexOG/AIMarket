import re
from pathlib import Path

import pandas as pd

from app.testy.score_tests.common.io import save_csv_for_excel
from app.testy.score_tests.common.plotting import plot_path


def _safe_filename(value):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", str(value)).strip("._") or "unknown"


def _to_utc_naive(values):
    return pd.to_datetime(values, utc=True).dt.tz_localize(None)


def _save_figure(fig, path, **kwargs):
    try:
        fig.savefig(path, **kwargs)
        return path
    except OSError as error:
        if getattr(error, "errno", None) != 22:
            raise
        fallback_path = path.with_name(f"{path.stem}_latest{path.suffix}")
        fig.savefig(fallback_path, **kwargs)
        return fallback_path


def _save_heatmap_csv(heatmap_data, output_dir, directory, filename):
    csv_filename = f"{Path(filename).stem}.csv"
    csv_data = heatmap_data.reset_index()
    save_csv_for_excel(csv_data, plot_path(output_dir, directory, csv_filename))
