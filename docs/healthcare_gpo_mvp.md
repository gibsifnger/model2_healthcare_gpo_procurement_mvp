# Healthcare GPO Procurement Strategy MVP

## 1. Purpose

This document describes an MVP scenario that reinterprets the Model2 procurement decision structure for healthcare GPO procurement strategy planning. It does not implement a real healthcare procurement system and does not use real hospital data. It is a portfolio extension based on synthetic demo data.

## 2. Input Data

| Column | Meaning |
|---|---|
| item_id | Item ID |
| item_name | Item name |
| category | Procurement category |
| annual_spend | Annual purchasing spend |
| contract_price | Current contract unit price |
| market_price_index | Market price pressure index |
| supplier_count | Number of suppliers |
| supplier_otif | On-time and in-full delivery rate |
| lead_time_days | Average lead time |
| emergency_purchase_ratio | Exception or emergency purchase ratio |
| standardization_score | Standardization opportunity score |
| substitute_available | Substitute item availability, 0 or 1 |
| data_quality_score | Data reliability score |
| inventory_risk_score | Shortage or inventory risk score |

## 3. A/B/C Decision Flow

| Step | Role |
|---|---|
| A_state | Converts raw item data into procurement strategy states |
| B_interpret | Converts states into opportunity and risk signals |
| C_policy_action | Generates candidate actions, checks gates, scores scenarios, and selects final actions |

## 4. Feature Definition

| State Feature | Meaning |
|---|---|
| spend_tier | high, mid, or low spend tier |
| price_pressure_score | high or normal market price pressure |
| supplier_concentration_risk | high, medium, or low supplier concentration risk |
| delivery_risk | high or low delivery risk |
| exception_purchase_risk | high or low exception purchase risk |
| standardization_opportunity | high or low standardization opportunity |
| substitute_readiness | available or unavailable substitute status |
| data_readiness | pass or fail data readiness |
| inventory_risk_level | high, medium, or low inventory risk |

## 5. Signal Definition

The former Model2 A/B concepts are reinterpreted as two procurement planning signal axes:

- Target A concept → cost_opportunity_signal
- Target B concept → supply_control_risk_signal

This MVP does not use a target-style scoring structure or fitted analytical engine. It uses state, signal, candidate action, gate, simulation, and final recommendation logic.

| Signal | Meaning |
|---|---|
| data_cleanup_signal | Data quality is too low for reliable action selection |
| cost_opportunity_signal | High spend and high price pressure indicate cost review opportunity |
| supply_control_risk_signal | Supplier concentration, delivery, or inventory risk is high |
| dual_source_signal | Single supplier and low delivery reliability indicate dual sourcing review |
| standardize_signal | Emergency purchasing and standardization opportunity are both high |
| substitute_signal | Inventory risk is high and a substitute exists |
| monitor_signal | No major action trigger is detected |

## 6. Candidate Actions

| Action | Meaning |
|---|---|
| data_cleanup_first | Prioritize data cleanup |
| maintain_contract | Maintain current contract |
| monitor_risk | Continue KPI monitoring |
| rebid | Run price review or rebid |
| annual_contract | Review annual unit-price contract |
| standardize_item | Review standard item conversion |
| dual_source | Review supplier diversification |
| review_substitute | Review substitute item |

## 7. Gate Rules

| Rule | Gate Result |
|---|---|
| Low data quality | data_cleanup_first passes first |
| Low data quality with other actions | other actions are blocked |
| No substitute item | review_substitute is blocked |
| Low standardization score | standardize_item is blocked |
| Supplier base and OTIF already acceptable | dual_source is deprioritized |

## 8. Simulation Logic

The simulator assigns simple expected effect scores:

| Action | Score Focus |
|---|---|
| rebid | Higher annual spend and price pressure increase cost opportunity |
| annual_contract | Mid or high spend and price pressure increase contract leverage score |
| dual_source | Single supplier and lower OTIF increase supply risk reduction |
| standardize_item | Emergency purchase ratio and standardization score increase stability score |
| review_substitute | Inventory risk and substitute availability increase risk reduction |
| data_cleanup_first | Lower data quality increases cleanup priority |

`priority_score` is a weighted combination of cost opportunity, supply risk reduction, and operation stability. Ties are resolved by action priority in `selector.py`.

## 9. KPI Candidates

- Category cost saving opportunity
- Contract compliance improvement
- Supplier OTIF improvement
- Emergency purchase reduction
- Standard item conversion
- Substitute item review
- Backorder or shortage risk reduction
- Report automation readiness

## 10. Limitations

This is synthetic demo data, not real healthcare purchasing data. The MVP is rule-based, does not replace healthcare procurement operations, and is intended to demonstrate decision structure for portfolio purposes.

## 11. Future Extension

Future versions could connect governed real data, BI dashboards, ML-based forecasting, RPA report automation, pharmaceutical categories, API categories, and supply disruption records.

