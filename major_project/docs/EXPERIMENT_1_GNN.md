# Experiment 1: Synthetic GNN Pipeline Validation

## Objective

To validate the end-to-end execution of the Graph Neural Network pipeline,
including graph construction, data loading, training, and evaluation.

## Dataset

- Synthetic interaction graph
- Nodes: Users
- Edges: Aggregated message interactions
- Labels: Rule-based weak supervision

## Class Distribution

- Normal: 30
- Suspicious: 0
- Fraud: 0

## Training Setup

- Model: GraphSAGE-based FraudGNN
- Epochs: 30 (early stopping at 12)
- Loss: CrossEntropy with class weighting
- Device: CPU

## Results

- Training loss converged to 0.0
- Validation accuracy: 1.0
- Model predicted all users as Normal

## Interpretation

Due to conservative labeling rules and a small synthetic dataset,
no users were labeled as suspicious or fraud.

The model correctly learned the observed label distribution.

This experiment validates the correctness of the GNN pipeline,
not detection performance.

## Limitations

- Synthetic data
- No positive fraud samples
- Intended for pipeline validation only

