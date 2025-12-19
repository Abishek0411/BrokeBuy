"""
Evaluation Module for Baseline ML Models

This module provides comprehensive evaluation metrics for fraud detection
models, including precision, recall, F1-score, ROC-AUC, and confusion matrices.

Why Recall is Critical for Fraud Detection
-------------------------------------------

Recall (True Positive Rate) measures: Of all actual fraud cases, how many
did we catch?

Recall = True Positives / (True Positives + False Negatives)

In fraud detection:
- **False Negatives (Missed Fraud)**: Very costly!
  - Fraudster continues operating
  - Users lose money
  - Platform reputation damaged
  
- **False Positives (Legitimate User Flagged)**: Less costly
  - User can appeal
  - Can be resolved with verification
  - Better to be safe than sorry

Therefore, we prioritize **high recall** (catching fraud) even if it means
some false positives. A model with 90% recall catches 9 out of 10 fraudsters,
which is much better than 50% recall (5 out of 10).

Tradeoff Between False Positives and False Negatives
-----------------------------------------------------

This is a fundamental tradeoff in fraud detection:

**High Recall, Low Precision** (Catch most fraud, but flag many false positives):
- Pros: Catch most fraudsters
- Cons: Many legitimate users flagged (bad user experience)
- Use case: Initial screening, manual review queue

**Low Recall, High Precision** (Catch few fraud, but very accurate):
- Pros: Few false positives (good user experience)
- Cons: Many fraudsters slip through
- Use case: Final blocking decisions (after verification)

**Balanced Approach**:
- Moderate recall and precision
- Use multiple stages: High-recall screening → Verification → High-precision blocking

The optimal balance depends on:
- Cost of false negatives (missed fraud)
- Cost of false positives (user friction)
- Available resources for manual review
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    accuracy_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)


def compute_binary_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Compute binary classification metrics.
    
    For multi-class problems, this converts to binary by treating
    fraud (label 2) as positive and everything else as negative.
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        
    Returns:
        Dictionary of metrics
    """
    # Convert to binary: fraud (2) vs non-fraud (0, 1)
    y_true_binary = (y_true == 2).astype(int)
    y_pred_binary = (y_pred == 2).astype(int)
    
    precision = precision_score(y_true_binary, y_pred_binary, zero_division=0)
    recall = recall_score(y_true_binary, y_pred_binary, zero_division=0)
    f1 = f1_score(y_true_binary, y_pred_binary, zero_division=0)
    accuracy = accuracy_score(y_true_binary, y_pred_binary)
    
    return {
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'accuracy': accuracy
    }


def compute_multiclass_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, any]:
    """
    Compute multi-class classification metrics.
    
    Computes metrics for each class (normal, suspicious, fraud) as well
    as macro and weighted averages.
    
    Args:
        y_true: True labels (0, 1, or 2)
        y_pred: Predicted labels (0, 1, or 2)
        
    Returns:
        Dictionary of metrics
    """
    # Per-class metrics
    precision_per_class = precision_score(y_true, y_pred, average=None, zero_division=0)
    recall_per_class = recall_score(y_true, y_pred, average=None, zero_division=0)
    f1_per_class = f1_score(y_true, y_pred, average=None, zero_division=0)
    
    # Macro averages (unweighted mean across classes)
    precision_macro = precision_score(y_true, y_pred, average='macro', zero_division=0)
    recall_macro = recall_score(y_true, y_pred, average='macro', zero_division=0)
    f1_macro = f1_score(y_true, y_pred, average='macro', zero_division=0)
    
    # Weighted averages (weighted by class frequency)
    precision_weighted = precision_score(y_true, y_pred, average='weighted', zero_division=0)
    recall_weighted = recall_score(y_true, y_pred, average='weighted', zero_division=0)
    f1_weighted = f1_score(y_true, y_pred, average='weighted', zero_division=0)
    
    # Overall accuracy
    accuracy = accuracy_score(y_true, y_pred)
    
    return {
        'per_class': {
            'normal': {
                'precision': precision_per_class[0],
                'recall': recall_per_class[0],
                'f1_score': f1_per_class[0]
            },
            'suspicious': {
                'precision': precision_per_class[1] if len(precision_per_class) > 1 else 0.0,
                'recall': recall_per_class[1] if len(recall_per_class) > 1 else 0.0,
                'f1_score': f1_per_class[1] if len(f1_per_class) > 1 else 0.0
            },
            'fraud': {
                'precision': precision_per_class[2] if len(precision_per_class) > 2 else 0.0,
                'recall': recall_per_class[2] if len(recall_per_class) > 2 else 0.0,
                'f1_score': f1_per_class[2] if len(f1_per_class) > 2 else 0.0
            }
        },
        'macro': {
            'precision': precision_macro,
            'recall': recall_macro,
            'f1_score': f1_macro
        },
        'weighted': {
            'precision': precision_weighted,
            'recall': recall_weighted,
            'f1_score': f1_weighted
        },
        'accuracy': accuracy
    }


def compute_roc_auc(y_true: np.ndarray, y_proba: np.ndarray, multi_class: str = 'ovr') -> float:
    """
    Compute ROC-AUC score.
    
    For multi-class problems, uses one-vs-rest (ovr) or one-vs-one (ovo) strategy.
    
    ROC-AUC measures the model's ability to distinguish between classes.
    Higher AUC (closer to 1.0) means better discrimination.
    
    Args:
        y_true: True labels
        y_proba: Predicted probabilities (n_samples, n_classes)
        multi_class: Strategy for multi-class ('ovr' or 'ovo')
        
    Returns:
        ROC-AUC score
    """
    try:
        # For binary classification
        if y_proba.shape[1] == 2:
            # Use probability of positive class
            return roc_auc_score(y_true == 2, y_proba[:, 1])
        else:
            # Multi-class
            return roc_auc_score(y_true, y_proba, multi_class=multi_class)
    except Exception as e:
        print(f"Error computing ROC-AUC: {e}")
        return 0.0


