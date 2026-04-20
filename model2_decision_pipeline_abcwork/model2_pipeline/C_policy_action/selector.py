from __future__ import annotations

import pandas as pd

from ..B_interpret.need_signal import infer_need_buy_flag_from_context


def infer_need_buy_flag(row: pd.Series) -> int:
    return infer_need_buy_flag_from_context(row)


def select_best_candidate(
    decision_master_df: pd.DataFrame,
    robust_summary_df: pd.DataFrame,
) -> pd.DataFrame:
    decision_map = decision_master_df.set_index("decision_id")
    status_rank_map = {"feasible": 0, "conditional": 1, "blocked": 9}

    picks = []

    for decision_id, group in robust_summary_df.groupby("decision_id"):
        decision_row = decision_map.loc[decision_id]
        need_buy_flag = infer_need_buy_flag(decision_row)

        group = group.copy()
        group["status_rank"] = group["candidate_status"].map(status_rank_map).fillna(9)
        group["qty_rank"] = group["candidate_qty_ton"]

        if need_buy_flag == 1:
            eligible = group[
                (group["candidate_status"] != "blocked")
                & (group["candidate_qty_ton"] > 0)
            ].copy()

            if eligible.empty:
                chosen = group.sort_values(
                    [
                        "status_rank",
                        "worst_case_shortage_ton",
                        "worst_case_cost_vs_observe_pct",
                        "qty_rank",
                    ],
                    ascending=[True, True, True, True],
                ).iloc[0]
            else:
                robust_eligible = eligible[
                    eligible["robust_no_shortage_all_scenarios"] == 1
                ].copy()
                pool = robust_eligible if not robust_eligible.empty else eligible

                chosen = pool.sort_values(
                    [
                        "status_rank",
                        "worst_case_cost_vs_observe_pct",
                        "worst_case_shortage_ton",
                        "qty_rank",
                    ],
                    ascending=[True, True, True, True],
                ).iloc[0]
        else:
            observe = group[group["candidate_name"] == "observe"]
            chosen = (
                observe.iloc[0]
                if not observe.empty
                else group.sort_values(["status_rank", "qty_rank"]).iloc[0]
            )

        picks.append(
            {
                "decision_id": decision_id,
                "selected_candidate_name": chosen["candidate_name"],
                "selected_candidate_qty_ton": chosen["candidate_qty_ton"],
                "selected_candidate_status": chosen["candidate_status"],
                "selected_robust_no_shortage_all_scenarios": chosen[
                    "robust_no_shortage_all_scenarios"
                ],
                "selected_worst_case_shortage_ton": chosen[
                    "worst_case_shortage_ton"
                ],
                "selected_worst_case_cost_vs_observe_pct": chosen[
                    "worst_case_cost_vs_observe_pct"
                ],
                "selected_worst_case_min_ending_inventory_ton": chosen[
                    "worst_case_min_ending_inventory_ton"
                ],
            }
        )

    return pd.DataFrame(picks)