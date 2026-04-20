# evaluation.py

import numpy as np
import json
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import (
    classification_report, roc_auc_score, confusion_matrix,
    average_precision_score, roc_curve, precision_recall_curve
)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from model_pipeline import get_feature_names


def evaluate_model(pipe, X_train, X_test, y_train, y_test):
    """
    Train and evaluate the Random Forest model.
    
    Args:
        pipe: Pipeline object
        X_train, X_test: Feature matrices
        y_train, y_test: Target vectors
        
    Returns:
        dict: Evaluation results
    """
    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)
    y_proba = pipe.predict_proba(X_test)[:, 1]

    roc_auc = roc_auc_score(y_test, y_proba)
    avg_prc = average_precision_score(y_test, y_proba)
    cm = confusion_matrix(y_test, y_pred)
    report = classification_report(
        y_test, y_pred, 
        target_names=['Non-PHA', 'PHA'], 
        output_dict=True
    )

    # 5-fold cross-validated ROC-AUC on training set
    cv_scores = cross_val_score(
        pipe, X_train, y_train,
        cv=StratifiedKFold(5, shuffle=True, random_state=0),
        scoring='roc_auc', n_jobs=-1
    )

    print(f"\n{'-'*52}")
    print(f"  Random Forest Model Evaluation")
    print(f"{'-'*52}")
    print(f"  ROC-AUC (test):        {roc_auc:.4f}")
    print(f"  Avg Precision (test):  {avg_prc:.4f}")
    print(f"  CV ROC-AUC (5-fold):   {cv_scores.mean():.4f} +- {cv_scores.std():.4f}")
    print()
    print(classification_report(y_test, y_pred, target_names=['Non-PHA', 'PHA']))

    return {
        'pipe': pipe,
        'y_pred': y_pred,
        'y_proba': y_proba,
        'roc_auc': roc_auc,
        'avg_prc': avg_prc,
        'cv_scores': cv_scores,
        'cm': cm,
        'report': report,
    }


def plot_diagnostics(result, X_test, y_test, out_path):
    """
    Create comprehensive diagnostic plots for Random Forest model.
    
    Args:
        result: Evaluation result dictionary
        X_test: Test feature matrix
        y_test: Test target vector
        out_path: Output path for plot
    """
    fig = plt.figure(figsize=(12, 8), facecolor='#060810')
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.35, wspace=0.35)

    TXT = '#e8eeff'
    MUTED = '#7a8ab5'
    BG = '#0d1120'
    PRIMARY = '#4f7cff'

    def style_ax(ax):
        ax.set_facecolor(BG)
        ax.tick_params(colors=MUTED, labelsize=9)
        for spine in ax.spines.values():
            spine.set_edgecolor('#1a2038')

    # ROC curve
    ax0 = fig.add_subplot(gs[0, 0])
    style_ax(ax0)
    fpr, tpr, _ = roc_curve(y_test, result['y_proba'])
    ax0.plot(fpr, tpr, color=PRIMARY, lw=2, 
            label=f"Random Forest (AUC={result['roc_auc']:.3f})")
    ax0.plot([0, 1], [0, 1], '--', color='#3d4d7a', lw=1)
    ax0.set_xlabel('False positive rate', color=MUTED, fontsize=9)
    ax0.set_ylabel('True positive rate', color=MUTED, fontsize=9)
    ax0.set_title('ROC Curve', color=TXT, fontsize=11, pad=8)
    ax0.legend(fontsize=9, facecolor='#131829', labelcolor=TXT, edgecolor='#1a2038')

    # Precision-Recall curve
    ax1 = fig.add_subplot(gs[0, 1])
    style_ax(ax1)
    prec, rec, _ = precision_recall_curve(y_test, result['y_proba'])
    ax1.plot(rec, prec, color=PRIMARY, lw=2, 
            label=f"Random Forest (AP={result['avg_prc']:.3f})")
    ax1.set_xlabel('Recall', color=MUTED, fontsize=9)
    ax1.set_ylabel('Precision', color=MUTED, fontsize=9)
    ax1.set_title('Precision-Recall Curve', color=TXT, fontsize=11, pad=8)
    ax1.legend(fontsize=9, facecolor='#131829', labelcolor=TXT, edgecolor='#1a2038')

    # Confusion matrix
    ax2 = fig.add_subplot(gs[1, 0])
    style_ax(ax2)
    cm = result['cm']
    im = ax2.imshow(cm, cmap='Blues', aspect='auto')
    ax2.set_xticks([0, 1])
    ax2.set_yticks([0, 1])
    ax2.set_xticklabels(['Non-PHA', 'PHA'], color=MUTED, fontsize=9)
    ax2.set_yticklabels(['Non-PHA', 'PHA'], color=MUTED, fontsize=9, 
                        rotation=90, va='center')
    for i in range(2):
        for j in range(2):
            ax2.text(j, i, f'{cm[i,j]:,}', ha='center', va='center',
                    color='white' if cm[i,j] > cm.max()/2 else MUTED, 
                    fontsize=12, fontweight='bold')
    ax2.set_title('Confusion Matrix', color=TXT, fontsize=11, pad=8)
    ax2.set_xlabel('Predicted', color=MUTED, fontsize=9)
    ax2.set_ylabel('Actual', color=MUTED, fontsize=9)

    # Probability distribution
    ax3 = fig.add_subplot(gs[1, 1])
    style_ax(ax3)
    ax3.hist(result['y_proba'][y_test == 1], bins=30, alpha=0.6, 
             color='#ff4f6a', label='PHA (Y)', density=True)
    ax3.hist(result['y_proba'][y_test == 0], bins=30, alpha=0.5,
             color='#3d4d7a', label='Non-PHA (N)', density=True)
    ax3.axvline(0.5, color=MUTED, lw=1, linestyle='--', label='Threshold')
    ax3.set_xlabel('Predicted PHA probability', color=MUTED, fontsize=9)
    ax3.set_ylabel('Density', color=MUTED, fontsize=9)
    ax3.set_title('Score Distribution', color=TXT, fontsize=11, pad=8)
    ax3.legend(fontsize=8, facecolor='#131829', labelcolor=TXT, edgecolor='#1a2038')

    fig.suptitle('Random Forest - PHA Prediction Diagnostics', color=TXT,
                 fontsize=14, fontweight='bold', y=1.01)
    plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='#060810')
    plt.close()
    print(f"  Saved -> {out_path}")


