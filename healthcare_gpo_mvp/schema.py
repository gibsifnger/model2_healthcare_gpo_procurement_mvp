REQUIRED_COLUMNS = [
    "item_id",
    "item_name",
    "category",
    "annual_spend",
    "contract_price",
    "market_price_index",
    "supplier_count",
    "supplier_otif",
    "lead_time_days",
    "emergency_purchase_ratio",
    "standardization_score",
    "substitute_available",
    "data_quality_score",
    "inventory_risk_score",
]

FINAL_OUTPUT_COLUMNS = [
    "item_id",
    "item_name",
    "category",
    "risk_summary",
    "recommended_action",
    "decision_reason",
    "priority_score",
]

CANDIDATE_ACTIONS = [
    "data_cleanup_first",
    "maintain_contract",
    "monitor_risk",
    "rebid",
    "annual_contract",
    "standardize_item",
    "dual_source",
    "review_substitute",
]

