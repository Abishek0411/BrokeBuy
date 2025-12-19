"""
Graph Neural Network Module for Fraud Detection

This module implements GNN models using PyTorch Geometric for fraud detection.
It includes data loading, model definition, training, and evaluation.
"""

from .data_loader import load_graph_snapshot, create_data_loader
from .model import FraudGNN, FraudGNNWithAttention
from .train import (
    train_model,
    train_epoch,
    validate,
    compute_class_weights,
    load_checkpoint
)
from .evaluate import (
    evaluate_gnn,
    compare_with_baseline,
    get_per_class_performance
)

__all__ = [
    # Data loading
    "load_graph_snapshot",
    "create_data_loader",
    # Models
    "FraudGNN",
    "FraudGNNWithAttention",
    # Training
    "train_model",
    "train_epoch",
    "validate",
    "compute_class_weights",
    "load_checkpoint",
    # Evaluation
    "evaluate_gnn",
    "compare_with_baseline",
    "get_per_class_performance",
]

