# Decision Flow

Input → State generation → Signal interpretation → Candidate action generation → Gate check → Scenario simulation → Final action recommendation

Input row: `decision_month + item_id`

| Step | Input | Output | File |
|---|---|---|---|
| Input | Synthetic demo item data | Raw purchasing category table | data/healthcare_gpo_mvp_demo.csv |
| State generation | Input CSV | State features | outputs/state_df.csv |
| Signal interpretation | State features | Opportunity and risk signals | outputs/signal_df.csv |
| Candidate action generation | Signals | Long-format candidate actions | outputs/candidate_df.csv |
| Gate check | Candidate actions and item context | Gate status and gate reason | outputs/gated_candidate_df.csv |
| Scenario simulation | Gated candidates | Expected effect scores | outputs/simulation_result_df.csv |
| Final action recommendation | Scenario scores | Selected action per item | outputs/final_decision_df.csv |
| Portfolio output | Final action table | Human-readable recommendations | outputs/healthcare_gpo_mvp_recommendations.csv |
