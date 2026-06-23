"""
[FILE PURPOSE]
- 상태값(state_df)을 비용절감 기회(cost_opportunity_signal)와 공급통제 리스크(supply_control_risk_signal)로 해석하는 단계이다.
- 비용기회와 공급리스크를 분리하는 이유는, 단순 절감 가능성만으로 실행하면 공급 안정성 문제를 초래할 수 있기 때문이다.

[BUSINESS UNIT]
- 기본 판단 단위: 구매전략 판단월(decision_month) × 품목(item_id)
"""

import pandas as pd

from healthcare_gpo_mvp import config


# ============================================================
# [BLOCK] 신호 해석 (B_interpret)
# [현업 의미] 상태값을 실무적 의사결정 신호로 변환한다. 예: 데이터 정비 필요, 절감 기회, 공급 안정성 리스크 등
# [판단 기준] 연간 구매금액·시장가·공급사 수·납기율·재고위험·긴급구매 비중·표준화 가능성·대체품 존재 여부 등
# [산출물] signal_df (다음 단계에서 후보 action 생성을 위해 사용)
# [WHY] 절감 기회와 공급리스크는 서로 충돌할 수 있으므로 분리해 고려해야 한다. 예컨대 단가가 낮더라도 납기·재고 리스크가 크면 별도 관리가 필요하다.
# ============================================================
def build_signals(state_df: pd.DataFrame) -> pd.DataFrame:
    signal_df = state_df.copy()
    # 데이터 정비 필요 신호: 데이터 품질이 낮으면 데이터 정비를 우선 action으로 분리
    signal_df["data_cleanup_signal"] = signal_df["data_readiness"] == "fail"
    # 비용 절감 기회: 고액 구매이면서 시장가 압박이 있는 경우 재입찰/단가 재검토 후보가 될 수 있음
    signal_df["cost_opportunity_signal"] = (
        (signal_df["spend_tier"] == "high")
        & (signal_df["price_pressure_score"] == "high")
    )
    # 공급 통제 리스크: 공급사 집중, 납기 문제, 재고 위험이 있는 경우 공급 안정성 확보가 우선
    signal_df["supply_control_risk_signal"] = (
        (signal_df["supplier_concentration_risk"] == "high")
        | (signal_df["delivery_risk"] == "high")
        | (signal_df["inventory_risk_level"] == "high")
    )
    # 이원화 후보 신호: 단일 공급사이면서 OTIF가 낮아 공급 안정성 확보가 필요하다고 판단되는 경우
    signal_df["dual_source_signal"] = (
        (signal_df["supplier_count"] == 1)
        & (signal_df["supplier_otif"] < config.SUPPLIER_OTIF_MIN)
    )
    # 표준화 후보 신호: 긴급구매 비중과 표준화 점수를 고려해 표준화 실행 가능성 판단
    signal_df["standardize_signal"] = (
        signal_df["emergency_purchase_ratio"] >= config.EMERGENCY_PURCHASE_HIGH
    ) & (signal_df["standardization_score"] >= config.STANDARDIZATION_MIN)
    # 대체품 검토 신호: 재고 위험이 높고 대체품이 확인된 경우
    signal_df["substitute_signal"] = (
        signal_df["inventory_risk_score"] >= config.INVENTORY_RISK_HIGH
    ) & (signal_df["substitute_available"] == 1)

    major_signals = [
        "data_cleanup_signal",
        "cost_opportunity_signal",
        "supply_control_risk_signal",
        "dual_source_signal",
        "standardize_signal",
        "substitute_signal",
    ]
    # 모니터 신호: 위 주요 신호들에 해당하지 않는 품목은 우선 관찰 대상으로 분류
    signal_df["monitor_signal"] = ~signal_df[major_signals].any(axis=1)
    return signal_df

