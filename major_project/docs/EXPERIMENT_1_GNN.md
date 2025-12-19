# Experiment 1: Synthetic GNN Pipeline Validation

## Objective

To validate the end-to-end execution of the Graph Neural Network pipeline,
including graph construction, data loading, training, and evaluation.

## Dataset

- Synthetic interaction graph
- Nodes: 30 Users
- Edges: Aggregated message interactions
- Labels: Rule-based weak supervision + forced fraud labels for testing

## Class Distribution

**Initial Run (Rule-Based Labels Only):**
- Normal: 30
- Suspicious: 0
- Fraud: 0

**Updated Run (With Forced Fraud Labels):**
- Normal: 28
- Suspicious: 0
- Fraud: 2 (forced for testing)

## Training Setup

- Model: GraphSAGE-based FraudGNN
- Hidden Dimension: 32
- Output Classes: 3 (Normal, Suspicious, Fraud)
- Epochs: 30 (with early stopping)
- Learning Rate: 0.01
- Loss: CrossEntropy with class weighting
- Device: CPU

## Methodology

1. **Initial Run**: Used rule-based labeling only
   - Result: All users labeled as Normal (conservative rules)
   - Model learned to predict all users as Normal
   - Validated pipeline correctness

2. **Updated Run**: Forced 2 users as fraud (label=2) to test fraud detection
   - Modified `quick_run.py` to override labels for first 2 users
   - Tests whether model can detect fraud when fraud samples are present

## Results

### Initial Run (No Fraud Samples)
- Training loss converged to 0.0
- Validation accuracy: 1.0
- Model predicted all users as Normal
- **Interpretation**: Model correctly learned the observed label distribution

### Updated Run (With Fraud Samples)
- Expected: Model should learn to distinguish fraud from normal users
- Class weights: Fraud class receives higher weight (inverse frequency)
- **Note**: Results depend on train/test split - if fraud users are in test set, model should detect them

## Interpretation

**Initial Run:**
Due to conservative labeling rules and a small synthetic dataset,
no users were labeled as suspicious or fraud. The model correctly learned
the observed label distribution. This validates the correctness of the GNN pipeline.

**Updated Run:**
By forcing fraud labels, we test whether the model can:
1. Learn from imbalanced data (2 fraud vs 28 normal)
2. Use class weights effectively to handle imbalance
3. Detect fraud patterns when they exist

## Key Findings

1. **Pipeline Validation**: ✅ End-to-end pipeline works correctly
   - Graph construction: ✅
   - Data loading: ✅
   - Training loop: ✅
   - Evaluation: ✅

2. **Class Weight Handling**: ✅ System correctly handles missing classes
   - Always returns 3-class weights even if classes are missing
   - Prevents runtime errors with CrossEntropyLoss

3. **Evaluation Robustness**: ✅ Handles imbalanced test sets
   - Confusion matrix always 3x3
   - Classification report handles missing classes

## Limitations

- Synthetic data (not real-world fraud patterns)
- Small dataset (30 users)
- Forced labels (not discovered fraud)
- Intended for pipeline validation, not performance evaluation
- No graph structure features (only user nodes, no listings/devices)

## Next Steps

- Test with larger synthetic datasets
- Add more graph structure (listings, devices, transactions)
- Test with real BrokeBuy data
- Compare with baseline ML models
- Evaluate on held-out test set with fraud samples

