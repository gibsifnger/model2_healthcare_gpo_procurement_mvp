from __future__ import annotations

import pandas as pd


def build_scenario_compare_summary(simulation_result_df: pd.DataFrame):
    scenario_summary_df = (
        simulation_result_df.groupby(
            ["decision_id", "candidate_name", "candidate_qty_ton", "candidate_status", "scenario_name"],
            as_index=False,
        )
        .agg(
            total_shortage_ton=("shortage_ton", "sum"),
            any_shortage_flag=("shortage_ton", lambda s: int((s > 0).any())),
            min_ending_inventory_ton=("ending_inventory_ton", "min"),
            total_cost=("total_month_cost", "sum"),
            total_emergency_buy_ton=("emergency_buy_ton", "sum"),
            last_ending_inventory_ton=("ending_inventory_ton", "last"),
        )
    )

    observe_ref = (
        scenario_summary_df[scenario_summary_df["candidate_name"] == "observe"]
        [["decision_id", "scenario_name", "total_cost"]]
        .rename(columns={"total_cost": "observe_total_cost"})
    )

    scenario_summary_df = scenario_summary_df.merge(
        observe_ref,
        on=["decision_id", "scenario_name"],
        how="left",
    )

    scenario_summary_df["cost_vs_observe_pct"] = (
        (scenario_summary_df["total_cost"] - scenario_summary_df["observe_total_cost"])
        / scenario_summary_df["observe_total_cost"]
    )

    robust_summary_df = (
        scenario_summary_df.groupby(
            ["decision_id", "candidate_name", "candidate_qty_ton", "candidate_status"],
            as_index=False,
        )
        .agg(
            scenario_count=("scenario_name", "nunique"),
            robust_no_shortage_all_scenarios=("any_shortage_flag", lambda s: int((s == 0).all())),
            worst_case_shortage_ton=("total_shortage_ton", "max"),
            worst_case_cost_vs_observe_pct=("cost_vs_observe_pct", "max"),
            worst_case_min_ending_inventory_ton=("min_ending_inventory_ton", "min"),
            avg_total_cost=("total_cost", "mean"),
        )
    )

    return scenario_summary_df, robust_summary_df