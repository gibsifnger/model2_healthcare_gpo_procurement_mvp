"""
[FILE PURPOSE]
- 후보 action별 KPI(절감 가능성, 공급 리스크 감소, 운영 안정성)를 모의(simulation)하여 우선순위 점수(priority_score)를 산출한다.
- 단순 절감액만 보는 것이 아니라 공급 안정성·운영 안정성·데이터 신뢰성까지 반영해 포트폴리오 관점의 우선순위를 계산한다.

[BUSINESS UNIT]
- 기본 판단 단위: 구매전략 판단월(decision_month) × 품목(item_id)
"""

import numpy as np
import pandas as pd


# ============================================================
# [BLOCK] KPI 시뮬레이션 (C_policy_action)
# [현업 의미] 후보 action을 절감효과(cost), 공급리스크 완화(supply), 운영 안정성(stability) 관점으로 정량화해
# 우선순위 점수(priority_score)를 산출한다.
# [판단 기준] 연간 구매금액, 시장가, 공급사 OTIF, 긴급구매 비중, 표준화 점수, 대체품 존재 여부, 데이터 품질, 재고 위험 등
# [산출물] simulation_result_df (각 후보별 KPI 점수와 priority_score)
# [WHY] 여러 KPI를 합산해 단순 절감액이 아닌 종합적인 구매전략 우선순위를 계산하기 위해
# ============================================================
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
    context = signal_df[["decision_month", "item_id", *missing_context]]
    simulation_df = gated_candidate_df.merge(
        context, on=["decision_month", "item_id"], how="left"
    )
    # 각 후보에 대해 KPI 점수를 산출
    scores = simulation_df.apply(_score_row, axis=1, result_type="expand")
    for column in scores.columns:
        simulation_df[column] = scores[column]

    # gate에서 차단된 후보의 우선순위는 0으로 설정, deprioritized는 우선순위 감소
    blocked = simulation_df["gate_status"] == "blocked"
    simulation_df.loc[blocked, "priority_score"] = 0.0
    deprioritized = simulation_df["gate_status"] == "deprioritized"
    simulation_df.loc[deprioritized, "priority_score"] *= 0.5
    simulation_df["priority_score"] = simulation_df["priority_score"].round(3)
    return simulation_df


def _score_row(row: pd.Series) -> dict:
    action = row["candidate_action"]
    # 지표 정규화/스케일링: 연간 구매금액, 시장가 차이, OTIF 등으로 기본 계수를 계산
    spend_factor = min(row["annual_spend"] / 150000000, 1.0)
    price_factor = min(max(row["market_price_index"] - 1.0, 0.0) / 0.15, 1.0)
    otif_factor = min(max(0.0, 0.95 - row["supplier_otif"]) / 0.2, 1.0)

    cost = 0.0
    supply = 0.0
    stability = 0.0

    # 각 action별로 절감·공급·안정성 기여도를 규칙 기반으로 계산
    if action == "rebid":
        # 재입찰은 비용 절감 중심
        cost = 0.7 * spend_factor + 0.3 * price_factor
    elif action == "annual_contract":
        # 연간계약은 비용 절감과 일부 안정성 기여
        cost = 0.45 * spend_factor + 0.35 * price_factor
        stability = 0.2
    elif action == "dual_source":
        # 이원화는 공급 안정성 개선 중심
        supply = (1.0 if row["supplier_count"] == 1 else 0.4) * 0.6 + otif_factor * 0.4
    elif action == "standardize_item":
        # 표준화는 긴급구매 완화와 표준화 점수 기반 안정성 기여
        stability = min(row["emergency_purchase_ratio"] / 0.25, 1.0) * 0.55 + row["standardization_score"] * 0.45
    elif action == "review_substitute":
        # 대체품 검토는 재고 위험을 낮추는 효과를 가정
        supply = row["inventory_risk_score"] * (1.0 if row["substitute_available"] == 1 else 0.0)
    elif action == "data_cleanup_first":
        # 데이터 정비는 우선적으로 데이터 신뢰도를 회복시켜 다른 전략 실행을 가능하게 함
        stability = min((1.0 - row["data_quality_score"]) / 0.5, 1.0)
    elif action == "monitor_risk":
        # 모니터링은 낮은 수준의 안정성 점수를 부여
        stability = 0.25 + row["inventory_risk_score"] * 0.2
    elif action == "maintain_contract":
        # 계약 유지 시 안정성 점수 기반 유지
        stability = 0.2

    # 종합 우선순위 점수: 비용·공급·안정성 가중 합
    priority = float(np.clip(0.45 * cost + 0.35 * supply + 0.20 * stability, 0.0, 1.0))
    if action == "data_cleanup_first":
        priority = max(priority, stability)

    return {
        "cost_saving_opportunity": round(float(cost), 3),
        "supply_risk_reduction": round(float(supply), 3),
        "operation_stability_score": round(float(stability), 3),
        "priority_score": round(float(priority), 3),
    }
