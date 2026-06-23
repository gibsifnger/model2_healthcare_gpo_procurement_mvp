"""
[FILE PURPOSE]
- 최종 선택된 action을 현업 담당자가 이해할 수 있는 추천 사유 및 리스크 요약으로 변환하는 단계이다.
- 모델의 결정 로그를 사람이 해석 가능한 설명으로 바꿔 포트폴리오 의사결정에 활용하도록 한다.

[BUSINESS UNIT]
- 기본 판단 단위: 구매전략 판단월(decision_month) × 품목(item_id)
"""

import pandas as pd

from healthcare_gpo_mvp.schema import FINAL_OUTPUT_COLUMNS


# 추천 사유 맵: 각 action이 왜 추천되었는지를 설명하는 현업용 문구
ACTION_REASONS = {
    "data_cleanup_first": "데이터 품질 점수가 낮아 계약/소싱 판단보다 품목·공급사·단가 데이터 정비가 우선입니다.",
    "dual_source": "공급사 의존도가 높고 납기 안정성이 낮아 공급사 이원화 검토가 필요합니다.",
    "review_substitute": "재고부족 위험이 높고 대체품이 존재하므로 대체품 검토가 필요합니다.",
    "standardize_item": "긴급구매 비중이 높고 표준화 가능성이 높아 표준품목 전환 검토가 필요합니다.",
    "rebid": "연간 구매금액과 시장가 압박이 높아 재입찰 또는 가격 재검토가 필요합니다.",
    "annual_contract": "반복 구매와 가격 변동성이 있어 연간단가계약 검토가 필요합니다.",
    "monitor_risk": "주요 위험 신호는 낮지만 납기·가격·재고 지표를 지속 모니터링해야 합니다.",
    "maintain_contract": "가격, 납기, 공급 안정성이 양호하여 기존 계약 유지가 가능합니다.",
}


def translate_actions(selection_df: pd.DataFrame, signal_df: pd.DataFrame) -> pd.DataFrame:
    # 필요한 컨텍스트(신호)를 결합해 리스크 요약과 추천 사유를 생성
    context = signal_df[
        [
            "decision_month",
            "item_id",
            "price_pressure_score",
            "supplier_concentration_risk",
            "delivery_risk",
            "exception_purchase_risk",
            "inventory_risk_level",
            "data_readiness",
        ]
    ]
    final_df = selection_df.merge(
        context, on=["decision_month", "item_id"], how="left"
    )
    final_df["risk_summary"] = final_df.apply(_risk_summary, axis=1)
    final_df["decision_reason"] = final_df["recommended_action"].map(ACTION_REASONS)
    return final_df[FINAL_OUTPUT_COLUMNS].sort_values(
        ["priority_score", "decision_month", "item_id"], ascending=[False, True, True]
    )


def _risk_summary(row: pd.Series) -> str:
    # 리스크 요약은 표준화된 키워드로 재무/공급/운영 리스크를 압축해 제공
    risks = []
    if row["data_readiness"] == "fail":
        risks.append("데이터 정비 필요")
    if row["price_pressure_score"] == "high":
        risks.append("가격 압박 높음")
    if row["supplier_concentration_risk"] == "high":
        risks.append("공급사 집중 위험")
    if row["delivery_risk"] == "high":
        risks.append("납기 위험")
    if row["exception_purchase_risk"] == "high":
        risks.append("긴급구매 비중 높음")
    if row["inventory_risk_level"] == "high":
        risks.append("재고부족 위험 높음")
    return ", ".join(risks) if risks else "주요 위험 낮음"
