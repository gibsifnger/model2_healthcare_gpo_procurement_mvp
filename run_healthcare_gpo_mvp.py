from healthcare_gpo_mvp.pipeline import run_pipeline


def main() -> None:
    result = run_pipeline()
    print(f"input path: {result['input_path']}")
    print(f"output path: {result['output_path']}")
    print(f"number of input rows: {result['input_rows']}")
    print(f"number of final recommendations: {result['final_recommendations']}")
    print(f"saved output file path: {result['saved_output_file']}")


if __name__ == "__main__":
    main()
