import pandas as pd


ACTION_PRIORITY = {
    "data_cleanup_first": 1,
    "dual_source": 2,
    "review_substitute": 3,
    "standardize_item": 4,
    "rebid": 5,
    "annual_contract": 6,
    "monitor_risk": 7,
    "maintain_contract": 8,
}


def select_final_actions(simulation_df: pd.DataFrame) -> pd.DataFrame:
    selectable = simulation_df[simulation_df["gate_status"] != "blocked"].copy()
    if selectable.empty:
        raise ValueError("No selectable candidate actions remain after gate checks.")

    selectable["action_rank"] = selectable["candidate_action"].map(ACTION_PRIORITY)
    selected = (
        selectable.sort_values(
            ["item_id", "priority_score", "action_rank"],
            ascending=[True, False, True],
        )
        .groupby("item_id", as_index=False)
        .head(1)
        .copy()
    )
    selected["recommended_action"] = selected["candidate_action"]
    selected["selection_reason"] = selected.apply(_selection_reason, axis=1)
    return selected[
        [
            "item_id",
            "item_name",
            "category",
            "recommended_action",
            "priority_score",
            "selection_reason",
        ]
    ]


def _selection_reason(row: pd.Series) -> str:
    return (
        f"Selected by priority score {row['priority_score']:.3f} "
        f"with gate status '{row['gate_status']}'."
    )

