import numpy as np
import pandas as pd


def simulate_actions(gated_candidate_df: pd.DataFrame, signal_df: pd.DataFrame) -> pd.DataFrame:
    context_columns = [
        "annual_spend",
        "market_price_index",
        "supplier_count",
        "supplier_otif",
        "emergency_purchase_ratio",
        "standardization_score",
        "substitute_available",
        "data_quality_score",
        "inventory_risk_score",
    ]
    missing_context = [
        column for column in context_columns if column not in gated_candidate_df.columns
    ]
    context = signal_df[["item_id", *missing_context]]
    simulation_df = gated_candidate_df.merge(context, on="item_id", how="left")
    scores = simulation_df.apply(_score_row, axis=1, result_type="expand")
    for column in scores.columns:
        simulation_df[column] = scores[column]

    blocked = simulation_df["gate_status"] == "blocked"
    simulation_df.loc[blocked, "priority_score"] = 0.0
    deprioritized = simulation_df["gate_status"] == "deprioritized"
    simulation_df.loc[deprioritized, "priority_score"] *= 0.5
    simulation_df["priority_score"] = simulation_df["priority_score"].round(3)
    return simulation_df


def _score_row(row: pd.Series) -> dict:
    action = row["candidate_action"]
    spend_factor = min(row["annual_spend"] / 150000000, 1.0)
    price_factor = min(max(row["market_price_index"] - 1.0, 0.0) / 0.15, 1.0)
    otif_factor = min(max(0.0, 0.95 - row["supplier_otif"]) / 0.2, 1.0)

    cost = 0.0
    supply = 0.0
    stability = 0.0

    if action == "rebid":
        cost = 0.7 * spend_factor + 0.3 * price_factor
    elif action == "annual_contract":
        cost = 0.45 * spend_factor + 0.35 * price_factor
        stability = 0.2
    elif action == "dual_source":
        supply = (1.0 if row["supplier_count"] == 1 else 0.4) * 0.6 + otif_factor * 0.4
    elif action == "standardize_item":
        stability = min(row["emergency_purchase_ratio"] / 0.25, 1.0) * 0.55 + row["standardization_score"] * 0.45
    elif action == "review_substitute":
        supply = row["inventory_risk_score"] * (1.0 if row["substitute_available"] == 1 else 0.0)
    elif action == "data_cleanup_first":
        stability = min((1.0 - row["data_quality_score"]) / 0.5, 1.0)
    elif action == "monitor_risk":
        stability = 0.25 + row["inventory_risk_score"] * 0.2
    elif action == "maintain_contract":
        stability = 0.2

    priority = float(np.clip(0.45 * cost + 0.35 * supply + 0.20 * stability, 0.0, 1.0))
    if action == "data_cleanup_first":
        priority = max(priority, stability)

    return {
        "cost_saving_opportunity": round(float(cost), 3),
        "supply_risk_reduction": round(float(supply), 3),
        "operation_stability_score": round(float(stability), 3),
        "priority_score": round(float(priority), 3),
    }
