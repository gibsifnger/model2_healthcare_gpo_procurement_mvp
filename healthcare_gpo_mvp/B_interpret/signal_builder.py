import pandas as pd

from healthcare_gpo_mvp import config


def build_signals(state_df: pd.DataFrame) -> pd.DataFrame:
    signal_df = state_df.copy()
    signal_df["data_cleanup_signal"] = signal_df["data_readiness"] == "fail"
    signal_df["cost_opportunity_signal"] = (
        (signal_df["spend_tier"] == "high")
        & (signal_df["price_pressure_score"] == "high")
    )
    signal_df["supply_control_risk_signal"] = (
        (signal_df["supplier_concentration_risk"] == "high")
        | (signal_df["delivery_risk"] == "high")
        | (signal_df["inventory_risk_level"] == "high")
    )
    signal_df["dual_source_signal"] = (
        (signal_df["supplier_count"] == 1)
        & (signal_df["supplier_otif"] < config.SUPPLIER_OTIF_MIN)
    )
    signal_df["standardize_signal"] = (
        signal_df["emergency_purchase_ratio"] >= config.EMERGENCY_PURCHASE_HIGH
    ) & (signal_df["standardization_score"] >= config.STANDARDIZATION_MIN)
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
    signal_df["monitor_signal"] = ~signal_df[major_signals].any(axis=1)
    return signal_df

