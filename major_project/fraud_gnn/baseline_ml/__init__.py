"""
Baseline ML Models for Fraud Detection

This module provides traditional machine learning models (Logistic Regression,
Random Forest, Gradient Boosting) that serve as baselines before implementing
graph neural networks.

These models use ONLY flat features (no graph structure) to establish what
traditional ML can achieve without graph awareness.
"""

from .feature_vector import build_user_feature_vector, build_feature_matrix
from .models import (
    LogisticRegressionModel,
    RandomForestModel,
    GradientBoostingModel,
    convert_feature_dicts_to_matrix
)
from .train import (
    prepare_train_test_split,
    compute_class_weights,
    train_model,
    train_all_models,
    scale_features,
    save_model,
    load_model,
    save_all_models,
    complete_training_pipeline
)
from .evaluate import (
    compute_binary_metrics,
    compute_multiclass_metrics,
    compute_roc_auc,
    compute_confusion_matrix,
    print_confusion_matrix,
    evaluate_model,
    compare_models
)

__all__ = [
    # Feature construction
    "build_user_feature_vector",
    "build_feature_matrix",
    "convert_feature_dicts_to_matrix",
    # Models
    "LogisticRegressionModel",
    "RandomForestModel",
    "GradientBoostingModel",
    # Training
    "prepare_train_test_split",
    "compute_class_weights",
    "train_model",
    "train_all_models",
    "scale_features",
    "save_model",
    "load_model",
    "save_all_models",
    "complete_training_pipeline",
    # Evaluation
    "compute_binary_metrics",
    "compute_multiclass_metrics",
    "compute_roc_auc",
    "compute_confusion_matrix",
    "print_confusion_matrix",
    "evaluate_model",
    "compare_models",
]

