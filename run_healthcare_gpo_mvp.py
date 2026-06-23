"""
[FILE PURPOSE]
- 이 파일은 포트폴리오용 실행 엔트리 포인트로, 전체 헬스케어 GPO 구매전략 의사결정 파이프라인을 한 번에 실행해 데모용 추천 결과를 생성한다.
- 단순 실행 스크립트가 아니라 품목별(decision_month × item_id) 의사결정 행의 파이프라인 흐름을 연결해 최종 추천 정보를 출력하는 역할을 한다.

[BUSINESS UNIT]
- 기본 판단 단위: 구매전략 판단월(decision_month) × 품목(item_id)
- 현재 버전은 2026-05 기준 단일월 snapshot 구조
- 향후 item_id × month 시계열 구조로 확장 가능

[INPUT]
- 기본적으로 파이프라인이 필요한 원천 데이터 경로를 입력으로 받음 (예: data/healthcare_gpo_mvp_demo.csv)
- 주요 컬럼: decision_month, item_id, item_name, category, annual_spend, contract_price, market_price_index, supplier_count, supplier_otif, lead_time_days, emergency_purchase_ratio, standardization_score, substitute_available, data_quality_score, inventory_risk_score

[OUTPUT]
- 파이프라인이 생성하는 주요 산출물: state_df, signal_df, candidate_df, gated_candidate_df, simulation_result_df, final_decision_df
- 저장 파일 예: outputs/healthcare_gpo_mvp_recommendations.csv

[현업 적용 시 교체 대상]
- demo CSV를 병원별 구매실적, 품목마스터, 공급사마스터, 계약단가, 납기실적 등 실무 데이터 소스로 교체해야 함
"""

from healthcare_gpo_mvp.pipeline import run_pipeline


# ============================================================
# [BLOCK] 실행 진입점
# [현업 의미] 포트폴리오 단위로 파이프라인을 실행해 품목별 구매전략 추천을 만들고, 결과 요약을 출력하는 실행부
# [판단 기준] 전체 파이프라인(A_state → B_interpret → C_policy_action → gate → simulation → final recommendation)을 순차 실행
# [산출물] state_df, signal_df, candidate_df, gated_candidate_df, simulation_result_df, final_decision_df 및 최종 저장 파일 경로
# [수정 포인트] 배포 시 입력 데이터 경로와 저장 경로를 실무 환경에 맞게 바꿔야 함
# [WHY] 포트폴리오 관점에서 한 번에 실행 가능한 형태로 제공해 의사결정 시나리오를 빠르게 검증하기 위해
# ============================================================
def main() -> None:
    result = run_pipeline()
    print(f"input path: {result['input_path']}")
    print(f"output path: {result['output_path']}")
    print(f"number of input rows: {result['input_rows']}")
    print(f"number of final recommendations: {result['final_recommendations']}")
    print(f"saved output file path: {result['saved_output_file']}")


if __name__ == "__main__":
    main()
