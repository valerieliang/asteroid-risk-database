# run_pipeline.py

"""
Usage: python run_pipeline.py --input data/sbdb_query_results.csv --outdir outputs
"""

import argparse
import os
import warnings
warnings.filterwarnings('ignore')

from sklearn.model_selection import train_test_split

from data_loader import load_data
from feature_engineering import engineer_features, prepare_features
from model_pipeline import build_pipeline
from evaluation import evaluate_model, plot_diagnostics, plot_feature_importance, save_summary
from inference import run_inference


def main():
    parser = argparse.ArgumentParser(description='PHA Classification Pipeline - Random Forest')
    parser.add_argument('--input', default='./',
                       help='Path to input CSV file')
    parser.add_argument('--outdir', default='./outputs',
                       help='Output directory for results')
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    print("=" * 52)
    print("  NEO PHA PREDICTION - RANDOM FOREST PIPELINE")
    print("=" * 52)

    # 1. Load data
    labelled, unlabelled = load_data(args.input)

    # 2. Feature engineering
    print("\n[1] Engineering features...")
    df = engineer_features(labelled)
    X, y = prepare_features(df)

    print(f"     Feature matrix: {X.shape[0]:,} rows x {X.shape[1]} columns")
    print(f"     Class balance: PHA-Y={y.sum():,} ({100*y.mean():.1f}%)  "
          f"PHA-N={(~y.astype(bool)).sum():,} ({100*(1-y.mean()):.1f}%)")

    # 3. Train/test split
    print("\n[2] Splitting 80/20 (stratified)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=0, stratify=y
    )
    print(f"     Train: {len(X_train):,}  Test: {len(X_test):,}")

    # 4. Train model
    print("\n[3] Training Random Forest model...")
    pipe = build_pipeline()
    result = evaluate_model(pipe, X_train, X_test, y_train, y_test)

    # 5. Generate plots
    print("\n[4] Generating diagnostic plots...")
    plot_diagnostics(result, X_test, y_test,
                    f'{args.outdir}/diagnostics.png')
    plot_feature_importance(result, f'{args.outdir}/feature_importance.png')

    # 6. Run inference
    print("\n[5] Running inference on unlabelled objects...")
    run_inference(result, unlabelled, f'{args.outdir}/predictions_unlabelled.csv')

    # 7. Save summary
    print("\n[6] Saving summary JSON...")
    summary = save_summary(result, f'{args.outdir}/model_summary.json')
    
    print("\n" + "=" * 52)
    print("  Model Performance Summary")
    print("=" * 52)
    for key, value in summary.items():
        if key != 'model':
            print(f"  {key.replace('_', ' ').title()}: {value}")
    print("=" * 52)
    print("\n  Done. All outputs in", args.outdir)
    print("=" * 52)


if __name__ == '__main__':
    main()