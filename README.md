# Healthcare GPO Procurement Strategy MVP

This project is a lightweight MVP that adapts the Model2 procurement decision architecture to a healthcare GPO procurement strategy scenario. It does not implement a full healthcare procurement system and does not use real hospital data.

이 프로젝트는 기존 Model2의 구매 의사결정 구조를 헬스케어 GPO 구매전략기획 상황에 맞게 경량 재구성한 synthetic demo data 기반 MVP입니다. 실제 의료 구매 시스템이나 실제 병원 데이터를 구현한 것이 아닙니다.

## 1. Project Overview

This MVP reuses the core decision architecture of the original Model2 project and rebuilds it for a healthcare GPO procurement strategy planning scenario. The focus is not algorithmic performance. The focus is turning category-level purchasing data into interpretable states, risk signals, candidate actions, gate checks, scenario scores, and final recommendations.

## 2. Why This Project

Procurement strategy planning is not only about unit price. It also requires category analysis, supplier structure, contract terms, delivery reliability, standardization potential, exception purchasing, inventory risk, and KPI monitoring.

This MVP shows how procurement data can be translated into executable action options such as rebid, annual contract review, standard item conversion, dual sourcing, substitute review, or monitoring.

## 3. Decision Architecture

Input data  
→ A_state  
→ B_interpret  
→ C_policy_action  
→ Gate  
→ Simulation  
→ Final recommendation

Row unit:
`decision_month + item_id = one procurement strategy decision row`

This MVP uses single-month item-level snapshot data for `2026-05`, not multi-month time-series data. If `decision_month` is later expanded across multiple months, the same structure can become an item-month procurement strategy decision history or time-series analysis dataset.

## 4. Repository Structure

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

## 5. Input Features

| Column | Meaning |
|---|---|
| decision_month | Decision snapshot month |
| item_id | Item ID |
| item_name | Item name |
| category | Procurement category: MRO, 진료재료, 장비소모품, 검사재료 |
| annual_spend | Annual purchasing spend |
| contract_price | Current contract unit price |
| market_price_index | Market price pressure index |
| supplier_count | Number of available suppliers |
| supplier_otif | On-time and in-full delivery rate |
| lead_time_days | Average lead time |
| emergency_purchase_ratio | Exception or emergency purchase ratio |
| standardization_score | Standardization opportunity score |
| substitute_available | Whether a substitute item exists, 0 or 1 |
| data_quality_score | Data reliability score |
| inventory_risk_score | Shortage or backorder risk score |

## 6. Candidate Actions

| Action | Meaning |
|---|---|
| data_cleanup_first | Clean item, supplier, and price data before strategy action |
| maintain_contract | Maintain the current contract |
| monitor_risk | Continue KPI monitoring |
| rebid | Review pricing or run a rebid |
| annual_contract | Review annual unit-price contract |
| standardize_item | Convert to standard item where appropriate |
| dual_source | Review supplier diversification |
| review_substitute | Review substitute item option |

## 7. Quick Start

```bash
pip install -r requirements.txt
python run_healthcare_gpo_mvp.py
```

## 8. Key Outputs

The pipeline writes intermediate and final CSV files to `outputs/`.

| File | Description |
|---|---|
| outputs/state_df.csv | A_state result with procurement strategy states |
| outputs/signal_df.csv | B_interpret result with risk and opportunity signals |
| outputs/candidate_df.csv | Candidate action list in long format |
| outputs/gated_candidate_df.csv | Candidate actions after gate checks |
| outputs/simulation_result_df.csv | Action-level KPI score comparison |
| outputs/final_decision_df.csv | Selected action per item |
| outputs/healthcare_gpo_mvp_recommendations.csv | Final recommendation file |
| examples/healthcare_gpo_mvp_recommendations_sample.csv | Portfolio sample output |

## 9. Portfolio Statement

This MVP demonstrates how procurement strategy planning can be structured into category-level data, risk signals, candidate actions, operating gates, KPI comparison, and final recommendations.

## 10. Limitations

- This is not a real healthcare procurement system.
- This does not use real hospital data.
- This is not a pharmaceutical or API category specialist model.
- This is a rule-based MVP and is not intended to validate ML performance.

## 11. Future Extension

- Connect with real hospital purchasing data after governance review.
- Extend to pharmaceutical and API categories.
- Add supply disruption and shortage event data.
- Connect to a BI dashboard.
- Connect to RPA or report automation.
- Extend toward ML-based price, demand, and risk forecasting.
