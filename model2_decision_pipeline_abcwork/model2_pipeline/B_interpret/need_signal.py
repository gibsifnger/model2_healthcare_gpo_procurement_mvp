"""
B_interpret.need_signal
- need_buy_flag를 B 레이어에 명시적으로 두기 위한 공통 유틸
"""
from __future__ import annotations
import pandas as pd

def infer_need_buy_flag_from_context(row: pd.Series) -> int:
    for a_col, b_col in [
        ("target_a_final_pred", "target_b_final_pred"),
        ("target_a_pred", "target_b_pred"),
        ("target_a_rule", "target_b_rule"),
    ]:
        a = int(row.get(a_col, 0) or 0)
        b = int(row.get(b_col, 0) or 0)
        if a == 1 or b == 1:
            return 1
    return 0

__all__ = ["infer_need_buy_flag_from_context"]
