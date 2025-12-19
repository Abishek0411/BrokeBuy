"""
Evaluation Module for Graph Neural Network

This module provides evaluation metrics for the GNN model, including
direct comparison with baseline ML models from Step 3.
"""

import torch
import numpy as np
from torch_geometric.data import Data
from typing import Dict, List, Optional
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    accuracy_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)

from .model import FraudGNN


def evaluate_gnn(
    model: FraudGNN,
    data: Data,
    mask: torch.Tensor = None,
    print_report: bool = True
) -> Dict:
    """
    Evaluate GNN model on test set.
    
    Args:
        model: Trained FraudGNN model
        data: PyTorch Geometric Data object
        mask: Optional mask for nodes to evaluate (if None, uses test_mask)
        print_report: Whether to print detailed report
        
    Returns:
        Dictionary of evaluation metrics
    """
    model.eval()
    
    if mask is None:
        mask = data.test_mask
    
    with torch.no_grad():
        out = model(data)
        
        # Get predictions and labels for masked nodes
        pred = out[mask].argmax(dim=1).cpu().numpy()
        proba = torch.softmax(out[mask], dim=1).cpu().numpy()
        labels = data.y[mask].cpu().numpy()
    
    # Filter out unlabeled nodes (label == -1)
    valid_mask = labels >= 0
    pred = pred[valid_mask]
    proba = proba[valid_mask]
    labels = labels[valid_mask]
    
    if len(labels) == 0:
        print("No labeled nodes to evaluate")
        return {}
    
    # Binary metrics (fraud vs non-fraud)
    labels_binary = (labels == 2).astype(int)
    pred_binary = (pred == 2).astype(int)
    
    binary_metrics = {
        'precision': precision_score(labels_binary, pred_binary, zero_division=0),
        'recall': recall_score(labels_binary, pred_binary, zero_division=0),
        'f1_score': f1_score(labels_binary, pred_binary, zero_division=0),
        'accuracy': accuracy_score(labels_binary, pred_binary)
    }
    
    # Multi-class metrics
    precision_per_class = precision_score(labels, pred, average=None, zero_division=0)
    recall_per_class = recall_score(labels, pred, average=None, zero_division=0)
    f1_per_class = f1_score(labels, pred, average=None, zero_division=0)
    
    multiclass_metrics = {
        'per_class': {
            'normal': {
                'precision': precision_per_class[0] if len(precision_per_class) > 0 else 0.0,
                'recall': recall_per_class[0] if len(recall_per_class) > 0 else 0.0,
                'f1_score': f1_per_class[0] if len(f1_per_class) > 0 else 0.0
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
            'precision': precision_score(labels, pred, average='macro', zero_division=0),
            'recall': recall_score(labels, pred, average='macro', zero_division=0),
            'f1_score': f1_score(labels, pred, average='macro', zero_division=0)
        },
        'weighted': {
            'precision': precision_score(labels, pred, average='weighted', zero_division=0),
            'recall': recall_score(labels, pred, average='weighted', zero_division=0),
            'f1_score': f1_score(labels, pred, average='weighted', zero_division=0)
        },
        'accuracy': accuracy_score(labels, pred)
    }
    
    # ROC-AUC
    try:
        if len(np.unique(labels_binary)) > 1:
            roc_auc = roc_auc_score(labels_binary, proba[:, 2])  # Probability of fraud class
        else:
            roc_auc = 0.0
    except:
        roc_auc = 0.0
    
    # Confusion matrix
    cm = confusion_matrix(labels, pred)
    
    if print_report:
        print("\n" + "="*60)
        print("GNN MODEL EVALUATION")
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
        
        print("\nConfusion Matrix:")
        print(" " * 15, end="")
        for name in ['Normal', 'Suspicious', 'Fraud']:
            print(f"{name:>12}", end="")
        print()
        for i, name in enumerate(['Normal', 'Suspicious', 'Fraud']):
            print(f"{name:>12}", end="")
            for j in range(len(cm[0])):
                print(f"{cm[i, j]:>12}", end="")
            print()
        
        print("\nDetailed Classification Report:")
        print(classification_report(labels, pred, target_names=['Normal', 'Suspicious', 'Fraud']))
    
    return {
        'binary_metrics': binary_metrics,
        'multiclass_metrics': multiclass_metrics,
        'roc_auc': roc_auc,
        'confusion_matrix': cm,
        'predictions': pred,
        'probabilities': proba
    }


def compare_with_baseline(
    gnn_results: Dict,
    baseline_results: Dict,
    baseline_name: str = "Baseline ML"
) -> None:
    """
    Compare GNN results with baseline ML results.
    
    Args:
        gnn_results: GNN evaluation results
        baseline_results: Baseline ML evaluation results
        baseline_name: Name of baseline model
    """
    print("\n" + "="*60)
    print("GNN vs BASELINE COMPARISON")
    print("="*60)
    
    gnn_binary = gnn_results['binary_metrics']
    baseline_binary = baseline_results['binary_metrics']
    
    print(f"\n{'Metric':<20} {'GNN':<15} {baseline_name:<15} {'Improvement':<15}")
    print("-"*60)
    
    metrics = ['precision', 'recall', 'f1_score', 'accuracy']
    for metric in metrics:
        gnn_val = gnn_binary[metric]
        baseline_val = baseline_binary[metric]
        improvement = gnn_val - baseline_val
        improvement_pct = (improvement / baseline_val * 100) if baseline_val > 0 else 0
        
        print(f"{metric.capitalize():<20} {gnn_val:<15.4f} {baseline_val:<15.4f} "
              f"{improvement:+.4f} ({improvement_pct:+.1f}%)")
    
    # ROC-AUC comparison
    gnn_auc = gnn_results.get('roc_auc', 0.0)
    baseline_auc = baseline_results.get('roc_auc', 0.0)
    auc_improvement = gnn_auc - baseline_auc
    auc_improvement_pct = (auc_improvement / baseline_auc * 100) if baseline_auc > 0 else 0
    
    print(f"{'ROC-AUC':<20} {gnn_auc:<15.4f} {baseline_auc:<15.4f} "
          f"{auc_improvement:+.4f} ({auc_improvement_pct:+.1f}%)")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    avg_improvement = np.mean([
        gnn_binary['precision'] - baseline_binary['precision'],
        gnn_binary['recall'] - baseline_binary['recall'],
        gnn_binary['f1_score'] - baseline_binary['f1_score']
    ])
    
    if avg_improvement > 0:
        print(f"✅ GNN outperforms {baseline_name} by {avg_improvement:.4f} on average")
        print(f"   Key improvement: Recall (+{gnn_binary['recall'] - baseline_binary['recall']:.4f})")
    else:
        print(f"⚠️  GNN does not outperform {baseline_name}")
        print(f"   Consider: feature engineering, hyperparameter tuning, or more data")


def get_per_class_performance(
    model: FraudGNN,
    data: Data,
    mask: torch.Tensor = None
) -> Dict[str, Dict]:
    """
    Get detailed per-class performance metrics.
    
    Args:
        model: Trained FraudGNN model
        data: PyTorch Geometric Data object
        mask: Optional mask for nodes to evaluate
        
    Returns:
        Dictionary with per-class metrics
    """
    results = evaluate_gnn(model, data, mask, print_report=False)
    return results['multiclass_metrics']['per_class']

