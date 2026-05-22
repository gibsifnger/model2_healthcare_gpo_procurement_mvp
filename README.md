# Healthcare GPO Procurement Strategy MVP

## 1. 프로젝트 한 줄 정의

이 프로젝트는 기존 Model2의 구매 의사결정 구조를 **헬스케어 GPO 구매전략기획 상황에 맞게 경량 재구성한 MVP**입니다.

실제 의료 구매 시스템을 구현한 것이 아니며, 실제 병원 데이터를 사용하지 않았습니다.  
`synthetic demo data`를 기반으로 카테고리별 구매 데이터를 **상태 → 신호 → 후보 action → gate → simulation → 최종 추천**으로 연결하는 구조를 보여주는 포트폴리오 프로젝트입니다.

---

## 2. 프로젝트 목적

이지메디컴 구매전략기획 직무는 단순히 단가를 낮추는 업무가 아니라, 카테고리별 구매 데이터, 공급사 구조, 계약조건, 납기 안정성, 표준화 가능성, 예외구매, 재고 리스크, KPI를 함께 보고 구매전략을 설계하는 업무에 가깝습니다.

이 MVP는 그 업무를 아래처럼 구조화합니다.

```text
품목별 구매 데이터
→ 현재 구매상태 생성
→ 비용기회/공급통제 리스크 신호 해석
→ 구매전략 후보 생성
→ 실행 가능성 gate 검토
→ KPI 관점 simulation
→ 최종 recommended action 생성
```

핵심은 **머신러닝 예측 성능**이 아니라, 구매전략기획 업무에서 반복되는 판단을 데이터 기반 의사결정 흐름으로 정리하는 것입니다.

---

## 3. 기존 Model2와의 관계

기존 Model2는 원자재 구매 의사결정을 위한 파이프라인이었습니다.  
이번 프로젝트는 기존 Model2의 복잡한 HGB 학습, 외생변수 API, artifact 관리 구조를 유지하지 않고, 아래 핵심 의사결정 구조만 가져왔습니다.

| 기존 Model2 핵심 구조 | 이번 Healthcare GPO MVP 적용 |
|---|---|
| State generation | 품목별 구매전략 상태 생성 |
| Judgment interpretation | 비용기회/공급통제 리스크 신호 해석 |
| Candidate policy generation | 재입찰, 연간계약, 표준화, 복수소싱 등 후보 생성 |
| Operating gate check | 데이터 품질, 대체품 가능성, 표준화 가능성 검토 |
| Scenario simulation | 원가절감 기회, 공급 리스크 감소, 운영 안정성 점수 비교 |
| Final action recommendation | 품목별 최종 구매전략 action 추천 |

즉, 이 프로젝트는 기존 모델2를 그대로 복사한 것이 아니라, **구매 의사결정 아키텍처를 헬스케어 GPO 구매전략 시나리오에 맞게 재해석한 경량 MVP**입니다.

---

## 4. Decision Architecture

```text
Input data
→ A_state
→ B_interpret
→ C_policy_action
→ Gate
→ Simulation
→ Final recommendation
```

### Row unit

```text
decision_month + item_id = one procurement strategy decision row
```

현재 버전은 여러 달의 시계열 데이터가 아니라, `2026-05` 기준의 단일 시점 품목별 snapshot 데이터입니다.

다만 `decision_month`를 여러 달로 확장하면, 향후 `item_id + month` 단위의 구매전략 판단 이력 또는 시계열 분석 구조로 확장할 수 있습니다.

---

## 5. Repository Structure

