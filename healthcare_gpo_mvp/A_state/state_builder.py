"""
[FILE PURPOSE]
- 원천 구매 데이터를 구매전략 판단에 필요한 품목별 상태(state_df)로 변환하는 단계이다.
- 상태값들은 이후 비용기회 신호(cost_opportunity)와 공급통제 리스크 신호로 해석되어 후보 action 생성을 촉발한다.

[BUSINESS UNIT]
- 기본 판단 단위: 구매전략 판단월(decision_month) × 품목(item_id)

[INPUT]
- 입력 CSV는 `healthcare_gpo_mvp.schema.REQUIRED_COLUMNS`에 정의된 컬럼들을 포함해야 한다.

[OUTPUT]
- 반환값: state_df (원본 입력에 추가된 상태 컬럼들)
"""

import pandas as pd

from healthcare_gpo_mvp import config
from healthcare_gpo_mvp.schema import REQUIRED_COLUMNS


def validate_input(df: pd.DataFrame) -> None:
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


# ============================================================
# [BLOCK] 상태값 생성 (A_state)
# [현업 의미] 품목별 연간 구매금액, 시장가 압박, 공급사 수, 납기율, 긴급구매 비중,
# 표준화 가능성, 대체품 존재, 데이터 품질, 재고위험 등을 계산해 구매전략 판단에 필요한 상태를 만든다.
# [판단 기준] spend_tier, price_pressure_score, supplier_concentration_risk, delivery_risk,
# exception_purchase_risk, standardization_opportunity, substitute_readiness, data_readiness, inventory_risk_level
# [산출물] 다음 단계(B_interpret)로 넘기는 state_df
# [WHY] 상태값으로 변환하면 비즈니스 규칙으로 신호를 일관되게 해석할 수 있다.
# ============================================================
def build_state(input_csv: str) -> pd.DataFrame:
    df = pd.read_csv(input_csv, encoding="utf-8")
    validate_input(df)

    state_df = df.copy()
    # 연간 구매금액 구간화: 비용절감 우선순위 판단의 기초
    state_df["spend_tier"] = state_df["annual_spend"].apply(_spend_tier)
    # 시장가 압박: 현재 단가가 시장 대비 높은지 여부
    state_df["price_pressure_score"] = state_df["market_price_index"].apply(
        lambda value: "high" if value >= config.MARKET_PRICE_PRESSURE_HIGH else "normal"
    )
    # 공급사 집중 리스크: 공급사 수가 적을수록 공급중단/교섭력 문제 발생 가능
    state_df["supplier_concentration_risk"] = state_df["supplier_count"].apply(
        _supplier_concentration_risk
    )
    # 납기/리드타임 기반 공급 리스크 판단
    state_df["delivery_risk"] = state_df.apply(_delivery_risk, axis=1)
    # 긴급구매 비중: 긴급구매가 많으면 계약·발주 운영 통제가 필요할 수 있음
    state_df["exception_purchase_risk"] = state_df["emergency_purchase_ratio"].apply(
        lambda value: "high" if value >= config.EMERGENCY_PURCHASE_HIGH else "low"
    )
    # 표준화 기회: 품목의 표준화 가능성 유무(업무 수용성·규격 안정성 판단)
    state_df["standardization_opportunity"] = state_df["standardization_score"].apply(
        lambda value: "high" if value >= config.STANDARDIZATION_MIN else "low"
    )
    # 대체품 준비도: 대체품이 확인된 경우 대체품 검토 후보로 올릴 수 있음
    state_df["substitute_readiness"] = state_df["substitute_available"].apply(
        lambda value: "available" if int(value) == 1 else "unavailable"
    )
    # 데이터 신뢰도: 데이터 품질이 낮으면 가격협상보다 데이터 정비 우선
    state_df["data_readiness"] = state_df["data_quality_score"].apply(
        lambda value: "pass" if value >= config.DATA_QUALITY_MIN else "fail"
    )
    # 재고 위험 수준: 재고 관련 리스크가 높으면 공급 안정성 확보 우선 고려
    state_df["inventory_risk_level"] = state_df["inventory_risk_score"].apply(
        _inventory_risk_level
    )
    return state_df


def _spend_tier(annual_spend: float) -> str:
    # 고액 구매는 절감 효과가 크므로 우선순위 상향
    if annual_spend >= config.HIGH_SPEND_THRESHOLD:
        return "high"
    if annual_spend >= config.MID_SPEND_THRESHOLD:
        return "mid"
    return "low"


def _supplier_concentration_risk(supplier_count: int) -> str:
    # 공급사 수가 1이면 단일공급사 의존으로 리스크가 높다.
    if supplier_count <= 1:
        return "high"
    if supplier_count == 2:
        return "medium"
    return "low"


def _delivery_risk(row: pd.Series) -> str:
    # 정시정량 납기율이 낮거나 리드타임이 긴 경우 공급 안정성 확보가 우선이다.
    if (
        row["supplier_otif"] < config.SUPPLIER_OTIF_MIN
        or row["lead_time_days"] >= config.LONG_LEAD_TIME_DAYS
    ):
        return "high"
    return "low"


def _inventory_risk_level(score: float) -> str:
    # 재고 위험 점수가 높으면 재고·공급 리스크 관점에서 관리 필요
    if score >= config.INVENTORY_RISK_HIGH:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"

