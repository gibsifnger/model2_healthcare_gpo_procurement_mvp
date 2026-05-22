import pandas as pd

from healthcare_gpo_mvp import config


def apply_gates(candidate_df: pd.DataFrame, signal_df: pd.DataFrame) -> pd.DataFrame:
    context_columns = [
        "decision_month",
        "item_id",
        "data_quality_score",
        "substitute_available",
        "standardization_score",
        "supplier_count",
        "supplier_otif",
    ]
    gated_df = candidate_df.merge(
        signal_df[context_columns], on=["decision_month", "item_id"], how="left"
    )
    gate_results = gated_df.apply(_gate_row, axis=1, result_type="expand")
    gated_df["gate_status"] = gate_results["gate_status"]
    gated_df["gate_reason"] = gate_results["gate_reason"]
    return gated_df


def _gate_row(row: pd.Series) -> dict:
    action = row["candidate_action"]

    if row["data_quality_score"] < config.DATA_QUALITY_MIN:
        if action == "data_cleanup_first":
            return {
                "gate_status": "pass",
                "gate_reason": "Data quality is below threshold, so cleanup is the first executable action.",
            }
        return {
            "gate_status": "blocked",
            "gate_reason": "Data quality is below threshold; strategic action is blocked until cleanup.",
        }

    if action == "review_substitute" and int(row["substitute_available"]) == 0:
        return {
            "gate_status": "blocked",
            "gate_reason": "No substitute item is available.",
        }
    if action == "standardize_item" and row["standardization_score"] < config.STANDARDIZATION_MIN:
        return {
            "gate_status": "blocked",
            "gate_reason": "Standardization score is below threshold.",
        }
    if (
        action == "dual_source"
        and row["supplier_count"] >= 2
        and row["supplier_otif"] >= config.SUPPLIER_OTIF_MIN
    ):
        return {
            "gate_status": "deprioritized",
            "gate_reason": "Supplier base and delivery reliability are already acceptable.",
        }

    return {
        "gate_status": "pass",
        "gate_reason": "Candidate action passed operating gate checks.",
    }