```text
model2_healthcare_gpo_procurement_mvp/
├─ README.md
├─ requirements.txt
├─ .gitignore
├─ run_healthcare_gpo_mvp.py
├─ data/
│  └─ healthcare_gpo_mvp_demo.csv
├─ outputs/
│  └─ .gitkeep
├─ examples/
│  └─ healthcare_gpo_mvp_recommendations_sample.csv
├─ docs/
│  ├─ healthcare_gpo_mvp.md
│  ├─ decision_flow.md
│  └─ portfolio_summary.md
└─ healthcare_gpo_mvp/
   ├─ __init__.py
   ├─ config.py
   ├─ schema.py
   ├─ pipeline.py
   ├─ A_state/
   ├─ B_interpret/
   └─ C_policy_action/
```

---

## 6. Input Features

| Column | 의미 |
|---|---|
| `decision_month` | 구매전략 판단 기준월 |
| `item_id` | 품목 ID |
| `item_name` | 품목명 |
| `category` | 구매 카테고리: MRO, 진료재료, 장비소모품, 검사재료 |
| `annual_spend` | 연간 구매금액 |
| `contract_price` | 현재 계약단가 |
| `market_price_index` | 시장가/단가 압박 지수 |
| `supplier_count` | 공급사 수 |
| `supplier_otif` | 정시·정량 납기율 |
| `lead_time_days` | 평균 리드타임 |
| `emergency_purchase_ratio` | 긴급구매 또는 예외구매 비중 |
| `standardization_score` | 표준품목 전환 가능성 점수 |
| `substitute_available` | 대체품 존재 여부, 0 또는 1 |
| `data_quality_score` | 데이터 신뢰도 점수 |
| `inventory_risk_score` | 재고부족 또는 백오더 위험 점수 |

---

## 7. A/B/C 처리 흐름

### A_state: 현재 구매상태 생성

입력 데이터를 바탕으로 품목별 구매전략 상태값을 만듭니다.

예시 상태값:

| 상태값 | 의미 |
|---|---|
| `spend_tier` | 지출 규모 등급 |
| `price_pressure_score` | 가격 압박 수준 |
| `supplier_concentration_risk` | 공급사 집중 위험 |
| `delivery_risk` | 납기 위험 |
| `exception_purchase_risk` | 긴급/예외구매 위험 |
| `standardization_opportunity` | 표준화 기회 |
| `substitute_readiness` | 대체품 검토 가능성 |
| `data_readiness` | 데이터 판단 가능 수준 |
| `inventory_risk_level` | 재고부족 위험 수준 |

### B_interpret: 신호 해석

기존 Model2의 Target A/B 구조를 그대로 쓰지 않고, 이번 MVP에서는 2개의 판단축으로 재해석했습니다.

| 기존 개념 | 이번 MVP 재해석 | 의미 |
|---|---|---|
| Target A concept | `cost_opportunity_signal` | 원가절감, 재입찰, 연간계약 검토 기회 |
| Target B concept | `supply_control_risk_signal` | 공급사 집중, 납기 불안정, 긴급구매, 재고위험, 표준화 필요 |

이번 버전은 학습 모델이나 예측 target을 사용하지 않습니다.  
대신 rule-based signal을 통해 구매전략 후보를 생성합니다.

### C_policy_action: 후보 생성, gate, simulation, 최종 추천

신호를 기반으로 실행 가능한 구매전략 후보를 만들고, gate 검토와 KPI 점수 비교를 거쳐 최종 action을 추천합니다.

---

## 8. Candidate Actions

| Action | 의미 |
|---|---|
| `data_cleanup_first` | 전략 판단보다 품목·공급사·단가 데이터 정비 우선 |
| `maintain_contract` | 기존 계약 유지 |
| `monitor_risk` | 주요 KPI 지속 모니터링 |
| `rebid` | 재입찰 또는 가격 재검토 |
| `annual_contract` | 연간단가계약 검토 |
| `standardize_item` | 표준품목 전환 검토 |
| `dual_source` | 공급사 이원화 검토 |
| `review_substitute` | 대체품 검토 |

---

## 9. Quick Start

```bash
pip install -r requirements.txt
python run_healthcare_gpo_mvp.py
```

실행 후 `outputs/` 폴더에 중간 산출물과 최종 추천 결과가 생성됩니다.

