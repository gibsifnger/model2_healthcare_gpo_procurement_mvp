"""
[FILE PURPOSE]
- 입력 데이터의 필수 컬럼과 최종 출력 컬럼, 허용되는 후보 action 목록을 정의하는 데이터 계약서 역할의 파일이다.
- 실무 적용 시 ERP/GPO/병원 구매시스템의 컬럼과 매핑하는 기준 문서로 사용한다.

[BUSINESS UNIT]
- 기본 판단 단위: 구매전략 판단월(decision_month) × 품목(item_id)
"""

REQUIRED_COLUMNS = [
    # 의사결정 기준 월: 구매전략을 판단하는 스냅샷 기준
    "decision_month",
    # 품목 식별자: 구매전략의 기본 단위
    "item_id",
    # 품목명: 현업 설명용
    "item_name",
    # 카테고리: 품목군별 전략 차등 적용에 사용
    "category",
    # 연간 구매금액: 비용절감 우선순위 판단 기준
    "annual_spend",
    # 계약 단가: 현재 계약상태를 반영
    "contract_price",
    # 시장가 지수: 시장가 압박 여부 판단에 사용
    "market_price_index",
    # 공급사 수: 공급사 집중도/이원화 필요성 판단
    "supplier_count",
    # 정시정량 납기율(OTIF): 공급 안정성 판단
    "supplier_otif",
    # 평균 리드타임(일): 장기 리드타임 여부 판단
    "lead_time_days",
    # 긴급구매 비중: 운영/재고 통제 필요성 판단
    "emergency_purchase_ratio",
    # 표준화 점수: 표준품목 전환 가능성 판단
    "standardization_score",
    # 대체품 존재 여부(0/1): 대체품 검토 실행 가능성 판단
    "substitute_available",
    # 데이터 품질 점수: 데이터 정비 우선 판단 기준
    "data_quality_score",
    # 재고 위험 점수: 재고 관련 리스크 판단
    "inventory_risk_score",
]

FINAL_OUTPUT_COLUMNS = [
    "decision_month",
    "item_id",
    "item_name",
    "category",
    # 리스크/기회 요약 텍스트
    "risk_summary",
    # 추천 action (최종 선택된 전략)
    "recommended_action",
    # 추천 사유(현업 담당자가 이해할 수 있는 설명)
    "decision_reason",
    # 포트폴리오 우선순위 점수
    "priority_score",
]

CANDIDATE_ACTIONS = [
    # 데이터 정비 우선(데이터 품질이 낮을 때 우선 수행)
    "data_cleanup_first",
    # 기존 계약 유지
    "maintain_contract",
    # 리스크 모니터링(즉시 실행보다는 감시)
    "monitor_risk",
    # 재입찰(가격경쟁을 통한 절감 가능성 탐색)
    "rebid",
    # 연간계약(장기계약으로 가격·배송 안정 확보)
    "annual_contract",
    # 표준품목 전환(규격화하여 구매 단가 및 관리 효율화)
    "standardize_item",
    # 공급사 이원화(공급 안정성 확보)
    "dual_source",
    # 대체품 검토(대체품이 확인된 경우 실행 후보)
    "review_substitute",
]
