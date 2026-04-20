from __future__ import annotations

import numpy as np
import pandas as pd

from ..B_interpret.need_signal import infer_need_buy_flag_from_context
from .explain_memo import build_decision_reason, build_additional_check_reason


def _resolve_need_buy_flag(row: pd.Series) -> int:
    return infer_need_buy_flag_from_context(row)


def map_final_action(decision_master_df: pd.DataFrame, best_candidate_df: pd.DataFrame) -> pd.DataFrame:
    final_df = decision_master_df.merge(best_candidate_df, on="decision_id", how="left").copy()
    final_df["need_buy_flag"] = final_df.apply(_resolve_need_buy_flag, axis=1)

    conditions = [
        (final_df["need_buy_flag"] == 1)
        & (final_df["selected_candidate_name"] != "observe")
        & (final_df["selected_candidate_status"].isin(["feasible", "conditional"]))
        & (final_df["selected_robust_no_shortage_all_scenarios"] == 1),
        (final_df["need_buy_flag"] == 0) & (final_df["selected_candidate_name"] == "observe"),
    ]
    choices = ["선매입 검토", "관망"]
    final_df["final_action"] = np.select(conditions, choices, default="추가확인")
    final_df["final_reason"] = final_df.apply(build_decision_reason, axis=1)
    final_df["additional_check_reason"] = np.where(
        final_df["final_action"] == "추가확인",
        final_df.apply(build_additional_check_reason, axis=1),
        "",
    )

    output_cols = [
        "decision_id", "decision_month", "material_code",
        "target_a_rule", "target_b_rule",
        "target_a_pred", "target_b_pred",
        "target_a_final_pred", "target_b_final_pred",
        "need_buy_flag",
        "selected_candidate_name", "selected_candidate_qty_ton", "selected_candidate_status",
        "selected_robust_no_shortage_all_scenarios",
        "selected_worst_case_shortage_ton",
        "selected_worst_case_cost_vs_observe_pct",
        "selected_worst_case_min_ending_inventory_ton",
        "selected_hard_fail_reason", "selected_soft_warning_reason",
        "selected_working_capital_gate_result", "selected_arrival_timing_gate_result",
        "required_candidate_qty_ton", "required_candidate_status",
        "required_candidate_hard_fail_reason", "required_candidate_soft_warning_reason",
        "final_action", "final_reason", "additional_check_reason",
    ]

    output_cols = [col for col in output_cols if col in final_df.columns]
    return final_df[output_cols]