---

## 10. Key Outputs

| File | 설명 |
|---|---|
| `outputs/state_df.csv` | A_state 결과: 품목별 구매전략 상태값 |
| `outputs/signal_df.csv` | B_interpret 결과: 비용기회/공급통제 리스크 신호 |
| `outputs/candidate_df.csv` | 품목별 후보 action 목록 |
| `outputs/gated_candidate_df.csv` | gate 검토 후 후보 action |
| `outputs/simulation_result_df.csv` | action별 KPI 점수 비교 |
| `outputs/final_decision_df.csv` | 품목별 최종 action 선택 결과 |
| `outputs/healthcare_gpo_mvp_recommendations.csv` | 최종 추천 결과 |
| `examples/healthcare_gpo_mvp_recommendations_sample.csv` | 포트폴리오 확인용 sample output |

---

## 11. Example Output

최종 output은 아래와 같은 형태입니다.

| decision_month | item_id | item_name | category | recommended_action | decision_reason |
|---|---|---|---|---|---|
| 2026-05 | HGP-016 | 수술 드레이프 | 진료재료 | `rebid` | 연간 구매금액과 시장가 압박이 높아 재입찰 또는 가격 재검토가 필요합니다. |
| 2026-05 | HGP-009 | 병동 라벨지 | MRO | `data_cleanup_first` | 데이터 품질 점수가 낮아 계약/소싱 판단보다 품목·공급사·단가 데이터 정비가 우선입니다. |

---

## 12. Portfolio Statement

이 MVP는 헬스케어 GPO 구매전략기획 업무를 다음과 같이 구조화할 수 있음을 보여줍니다.

```text
카테고리별 구매 데이터
→ 비용기회/공급통제 리스크 신호
→ 구매전략 후보 action
→ gate 기반 실행 가능성 검토
→ KPI 비교
→ 최종 추천과 사유 생성
```

즉, 이 프로젝트는 머신러닝 예측모델 성능을 보여주는 것이 아니라, **구매전략기획 업무의 판단 흐름을 데이터 기반으로 구조화한 AI-ready decision pipeline**입니다.

---

## 13. Limitations

- 실제 의료 구매 시스템이 아닙니다.
- 실제 병원 데이터를 사용하지 않았습니다.
- 의약품/API 전문 모델이 아닙니다.
- rule-based MVP이며, ML 모델 성능 검증 목적이 아닙니다.
- 현재 버전은 단일월 snapshot 데이터 기반입니다.

---

## 14. Future Extension

향후 실제 구매 데이터가 확보되면 아래 방향으로 확장할 수 있습니다.

| 확장 방향 | 설명 |
|---|---|
| 실제 병원 구매 데이터 연동 | 품목, 공급사, 계약단가, 납기, 재고 데이터 연결 |
| item-month 시계열 확장 | `decision_month + item_id`를 여러 달로 확장 |
| 의약품/API 카테고리 확장 | 공급중단, 규제, 대체 가능성, 유효기간 조건 반영 |
| BI dashboard 연결 | 카테고리별 절감기회·리스크·KPI 시각화 |
| RPA/report automation | 반복 리포트 자동 생성 |
| ML 예측모델 결합 | 가격, 수요, 공급지연, 재고부족 위험 예측 |

---

## 15. Summary

이 프로젝트는 실제 의료 구매 시스템이 아니라, 기존 Model2의 구매 의사결정 구조를 헬스케어 GPO 구매전략기획 상황에 맞게 경량 재구성한 synthetic data 기반 MVP입니다.

핵심 메시지는 다음과 같습니다.

> 구매 데이터를 단순 보고용 숫자로 끝내지 않고, 비용기회와 공급망 리스크 신호로 해석한 뒤, 재입찰·연간계약·표준화·공급사 이원화·대체품 검토 같은 실행 가능한 구매전략 action으로 연결한다.
