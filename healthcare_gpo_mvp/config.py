"""
[FILE PURPOSE]
- 구매전략 판단에 사용하는 핵심 기준값(Threshold)을 모아둔 설정 파일이다.
- 실무 적용 시 병원군, 카테고리, 품목 중요도, 계약조건에 따라 이 값들을 조정해야 한다.

[BUSINESS UNIT]
- 기본 판단 단위: 구매전략 판단월(decision_month) × 품목(item_id)
"""

# 데이터 품질 기준: 이 값보다 낮으면 가격협상보다 데이터 정비 우선으로 분리한다.
DATA_QUALITY_MIN = 0.65
# 정시·정량 납기율 기준: 이 값보다 낮으면 공급 안정성 리스크로 해석한다.
SUPPLIER_OTIF_MIN = 0.90
# 긴급구매 비중이 이 값보다 높으면 운영/재고 통제 필요성을 의미한다.
EMERGENCY_PURCHASE_HIGH = 0.15
# 표준화 가능성 최소 기준: 이 값 이상일 때 표준화 후보로 고려한다.
STANDARDIZATION_MIN = 0.70
# 시장가 압박 기준: 현재 계약단가/시장가 지수가 이 값 이상이면 가격 재검토 후보로 본다.
MARKET_PRICE_PRESSURE_HIGH = 1.07
# 재고 위험 판단 기준: 재고 위험 점수가 이 값 이상이면 재고·공급 안정성 우선 관리 대상이다.
INVENTORY_RISK_HIGH = 0.70
# 고액 연간 구매 기준: 이 값 이상이면 비용절감 효과 우선 고려 대상이다.
HIGH_SPEND_THRESHOLD = 100000000
# 중간 연간 구매 기준: 이 값 이상이면 중간 우선순위 비용절감 후보로 본다.
MID_SPEND_THRESHOLD = 50000000
# 장기 리드타임 기준(일): 이 값 이상이면 공급 안정성 확보(이원화 등) 고려 대상이다.
LONG_LEAD_TIME_DAYS = 30

