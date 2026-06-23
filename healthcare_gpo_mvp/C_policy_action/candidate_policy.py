"""
[FILE PURPOSE]
- 신호(signal_df)를 바탕으로 구매전략 후보 action을 생성하는 단계이다.
- 각 후보는 구매전략 관점에서 "왜" 생성되었는지를 명확히 하기 위해 후보 사유(candidiate_reason)를 포함한다.

[BUSINESS UNIT]
- 기본 판단 단위: 구매전략 판단월(decision_month) × 품목(item_id)
"""

import pandas as pd


# ============================================================
# [BLOCK] 후보 Action 생성 (C_policy_action)
# [현업 의미] 신호를 해석해 재입찰, 연간계약, 표준화, 이원화, 대체품검토, 데이터정비 등 실행 가능한 후보 action을 생성한다.
# [판단 기준] 데이터 신뢰도 우선, 비용절감 기회, 공급 안정성 리스크, 표준화·대체품 준비도, 계약 안정성 등
# [산출물] candidate_df (action 후보와 후보 사유 포함)
# [WHY] 후보 단계에서 여러 대안을 병렬로 검토하면 gate에서 실행 가능성을 따져 보다 현실적인 실행안을 도출할 수 있다.
# ============================================================
def build_candidates(signal_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in signal_df.iterrows():
        item = {
            "decision_month": row["decision_month"],
            "item_id": row["item_id"],
            "item_name": row["item_name"],
            "category": row["category"],
        }
        # 데이터 품질 문제는 우선 데이터 정비 action으로 분리
        if row["data_cleanup_signal"]:
            rows.append(_candidate(item, "data_cleanup_first", "Data readiness failed."))
        # 비용 절감 기회: 재입찰 또는 연간계약으로 절감/레버리지 확보를 동시에 고려
        if row["cost_opportunity_signal"]:
            rows.append(_candidate(item, "rebid", "High spend and high market price pressure."))
            rows.append(_candidate(item, "annual_contract", "High spend item needs contract leverage."))
        # 공급사 이원화 후보: 단일공급사 + 낮은 납기 신뢰도
        if row["dual_source_signal"]:
            rows.append(_candidate(item, "dual_source", "Single supplier with low delivery reliability."))
        # 표준화 후보: 긴급구매가 발생하면서 표준화 가능성이 있는 경우
        if row["standardize_signal"]:
            rows.append(_candidate(item, "standardize_item", "Emergency purchasing and standardization opportunity are high."))
        # 대체품 검토 후보: 재고 위험이 높고 대체품이 준비된 경우
        if row["substitute_signal"]:
            rows.append(_candidate(item, "review_substitute", "High inventory risk with substitute availability."))
        # 모니터 신호에 대해 안정적 계약이면 유지, 아니면 모니터링을 후보로 둠
        if row["monitor_signal"]:
            if _is_stable_contract(row):
                rows.append(_candidate(item, "maintain_contract", "Core price, delivery, and inventory indicators are stable."))
            else:
                rows.append(_candidate(item, "monitor_risk", "No major action trigger, but KPI monitoring is needed."))
        # 만약 어떤 후보도 추가되지 않았다면 모니터링을 기본 후보로 추가
        if not any(
            candidate["decision_month"] == row["decision_month"]
            and candidate["item_id"] == row["item_id"]
            for candidate in rows
        ):
            rows.append(_candidate(item, "monitor_risk", "No dominant action trigger was detected."))

    return pd.DataFrame(rows)


def _candidate(item: dict, action: str, reason: str) -> dict:
    return {
        **item,
        "candidate_action": action,
        "candidate_reason": reason,
    }


def _is_stable_contract(row: pd.Series) -> bool:
    # 가격·납기·재고·예외구매 지표가 모두 안정적이면 기존 계약 유지 후보로 분류
    return (
        row["price_pressure_score"] == "normal"
        and row["delivery_risk"] == "low"
        and row["inventory_risk_level"] == "low"
        and row["exception_purchase_risk"] == "low"
    )
