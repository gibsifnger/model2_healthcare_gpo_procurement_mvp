import pandas as pd


def build_candidates(signal_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in signal_df.iterrows():
        item = {
            "item_id": row["item_id"],
            "item_name": row["item_name"],
            "category": row["category"],
        }
        if row["data_cleanup_signal"]:
            rows.append(_candidate(item, "data_cleanup_first", "Data readiness failed."))
        if row["cost_opportunity_signal"]:
            rows.append(_candidate(item, "rebid", "High spend and high market price pressure."))
            rows.append(_candidate(item, "annual_contract", "High spend item needs contract leverage."))
        if row["dual_source_signal"]:
            rows.append(_candidate(item, "dual_source", "Single supplier with low delivery reliability."))
        if row["standardize_signal"]:
            rows.append(_candidate(item, "standardize_item", "Emergency purchasing and standardization opportunity are high."))
        if row["substitute_signal"]:
            rows.append(_candidate(item, "review_substitute", "High inventory risk with substitute availability."))
        if row["monitor_signal"]:
            if _is_stable_contract(row):
                rows.append(_candidate(item, "maintain_contract", "Core price, delivery, and inventory indicators are stable."))
            else:
                rows.append(_candidate(item, "monitor_risk", "No major action trigger, but KPI monitoring is needed."))
        if not any(candidate["item_id"] == row["item_id"] for candidate in rows):
            rows.append(_candidate(item, "monitor_risk", "No dominant action trigger was detected."))

    return pd.DataFrame(rows)


def _candidate(item: dict, action: str, reason: str) -> dict:
    return {
        **item,
        "candidate_action": action,
        "candidate_reason": reason,
    }


def _is_stable_contract(row: pd.Series) -> bool:
    return (
        row["price_pressure_score"] == "normal"
        and row["delivery_risk"] == "low"
        and row["inventory_risk_level"] == "low"
        and row["exception_purchase_risk"] == "low"
    )

