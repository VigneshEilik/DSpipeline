import argparse
import json
import sys
from pathlib import Path
import pandas as pd

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from ml.pipelines.training.trainer import train_churn_model, SUPPORTED_ALGORITHMS
from ml.pipelines.validation.validator import validate_churn_dataset

def main():
    parser = argparse.ArgumentParser(description="ModelOps Studio CLI Model Trainer")
    parser.add_argument("--data", type=str, default="datasets/samples/telco_churn_sample.csv", help="Path to CSV dataset")
    parser.add_argument("--algorithm", type=str, default="logistic_regression", choices=list(SUPPORTED_ALGORITHMS.keys()), help="Model algorithm")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--test-size", type=float, default=0.20, help="Test split ratio")
    parser.add_argument("--output-dir", type=str, default="storage/models", help="Directory to save model artifact")
    args = parser.parse_args()

    print(f"Loading dataset from: {args.data}")
    df = pd.read_csv(args.data)

    print("Validating dataset...")
    is_valid, report = validate_churn_dataset(df)
    if not is_valid:
        print("Dataset validation FAILED:")
        print(json.dumps(report["errors"], indent=2))
        sys.exit(1)
    print(f"Validation status: {report['status']}")

    print(f"Starting training run: Algorithm={args.algorithm}, Seed={args.seed}, TestSize={args.test_size}")
    pipeline, metrics = train_churn_model(
        df=df,
        algorithm=args.algorithm,
        random_seed=args.seed,
        test_size=args.test_size,
        artifact_output_dir=args.output_dir,
    )

    print("\n--- Training Evaluation Results ---")
    print(f"Accuracy:  {metrics['accuracy']:.4f}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall:    {metrics['recall']:.4f}")
    print(f"F1 Score:  {metrics['f1_score']:.4f}")
    if metrics["roc_auc"]:
        print(f"ROC AUC:   {metrics['roc_auc']:.4f}")
    if metrics["pr_auc"]:
        print(f"PR AUC:    {metrics['pr_auc']:.4f}")
    print(f"Artifact:  {metrics['artifact_path']}")
    print("-----------------------------------")

if __name__ == "__main__":
    main()
