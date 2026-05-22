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


def run_pipeline(
    input_path: str = "data/healthcare_gpo_mvp_demo.csv",
    output_dir: str = "outputs",
    example_path: str = "examples/healthcare_gpo_mvp_recommendations_sample.csv",
) -> dict:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    Path(example_path).parent.mkdir(parents=True, exist_ok=True)

    state_df = build_state(input_path)
    signal_df = build_signals(state_df)
    candidate_df = build_candidates(signal_df)
    gated_candidate_df = apply_gates(candidate_df, signal_df)
    simulation_result_df = simulate_actions(gated_candidate_df, signal_df)
    final_decision_df = select_final_actions(simulation_result_df)
    recommendation_df = translate_actions(final_decision_df, signal_df)

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

