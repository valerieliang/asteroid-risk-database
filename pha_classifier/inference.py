# inference.py

import numpy as np
from feature_engineering import engineer_features
from config import get_all_features


def run_inference(result, unlabelled, out_path):
    """
    Predict PHA status for unlabelled objects.
    
    Args:
        result: Evaluation result dictionary with trained model
        unlabelled: DataFrame of unlabelled objects
        out_path: Output path for predictions CSV
    """
    if unlabelled.empty:
        print("\n  No unlabelled rows to predict.")
        return

    df = engineer_features(unlabelled)
    num_feats, cat_feats = get_all_features()
    all_feats = num_feats + cat_feats
    X_infer = df[all_feats]

    pipe = result['pipe']
    probas = pipe.predict_proba(X_infer)[:, 1]
    preds = pipe.predict(X_infer)

    out = unlabelled[['spkid', 'full_name', 'class']].copy()
    out['pha_prob'] = np.round(probas, 4)
    out['pha_pred'] = np.where(preds == 1, 'Y', 'N')
    out = out.sort_values('pha_prob', ascending=False)

    out.to_csv(out_path, index=False)
    predicted_pha = (out['pha_pred'] == 'Y').sum()
    
    print(f"\n  Unlabelled inference: {len(out):,} objects")
    print(f"  Model predicts PHA-Y for {predicted_pha} of them ({100*predicted_pha/len(out):.1f}%)")
    print(f"  Saved -> {out_path}")
    print()
    print("  Top 10 predicted PHAs among unlabelled objects:")
    print(out.head(10).to_string(index=False))
    
    return out