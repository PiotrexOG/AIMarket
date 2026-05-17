# app/services/simulation_runner.py

from math import log2

from sqlalchemy import desc
from app.db.models.portfolio import PortfolioHistory
from app.simulation.batch.simulation_batch_service import SimulationBatchService
from app.simulation.simulation_service import SimulationService
from app.db.database import SessionLocal
from app.config.config import BENCHMARK_CHANGE_RATIO, ZERO_TIME, TICKERS
from app.portfolio_generation.robust_scoring import (
    DEFAULT_OUTPUT_PATH as DEFAULT_ROBUST_OUTPUT_PATH,
    DEFAULT_RESULTS_PATH,
    add_robust_scores,
    load_results,
    save_results,
)
from app.portfolio_generation.decision_tree import (
    DEFAULT_OUTPUT_PATH as DEFAULT_GMM_OUTPUT_PATH,
    generate_gmm_archetypes,
    select_cluster_count_by_bic,
    save_json,
)


def get_start_datetime(default_start, delta_days):
    with SessionLocal() as session:
        latest_record = (
            session.query(PortfolioHistory)
            .order_by(desc(PortfolioHistory.datetime))
            .first()
        )

        start_time = (
            latest_record.datetime + delta_days
            if latest_record
            else default_start
        )

    return start_time


def run_simulation(start_datetime, end_time, users_per_archetype, delta_days, archetypes_config):
    with SessionLocal() as session:
        simulation_service = SimulationService(
            db=session,
            tickers=TICKERS,
            zero_time=ZERO_TIME,
            start_time=start_datetime,
            end_time=end_time,
            users_per_archetype=users_per_archetype,
            delta_days=delta_days,
            archetypes_config=archetypes_config

        )

        simulation_service.run_simulation()

def run_simulation_batch(start_datetime, end_time, users_per_archetype, delta_days, archetypes_config):
    with SessionLocal() as session:
        simulation_service = SimulationBatchService(
            db=session,
            tickers=TICKERS,
            zero_time=ZERO_TIME,
            start_time=start_datetime,
            end_time=end_time,
            users_per_archetype=users_per_archetype,
            delta_days=delta_days,
            archetypes_config=archetypes_config

        )
        simulation_service.run_simulation()


def _nearest_power_of_two(value: float) -> int:
    if value <= 1:
        return 1

    lower_exp = int(log2(value))
    lower = 2 ** lower_exp
    upper = 2 ** (lower_exp + 1)
    return lower if abs(value - lower) <= abs(upper - value) else upper


def _derive_analysis_params(
    total_rows: int,
    *,
    n_clusters: int,
    top_percentile: float,
) -> tuple[int, int]:
    """
    Technical defaults derived from sample size, so the public API stays small.
    """
    k_neighbors = _nearest_power_of_two(total_rows ** 0.5)
    k_neighbors = max(64, min(512, k_neighbors))
    k_neighbors = min(k_neighbors, max(1, total_rows - 1))

    top_rows = max(1, round(total_rows * (1.0 - top_percentile)))
    min_cluster_size = max(25, round(top_rows / max(1, n_clusters * 10)))
    return k_neighbors, min_cluster_size


def run_archetype_discovery_pipeline(
    *,
    top_percentile: float = 0.95,
    max_clusters: int = 10,
    random_state: int = 42,
) -> dict:
    """
    Run robust scoring and GMM archetype extraction after a batch simulation.

    Exposed parameters are the strategic choices. Technical settings that depend
    on dataset size are inferred automatically from the number of analyzed users.
    """
    rows = load_results(DEFAULT_RESULTS_PATH)
    k_neighbors, _ = _derive_analysis_params(
        len(rows),
        n_clusters=1,
        top_percentile=top_percentile,
    )

    scored_rows = add_robust_scores(
        rows,
        k_neighbors=k_neighbors,
        hit_threshold=BENCHMARK_CHANGE_RATIO,
    )
    save_results(scored_rows, DEFAULT_ROBUST_OUTPUT_PATH)

    selected_n_clusters, bic_by_clusters = select_cluster_count_by_bic(
        scored_rows,
        top_percentile=top_percentile,
        min_clusters=2,
        max_clusters=max_clusters,
        random_state=random_state,
    )
    _, min_cluster_size = _derive_analysis_params(
        len(rows),
        n_clusters=selected_n_clusters,
        top_percentile=top_percentile,
    )

    archetypes = generate_gmm_archetypes(
        scored_rows,
        n_clusters=selected_n_clusters,
        top_percentile=top_percentile,
        min_cluster_size=min_cluster_size,
        random_state=random_state,
    )
    for archetype in archetypes.values():
        archetype["metadata"]["bic_by_clusters"] = {
            str(k): round(v, 6) for k, v in bic_by_clusters.items()
        }
    save_json(archetypes, DEFAULT_GMM_OUTPUT_PATH)

    return {
        "rows_analyzed": len(rows),
        "k_neighbors": k_neighbors,
        "min_cluster_size": min_cluster_size,
        "selected_n_clusters": selected_n_clusters,
        "bic_by_clusters": {str(k): round(v, 6) for k, v in bic_by_clusters.items()},
        "robust_results_path": str(DEFAULT_ROBUST_OUTPUT_PATH),
        "gmm_output_path": str(DEFAULT_GMM_OUTPUT_PATH),
        "archetypes_count": len(archetypes),
    }
