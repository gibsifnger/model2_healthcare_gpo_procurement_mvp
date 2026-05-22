import pandas as pd

from healthcare_gpo_mvp.schema import FINAL_OUTPUT_COLUMNS


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
    context = signal_df[
        [
            "item_id",
            "price_pressure_score",
            "supplier_concentration_risk",
            "delivery_risk",
            "exception_purchase_risk",
            "inventory_risk_level",
            "data_readiness",
        ]
    ]
    final_df = selection_df.merge(context, on="item_id", how="left")
    final_df["risk_summary"] = final_df.apply(_risk_summary, axis=1)
    final_df["decision_reason"] = final_df["recommended_action"].map(ACTION_REASONS)
    return final_df[FINAL_OUTPUT_COLUMNS].sort_values(
        ["priority_score", "item_id"], ascending=[False, True]
    )


def _risk_summary(row: pd.Series) -> str:
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