def compute_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
    """
    Compute confusion matrix.
    
    Rows = True labels, Columns = Predicted labels
    
    For 3 classes (normal, suspicious, fraud):
    ```
                Predicted
              Normal  Susp  Fraud
    Normal    [  TN     FP     FP  ]
    Susp      [  FN     TP     FP  ]
    Fraud     [  FN     FN     TP  ]
    ```
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        
    Returns:
        Confusion matrix (n_classes, n_classes)
    """
    return confusion_matrix(y_true, y_pred)


def print_confusion_matrix(cm: np.ndarray, class_names: List[str] = None) -> None:
    """
    Print confusion matrix in a readable format.
    
    Args:
        cm: Confusion matrix
        class_names: Optional list of class names
    """
    if class_names is None:
        class_names = ['Normal', 'Suspicious', 'Fraud']
    
    print("\nConfusion Matrix:")
    print(" " * 15, end="")
    for name in class_names:
        print(f"{name:>12}", end="")
    print()
    
    for i, name in enumerate(class_names):
        print(f"{name:>12}", end="")
        for j in range(len(class_names)):
            print(f"{cm[i, j]:>12}", end="")
        print()


def evaluate_model(
    model,
    X_test: np.ndarray,
    y_test: np.ndarray,
    print_report: bool = True
) -> Dict[str, any]:
    """
    Comprehensive evaluation of a model.
    
    Computes all metrics: precision, recall, F1, accuracy, ROC-AUC,
    and confusion matrix.
    
    Args:
        model: Trained model instance
        X_test: Test features
        y_test: Test labels
        print_report: Whether to print detailed report
        
    Returns:
        Dictionary containing all metrics
    """
    # Predictions
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)
    
    # Binary metrics (fraud vs non-fraud)
    binary_metrics = compute_binary_metrics(y_test, y_pred)
    
    # Multi-class metrics
    multiclass_metrics = compute_multiclass_metrics(y_test, y_pred)
    
    # ROC-AUC
    roc_auc = compute_roc_auc(y_test, y_proba)
    
    # Confusion matrix
    cm = compute_confusion_matrix(y_test, y_pred)
    
    # Classification report
    if print_report:
        print("\n" + "="*60)
        print("MODEL EVALUATION REPORT")
        print("="*60)
        
        print("\nBinary Classification (Fraud vs Non-Fraud):")
        print(f"  Precision: {binary_metrics['precision']:.4f}")
        print(f"  Recall:    {binary_metrics['recall']:.4f}")
        print(f"  F1-Score:  {binary_metrics['f1_score']:.4f}")
        print(f"  Accuracy:  {binary_metrics['accuracy']:.4f}")
        
        print("\nMulti-Class Classification:")
        print(f"  Macro Precision: {multiclass_metrics['macro']['precision']:.4f}")
        print(f"  Macro Recall:    {multiclass_metrics['macro']['recall']:.4f}")
        print(f"  Macro F1-Score:  {multiclass_metrics['macro']['f1_score']:.4f}")
        print(f"  Overall Accuracy: {multiclass_metrics['accuracy']:.4f}")
        
        print("\nPer-Class Metrics:")
        for class_name, metrics in multiclass_metrics['per_class'].items():
            print(f"  {class_name.capitalize()}:")
            print(f"    Precision: {metrics['precision']:.4f}")
            print(f"    Recall:    {metrics['recall']:.4f}")
            print(f"    F1-Score:  {metrics['f1_score']:.4f}")
        
        print(f"\nROC-AUC Score: {roc_auc:.4f}")
        
        print_confusion_matrix(cm)
        
        print("\nDetailed Classification Report:")
        print(classification_report(y_test, y_pred, target_names=['Normal', 'Suspicious', 'Fraud']))
    
    return {
        'binary_metrics': binary_metrics,
        'multiclass_metrics': multiclass_metrics,
        'roc_auc': roc_auc,
        'confusion_matrix': cm,
        'y_pred': y_pred,
        'y_proba': y_proba
    }


def compare_models(
    models: Dict[str, any],
    X_test: np.ndarray,
    y_test: np.ndarray
) -> Dict[str, Dict[str, any]]:
    """
    Compare multiple models side-by-side.
    
    Args:
        models: Dictionary mapping model names to model instances
        X_test: Test features
        y_test: Test labels
        
    Returns:
        Dictionary mapping model names to evaluation results
    """
    results = {}
    
    for name, model in models.items():
        print(f"\n{'='*60}")
        print(f"Evaluating {name.upper()}")
        print('='*60)
        results[name] = evaluate_model(model, X_test, y_test, print_report=True)
    
    # Summary comparison
    print("\n" + "="*60)
    print("MODEL COMPARISON SUMMARY")
    print("="*60)
    print(f"{'Model':<20} {'Precision':<12} {'Recall':<12} {'F1-Score':<12} {'ROC-AUC':<12}")
    print("-"*60)
    
    for name, result in results.items():
        binary = result['binary_metrics']
        roc_auc = result['roc_auc']
        print(f"{name:<20} {binary['precision']:<12.4f} {binary['recall']:<12.4f} "
              f"{binary['f1_score']:<12.4f} {roc_auc:<12.4f}")
    
    return results