def plot_feature_importance(result, out_path, top_n=20):
    """
    Plot top N feature importances for Random Forest model.
    
    Args:
        result: Evaluation result dictionary
        out_path: Output path for plot
        top_n: Number of top features to display
    """
    pipe = result['pipe']
    clf = pipe.named_steps['classifier']
    names = get_feature_names(pipe)

    if hasattr(clf, 'feature_importances_'):
        imp = clf.feature_importances_
    else:
        print(f"  Warning: Cannot extract importance from model")
        return

    # Sort and get top N
    idx = np.argsort(imp)[-top_n:]
    
    fig, ax = plt.subplots(figsize=(10, 8))
    colors = ['#ff4f6a' if imp[i] > np.percentile(imp, 80) else '#4f7cff' 
              for i in idx]
    bars = ax.barh([names[i] for i in idx], imp[idx], color=colors, edgecolor='none')
    
    # Add value labels
    for bar, val in zip(bars, imp[idx]):
        ax.text(val + 0.002, bar.get_y() + bar.get_height()/2, 
                f'{val:.3f}', va='center', color='#e8eeff', fontsize=8)
    
    ax.set_xlabel('Feature Importance', color='#e8eeff', fontsize=11)
    ax.set_title(f'Top {top_n} Feature Importances - Random Forest', 
                 color='#e8eeff', fontsize=12, pad=12)
    ax.tick_params(colors='#7a8ab5', labelsize=9)
    for spine in ax.spines.values():
        spine.set_edgecolor('#1a2038')
    ax.set_facecolor('#0d1120')
    fig.patch.set_facecolor('#060810')
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved -> {out_path}")


def save_summary(result, out_path):
    """
    Save model performance summary as JSON.
    
    Args:
        result: Evaluation result dictionary
        out_path: Output path for JSON file
    """
    summary = {
        'model': 'Random Forest',
        'roc_auc': round(result['roc_auc'], 4),
        'avg_precision': round(result['avg_prc'], 4),
        'cv_roc_auc': round(result['cv_scores'].mean(), 4),
        'cv_std': round(result['cv_scores'].std(), 4),
        'pha_precision': round(result['report']['PHA']['precision'], 4),
        'pha_recall': round(result['report']['PHA']['recall'], 4),
        'pha_f1': round(result['report']['PHA']['f1-score'], 4),
        'non_pha_precision': round(result['report']['Non-PHA']['precision'], 4),
        'non_pha_recall': round(result['report']['Non-PHA']['recall'], 4),
        'non_pha_f1': round(result['report']['Non-PHA']['f1-score'], 4),
        'accuracy': round(result['report']['accuracy'], 4),
    }
    
    with open(out_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"  Saved -> {out_path}")
    
    return summary