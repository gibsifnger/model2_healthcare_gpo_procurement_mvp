import pandas as pd

from healthcare_gpo_mvp import config
from healthcare_gpo_mvp.schema import REQUIRED_COLUMNS


def validate_input(df: pd.DataFrame) -> None:
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def build_state(input_csv: str) -> pd.DataFrame:
    df = pd.read_csv(input_csv, encoding="utf-8")
    validate_input(df)

    state_df = df.copy()
    state_df["spend_tier"] = state_df["annual_spend"].apply(_spend_tier)
    state_df["price_pressure_score"] = state_df["market_price_index"].apply(
        lambda value: "high" if value >= config.MARKET_PRICE_PRESSURE_HIGH else "normal"
    )
    state_df["supplier_concentration_risk"] = state_df["supplier_count"].apply(
        _supplier_concentration_risk
    )
    state_df["delivery_risk"] = state_df.apply(_delivery_risk, axis=1)
    state_df["exception_purchase_risk"] = state_df["emergency_purchase_ratio"].apply(
        lambda value: "high" if value >= config.EMERGENCY_PURCHASE_HIGH else "low"
    )
    state_df["standardization_opportunity"] = state_df["standardization_score"].apply(
        lambda value: "high" if value >= config.STANDARDIZATION_MIN else "low"
    )
    state_df["substitute_readiness"] = state_df["substitute_available"].apply(
        lambda value: "available" if int(value) == 1 else "unavailable"
    )
    state_df["data_readiness"] = state_df["data_quality_score"].apply(
        lambda value: "pass" if value >= config.DATA_QUALITY_MIN else "fail"
    )
    state_df["inventory_risk_level"] = state_df["inventory_risk_score"].apply(
        _inventory_risk_level
    )
    return state_df


def _spend_tier(annual_spend: float) -> str:
    if annual_spend >= config.HIGH_SPEND_THRESHOLD:
        return "high"
    if annual_spend >= config.MID_SPEND_THRESHOLD:
        return "mid"
    return "low"


def _supplier_concentration_risk(supplier_count: int) -> str:
    if supplier_count <= 1:
        return "high"
    if supplier_count == 2:
        return "medium"
    return "low"


def _delivery_risk(row: pd.Series) -> str:
    if (
        row["supplier_otif"] < config.SUPPLIER_OTIF_MIN
        or row["lead_time_days"] >= config.LONG_LEAD_TIME_DAYS
    ):
        return "high"
    return "low"


def _inventory_risk_level(score: float) -> str:
    if score >= config.INVENTORY_RISK_HIGH:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"

