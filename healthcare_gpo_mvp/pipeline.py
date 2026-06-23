"""
[FILE PURPOSE]
- 파이프라인 오케스트레이션 파일로, A_state → B_interpret → C_policy_action → gate → simulation → final recommendation의 전체 흐름을 연결한다.
- 각 단계의 중간 산출물을 저장하고 포트폴리오 단위 실행 결과(추천 파일)를 생성한다.

[BUSINESS UNIT]
- 기본 판단 단위: 구매전략 판단월(decision_month) × 품목(item_id)
- 현재 버전은 단일월 snapshot 기반

[INPUT]
- demo CSV 경로 또는 실무 데이터 파일 경로

[OUTPUT]
- 중간 및 최종 산출물: state_df.csv, signal_df.csv, candidate_df.csv, gated_candidate_df.csv, simulation_result_df.csv, final_decision_df.csv, healthcare_gpo_mvp_recommendations.csv

[현업 적용 시 교체 대상]
- 각 단계에서 사용하는 원천 데이터(병원 구매실적, 품목/공급사 마스터 등)를 실무 DB/파일로 연결해야 함
"""

from pathlib import Path
import shutil

import pandas as pd

from healthcare_gpo_mvp.A_state.state_builder import build_state
from healthcare_gpo_mvp.B_interpret.signal_builder import build_signals
from healthcare_gpo_mvp.C_policy_action.action_translator import translate_actions
from healthcare_gpo_mvp.C_policy_action.candidate_policy import build_candidates
from healthcare_gpo_mvp.C_policy_action.gate_policy import apply_gates
from healthcare_gpo_mvp.C_policy_action.selector import select_final_actions
from healthcare_gpo_mvp.C_policy_action.simulator import simulate_actions


# ============================================================
# [BLOCK] 전체 파이프라인 연결
# [현업 의미] 원천 구매데이터를 받아 품목별 상태를 생성하고, 리스크/기회 신호로 해석한 뒤
# 후보 action을 만들고 실행 가능성을 gate에서 검증한 후 KPI 관점의 시뮬레이션으로 비교해 최종 추천을 만든다.
# [판단 기준] 상태 생성 → 신호 해석(비용 절감 기회 vs 공급 통제 리스크) → 후보 생성 → gate(실행 가능성) → simulation → selector
# [산출물] state_df, signal_df, candidate_df, gated_candidate_df, simulation_result_df, final_decision_df, recommendation_df
# [수정 포인트] 실무 적용 시 병원군, 카테고리, 계약조건별로 threshold와 데이터 매핑을 조정해야 함
# [WHY] 단계별 중간 결과를 남겨 두면 포트폴리오 분석, 감사, 그리고 의사결정 근거 제공에 유리하다
# ============================================================
def run_pipeline(
    input_path: str = "data/healthcare_gpo_mvp_demo.csv",
    output_dir: str = "outputs",
    example_path: str = "examples/healthcare_gpo_mvp_recommendations_sample.csv",
) -> dict:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    Path(example_path).parent.mkdir(parents=True, exist_ok=True)

    # 상태 생성: 품목별로 구매상태(state_df)를 만들고 다음 단계(신호해석)에 넘긴다.
    state_df = build_state(input_path)
    # 신호 해석: 상태값을 비용기회 신호와 공급통제 리스크 신호로 해석한다.
    signal_df = build_signals(state_df)
    # 후보 생성: 신호를 바탕으로 실행 가능한 후보 action 목록을 생성한다.
    candidate_df = build_candidates(signal_df)
    # 게이트 검토: 데이터 신뢰도, 대체품 존재, 표준화 가능성 등으로 실행 가능성을 검토한다.
    gated_candidate_df = apply_gates(candidate_df, signal_df)
    # 시뮬레이션: 후보 action별로 절감/리스크/운영 안정성 관점의 KPI 시뮬레이션을 수행한다.
    simulation_result_df = simulate_actions(gated_candidate_df, signal_df)
    # 최종 선택: 시뮬레이션 결과와 우선순위 규칙으로 최종 추천 action을 선택한다.
    final_decision_df = select_final_actions(simulation_result_df)
    # 추천 사유 변환: 최종 추천을 담당자가 이해할 수 있는 설명으로 변환한다.
    recommendation_df = translate_actions(final_decision_df, signal_df)

    # 중간/최종 산출물 저장: 포트폴리오 분석 및 검증을 위해 모든 단계의 결과를 CSV로 남긴다.
    _save_csv(state_df, output_path / "state_df.csv")
    _save_csv(signal_df, output_path / "signal_df.csv")
    _save_csv(candidate_df, output_path / "candidate_df.csv")
    _save_csv(gated_candidate_df, output_path / "gated_candidate_df.csv")
    _save_csv(simulation_result_df, output_path / "simulation_result_df.csv")
    _save_csv(final_decision_df, output_path / "final_decision_df.csv")

    final_file = output_path / "healthcare_gpo_mvp_recommendations.csv"
    _save_csv(recommendation_df, final_file)
    shutil.copyfile(final_file, example_path)

    return {
        "input_path": str(Path(input_path)),
        "output_path": str(output_path),
        "input_rows": len(pd.read_csv(input_path, encoding="utf-8")),
        "final_recommendations": len(recommendation_df),
        "saved_output_file": str(final_file),
    }


def _save_csv(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, index=False, encoding="utf-8-sig")

