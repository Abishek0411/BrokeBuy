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
- **Class Distribution**: Normal: 27, Suspicious: 1, Fraud: 2
- **Class Weights**: Normal: 0.0723, Suspicious: 1.9518, Fraud: 0.9759
- **Training**: Model trained successfully, training accuracy: 95.24%
- **Test Set Issue**: All fraud users (2) ended up in training set, test set only contains Normal users
- **Test Results**: Model correctly predicted all 5 test users as Normal (100% accuracy)
- **Limitation**: Cannot evaluate fraud detection performance because no fraud samples in test set

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
   - Correctly weights rare classes (Suspicious: 1.95x, Fraud: 0.98x)

3. **Evaluation Robustness**: ✅ Handles imbalanced test sets
   - Confusion matrix always 3x3
   - Classification report handles missing classes

4. **Train/Test Split Issue**: ⚠️ Small dataset limitation
   - With only 2 fraud samples, stratified split placed both in training set
   - Test set contains only Normal users (5 samples)
   - Model correctly predicts Normal users (100% accuracy on test set)
   - **Cannot evaluate fraud detection** because no fraud in test set
   - This is expected with very small datasets and rare classes

## Limitations

- Synthetic data (not real-world fraud patterns)
- Small dataset (30 users) - too small for meaningful train/test split
- Forced labels (not discovered fraud)
- **Train/test split issue**: All fraud samples ended up in training, none in test
- Intended for pipeline validation, not performance evaluation
- No graph structure features (only user nodes, no listings/devices)
- Cannot evaluate fraud detection performance (no fraud in test set)

## Next Steps

- **Larger Dataset**: Test with 100+ users to ensure fraud samples in test set
- **Manual Split**: Use manual train/test split to ensure fraud samples in both sets
- **More Graph Structure**: Add listings, devices, transactions for richer graph
- **Real Data**: Test with real BrokeBuy data
- **Baseline Comparison**: Compare GNN with baseline ML models
- **Cross-Validation**: Use k-fold CV to better evaluate with small datasets

## Actual Results Summary

**Training:**
- Loss: Converged to 0.0 (best validation loss)
- Training Accuracy: 95.24% (20/21 samples correct)
- Early Stopping: Epoch 13 (out of 30)

**Test Set:**
- Test Samples: 5 (all Normal users)
- Test Accuracy: 100% (5/5 correct)
- Fraud Detection: Cannot evaluate (no fraud in test set)

**Model Behavior:**
- Model learned to predict Normal class correctly
- Training set contained 2 fraud users, model saw them during training
- Test set only had Normal users, model correctly identified them
- This validates the pipeline works, but cannot test fraud detection capability

