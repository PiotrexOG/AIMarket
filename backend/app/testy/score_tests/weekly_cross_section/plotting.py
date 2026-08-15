from .information_coefficient import plot as plot_information_coefficient
from .top_n_selection import plot as plot_top_n_selection


def plot(analysis, output_dir):
    if analysis.empty:
        return
    plot_top_n_selection(analysis, output_dir)
    plot_information_coefficient(analysis, output_dir)


def plot_weekly_information_coefficient(analysis, output_dir):
    if analysis.empty:
        return
    plot_information_coefficient(analysis, output_dir)
