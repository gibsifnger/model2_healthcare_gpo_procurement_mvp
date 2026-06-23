"""
[FILE PURPOSE]
- 시뮬레이션 결과에서 각 품목(decision_month × item_id)별로 최종 추천 action을 선택하는 단계이다.
- 단순 최고점 선택이 아니라 사전 정의된 action 우선순위와 종합 점수를 조합해 실무적 우선순위를 도출한다.

[BUSINESS UNIT]
- 기본 판단 단위: 구매전략 판단월(decision_month) × 품목(item_id)
"""

import pandas as pd


# action 우선순위 맵: 동일 우선순위 점수일 경우 비즈니스 우선순위를 반영해 결정
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
    # gate에서 차단된 후보는 제외하고 선택 대상만 남긴다.
    selectable = simulation_df[simulation_df["gate_status"] != "blocked"].copy()
    if selectable.empty:
        raise ValueError("No selectable candidate actions remain after gate checks.")

    # 우선순위 점수와 action 우선순위 맵을 조합해 최종 선택
    selectable["action_rank"] = selectable["candidate_action"].map(ACTION_PRIORITY)
    selected = (
        selectable.sort_values(
            ["decision_month", "item_id", "priority_score", "action_rank"],
            ascending=[True, True, False, True],
        )
        .groupby(["decision_month", "item_id"], as_index=False)
        .head(1)
        .copy()
    )
    selected["recommended_action"] = selected["candidate_action"]
    selected["selection_reason"] = selected.apply(_selection_reason, axis=1)
    return selected[
        [
            "decision_month",
            "item_id",
            "item_name",
            "category",
            "recommended_action",
            "priority_score",
            "selection_reason",
        ]
    ]


def _selection_reason(row: pd.Series) -> str:
    # 선택 사유: 우선순위 점수와 gate 상태를 함께 제공해 현업에서 해석 가능하도록 함
    return (
        f"Selected by priority score {row['priority_score']:.3f} "
        f"with gate status '{row['gate_status']}'."
    )
