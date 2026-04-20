from __future__ import annotations

import numpy as np
import pandas as pd


def _pick_first_present_int(row: pd.Series, candidates: list[str], default: int = 0) -> int:
    for col in candidates:
        if col in row.index and pd.notna(row.get(col)):
            return int(row.get(col))
    return int(default)


def build_decision_reason(row: pd.Series) -> str:
    parts = []
    if _pick_first_present_int(row, ["target_a_final_pred", "target_a_pred", "target_a_rule"], 0) == 1:
        parts.append("A-risk on")
    if _pick_first_present_int(row, ["target_b_final_pred", "target_b_pred", "target_b_rule"], 0) == 1:
        parts.append("B-risk on")

    parts.append(f"candidate={row['selected_candidate_name']}")
    parts.append(f"status={row['selected_candidate_status']}")
    parts.append(f"robust={int(row['selected_robust_no_shortage_all_scenarios'])}")
    parts.append(f"worst_shortage={row['selected_worst_case_shortage_ton']:.0f}t")
    return " | ".join(parts)


def build_additional_check_reason(row: pd.Series) -> str:
    reasons: list[str] = []

    selected_name = str(row.get("selected_candidate_name", ""))
    selected_status = str(row.get("selected_candidate_status", ""))
    required_status = str(row.get("required_candidate_status", ""))

    if int(row.get("need_buy_flag", 0)) == 1 and selected_name == "observe":
        reasons.append("위험은 있으나 실행 가능한 비관망 후보가 없음")

    if selected_status == "conditional":
        if str(row.get("selected_arrival_timing_gate_result", "")) == "conditional":
            reasons.append("선택후보 도착 타이밍이 타이트함")
        if str(row.get("selected_working_capital_gate_result", "")) == "conditional":
            reasons.append("선택후보 운전자본 압박이 높음")
        if isinstance(row.get("selected_soft_warning_reason"), str) and row.get("selected_soft_warning_reason"):
            reasons.append(f"선택후보 주의사유: {row.get('selected_soft_warning_reason')}")

    if selected_status == "blocked":
        if isinstance(row.get("selected_hard_fail_reason"), str) and row.get("selected_hard_fail_reason"):
            reasons.append(f"선택후보 실행불가: {row.get('selected_hard_fail_reason')}")
        else:
            reasons.append("선택후보 실행불가")

    if int(row.get("selected_robust_no_shortage_all_scenarios", 0)) == 0:
        reasons.append("전 시나리오 기준 robust하지 않음")

    worst_shortage = float(row.get("selected_worst_case_shortage_ton", 0.0) or 0.0)
    if worst_shortage > 0:
        reasons.append(f"선택후보로도 worst-case shortage {worst_shortage:.0f}톤이 남음")

    required_qty = row.get("required_candidate_qty_ton", np.nan)
    if pd.notna(required_qty):
        if required_status == "blocked":
            hard_reason = str(row.get("required_candidate_hard_fail_reason", "")).strip()
            if hard_reason:
                reasons.append(f"필요수량 후보({float(required_qty):.0f}톤)는 실행불가: {hard_reason}")
            else:
                reasons.append(f"필요수량 후보({float(required_qty):.0f}톤)는 실행불가")
        elif required_status == "conditional":
            soft_reason = str(row.get("required_candidate_soft_warning_reason", "")).strip()
            if soft_reason:
                reasons.append(f"필요수량 후보({float(required_qty):.0f}톤)는 조건부: {soft_reason}")
            else:
                reasons.append(f"필요수량 후보({float(required_qty):.0f}톤)는 조건부")

        selected_qty = float(row.get("selected_candidate_qty_ton", 0.0) or 0.0)
        if selected_qty > 0 and float(required_qty) > selected_qty and selected_name != "shortage_anchored":
            reasons.append("필요수량 후보 대신 더 작은 실행가능 후보를 선택함")

    if _pick_first_present_int(row, ["target_b_final_pred", "target_b_pred", "target_b_rule"], 0) == 1:
        reasons.append("비용 상방 리스크도 함께 확인 필요")

    deduped: list[str] = []
    seen = set()
    for reason in reasons:
        key = reason.strip()
        if key and key not in seen:
            seen.add(key)
            deduped.append(key)

    return " | ".join(deduped)