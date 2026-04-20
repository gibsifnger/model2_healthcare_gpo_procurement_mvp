"""
B_interpret.helper_calculator
- decision_generator.py에서 helper / 해석(B) 계산을 분리한 파일
- 상태 자체는 만들지 않고, no-buy world를 해석해서 risk / requirement / rule 신호를 만든다.
"""
from __future__ import annotations

from typing import Dict, List
import numpy as np
import pandas as pd

from ..config import PipelineConfig


def _calc_required_buy_qty_from_arrival(
    starting_inventory_ton: float,
    usage_path: List[float],
    open_po_path: List[float],
    arrival_month_idx: int,
    safety_stock_ton: float,
) -> Dict[str, float]:
    begin_inv = float(starting_inventory_ton)
    begin_inv_at_arrival = float(starting_inventory_ton)

    for month_idx in range(1, arrival_month_idx):
        available = begin_inv + float(open_po_path[month_idx - 1])
        ending_inv = max(0.0, available - float(usage_path[month_idx - 1]))
        begin_inv = ending_inv
    begin_inv_at_arrival = begin_inv

    cum_receipts = 0.0
    cum_demand = 0.0
    required_qty = 0.0
    max_gap_qty = 0.0

    for month_idx in range(arrival_month_idx, len(usage_path) + 1):
        cum_receipts += float(open_po_path[month_idx - 1])
        cum_demand += float(usage_path[month_idx - 1])
        gap_without_candidate = cum_demand - (begin_inv_at_arrival + cum_receipts)
        max_gap_qty = max(max_gap_qty, gap_without_candidate)
        required_qty = max(required_qty, gap_without_candidate + safety_stock_ton)

    required_first_shortage_qty = max(
        0.0,
        float(usage_path[arrival_month_idx - 1]) - (begin_inv_at_arrival + float(open_po_path[arrival_month_idx - 1])) + safety_stock_ton,
    )

    return {
        "begin_inv_at_arrival_ton": float(begin_inv_at_arrival),
        "max_cum_gap_arrival_ton": float(max(0.0, max_gap_qty)),
        "required_buy_qty_arrival_ton": float(max(0.0, required_qty)),
        "required_buy_qty_first_shortage_ton": float(max(0.0, required_first_shortage_qty)),
    }


def _simulate_no_buy_helpers(
    starting_inventory_ton: float,
    usage_path: List[float],
    open_po_path: List[float],
    expected_cost_path: List[float],
    now_cost: float,
    freight_current: float,
    usd_current: float,
    cfg: PipelineConfig,
) -> Dict[str, float]:
    begin_inv = float(starting_inventory_ton)
    end_inv_raw_path: List[float] = []
    end_inv_clipped_path: List[float] = []
    shortage_path: List[float] = []

    for demand_ton, open_po_ton in zip(usage_path, open_po_path):
        available = begin_inv + float(open_po_ton)
        raw_end_inv = available - float(demand_ton)
        shortage = max(0.0, -raw_end_inv)
        ending_inv = max(0.0, raw_end_inv)

        end_inv_raw_path.append(float(raw_end_inv))
        end_inv_clipped_path.append(float(ending_inv))
        shortage_path.append(float(shortage))
        begin_inv = ending_inv

    cover_months = [
        (end_inv / usage if usage > 0 else np.nan)
        for end_inv, usage in zip(end_inv_clipped_path, usage_path)
    ]

    shortage_months = [i + 1 for i, qty in enumerate(shortage_path) if qty > 0]
    a_first_shortage_month_idx = float(shortage_months[0]) if shortage_months else np.nan
    arrival_month_idx = int(a_first_shortage_month_idx) if shortage_months else cfg.lt_months
    arrival_month_idx = max(1, min(arrival_month_idx, cfg.horizon_months))

    req = _calc_required_buy_qty_from_arrival(
        starting_inventory_ton=starting_inventory_ton,
        usage_path=usage_path,
        open_po_path=open_po_path,
        arrival_month_idx=arrival_month_idx,
        safety_stock_ton=cfg.safety_stock_ton,
    )

    a_min_end_inv_ton = float(np.min(end_inv_raw_path))
    a_min_cover_months = float(np.nanmin(cover_months))
    a_emergency_buy_needed_flag = int(any(qty > 0 for qty in shortage_path))
    baseline_total_shortage_ton = float(np.sum(shortage_path))

    cost_vs_now = [
        (float(cost) / float(now_cost) - 1.0) if now_cost > 0 else 0.0
        for cost in expected_cost_path
    ]
    peak_cost_vs_now_pct = float(np.max(cost_vs_now))
    high_cost_month_count = int(sum(1 for v in cost_vs_now if v >= 0.05))

    if shortage_months:
        shortage_month_costs = [cost_vs_now[idx - 1] for idx in shortage_months]
        forced_buy_cost_vs_now_pct = float(np.max(shortage_month_costs))
    else:
        forced_buy_cost_vs_now_pct = float(max(0.0, peak_cost_vs_now_pct))

    b_forced_buy_flag = int(a_emergency_buy_needed_flag == 1)

    freight_stress = np.clip((freight_current - 95.0) / 30.0, 0.0, 1.0)
    fx_stress = np.clip((usd_current - 1260.0) / 80.0, 0.0, 1.0)
    shortage_severity = np.clip(max(shortage_path) / cfg.monthly_usage_base_ton, 0.0, 1.0)
    premium_score = 100.0 * np.clip(
        0.45 * max(0.0, peak_cost_vs_now_pct / 0.10)
        + 0.25 * freight_stress
        + 0.15 * fx_stress
        + 0.15 * shortage_severity,
        0.0,
        1.0,
    )

    target_a = int(
        (a_emergency_buy_needed_flag == 1)
        or (a_min_end_inv_ton < 0)
        or (a_min_cover_months < 0.35)
        or (
            (a_min_cover_months < 0.50)
            and (not pd.isna(a_first_shortage_month_idx))
            and (a_first_shortage_month_idx <= 2)
        )
    )

    target_b = int(
        ((b_forced_buy_flag == 1) and (forced_buy_cost_vs_now_pct >= 0.05))
        or (premium_score >= 60.0)
        or (peak_cost_vs_now_pct >= 0.08)
        or ((peak_cost_vs_now_pct >= 0.05) and (high_cost_month_count >= 2))
    )

    return {
        "a_min_end_inv_ton": float(a_min_end_inv_ton),
        "a_min_cover_months": float(a_min_cover_months),
        "a_emergency_buy_needed_flag": int(a_emergency_buy_needed_flag),
        "a_first_shortage_month_idx": a_first_shortage_month_idx,
        "baseline_total_shortage_ton": baseline_total_shortage_ton,
        **req,
        "b_peak_cost_vs_now_pct": float(peak_cost_vs_now_pct),
        "b_forced_buy_flag": int(b_forced_buy_flag),
        "b_forced_buy_cost_vs_now_pct": float(forced_buy_cost_vs_now_pct),
        "b_emergency_premium_score": float(premium_score),
        "b_high_cost_month_count": int(high_cost_month_count),
        "target_a_rule": int(target_a),
        "target_b_rule": int(target_b),
    }


__all__ = [
    "_calc_required_buy_qty_from_arrival",
    "_simulate_no_buy_helpers",
]
