"""
[FILE PURPOSE]
- 후보 action의 실행 가능성을 실무적 관점에서 검토하는 gate 로직을 포함한다.
- 데이터 품질, 대체품 존재, 표준화 가능성, 공급 안정성 등을 기준으로 실행 가능 여부를 차단(block), 보류(deprioritized), 통과(pass)로 나눈다.

[BUSINESS UNIT]
- 기본 판단 단위: 구매전략 판단월(decision_month) × 품목(item_id)
"""

import pandas as pd

from healthcare_gpo_mvp import config


def apply_gates(candidate_df: pd.DataFrame, signal_df: pd.DataFrame) -> pd.DataFrame:
    context_columns = [
        "decision_month",
        "item_id",
        "data_quality_score",
        "substitute_available",
        "standardization_score",
        "supplier_count",
        "supplier_otif",
    ]
    gated_df = candidate_df.merge(
        signal_df[context_columns], on=["decision_month", "item_id"], how="left"
    )
    # 각 후보에 대해 gate 판단을 수행하고 상태와 사유를 부여
    gate_results = gated_df.apply(_gate_row, axis=1, result_type="expand")
    gated_df["gate_status"] = gate_results["gate_status"]
    gated_df["gate_reason"] = gate_results["gate_reason"]
    return gated_df


def _gate_row(row: pd.Series) -> dict:
    action = row["candidate_action"]

    # 데이터 품질이 낮으면 모든 전략적 액션은 차단하고 데이터 정비만 허용
    if row["data_quality_score"] < config.DATA_QUALITY_MIN:
        if action == "data_cleanup_first":
            return {
                "gate_status": "pass",
                "gate_reason": "Data quality is below threshold, so cleanup is the first executable action.",
            }
        return {
            "gate_status": "blocked",
            "gate_reason": "Data quality is below threshold; strategic action is blocked until cleanup.",
        }

    # 대체품이 존재하지 않으면 대체품 검토 action은 실행 불가
    if action == "review_substitute" and int(row["substitute_available"]) == 0:
        return {
            "gate_status": "blocked",
            "gate_reason": "No substitute item is available.",
        }
    # 표준화 점수가 낮으면 표준화 action은 실행 불가
    if action == "standardize_item" and row["standardization_score"] < config.STANDARDIZATION_MIN:
        return {
            "gate_status": "blocked",
            "gate_reason": "Standardization score is below threshold.",
        }
    # 이미 공급사 기반과 납기 신뢰도가 양호하면 이원화는 우선순위 하향
    if (
        action == "dual_source"
        and row["supplier_count"] >= 2
        and row["supplier_otif"] >= config.SUPPLIER_OTIF_MIN
    ):
        return {
            "gate_status": "deprioritized",
            "gate_reason": "Supplier base and delivery reliability are already acceptable.",
        }

    return {
        "gate_status": "pass",
        "gate_reason": "Candidate action passed operating gate checks.",
    }
