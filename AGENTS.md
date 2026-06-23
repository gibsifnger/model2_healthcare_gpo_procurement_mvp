# AGENTS for model2_healthcare_gpo_procurement_mvp

프로젝트 역할: 헬스케어 GPO 구매전략 의사결정 파이프라인

주석 목적: 단순 Python 문법 설명이 아닌, 품목별 구매전략 판단을 비즈니스 관점에서 설명하기 위해 작성됨. 주석은 한국어로 작성되어 있으며, 상태 생성, 비용기회 신호, 공급통제 리스크 신호, 후보 action, gate, simulation, 최종 추천 사유를 중심으로 한다.

Decision Row Unit: 구매전략 판단월(decision_month) × 품목(item_id)

주석 언어: 한국어

금지: Python 문법 설명형 주석(예: "pandas를 불러온다", "리스트를 만든다")은 허용되지 않음.

강조: 상태 생성, 비용기회 신호, 공급통제 리스크 신호, 후보 action, gate, simulation, 최종 추천 사유에 대한 비즈니스 의미 중심 주석을 유지할 것.

실무 데이터 교체 지점:
- 병원 구매실적
- 품목마스터
- 공급사마스터
- 계약단가/계약이력
- 납기실적
- 긴급구매 이력
- 재고위험 데이터
- 대체품 정보
- 표준품목 정보

검증 명령: python run_healthcare_gpo_mvp.py
