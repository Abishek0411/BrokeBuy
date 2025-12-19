# Experiment 2: Controlled GNN Evaluation

## Objective

To evaluate GNN fraud detection performance with a controlled synthetic dataset
and deterministic train/val/test splits ensuring fraud samples in all sets.

## Dataset

- **Total Users**: 150
- **Normal**: 115 users
- **Suspicious**: 15 users
- **Fraud**: 20 users

### User Behavior Patterns

**Fraud Users:**
- Very high message count (50-100)
- Very low account age (1-7 days)
- High listing count (15-30)
- No verification
- Communicate with many distinct users (spam behavior)

**Suspicious Users:**
- Medium message count (20-40)
- Medium account age (8-30 days)
- Medium listing count (8-15)
- Mixed verification status
- Some communication overlap

**Normal Users:**
- Low message count (3-15)
- High account age (60-365 days)
- Low listing count (1-8)
- Verified status
- Sparse interactions

## Train/Val/Test Split

**Deterministic Split (Not Random):**

- **Training Set**: 105 users (70%)
  - Fraud: 10, Suspicious: 10, Normal: 85
  
- **Validation Set**: 22 users (15%)
  - Fraud: 5, Suspicious: 2, Normal: 15
  
- **Test Set**: 23 users (15%)
  - Fraud: 5, Suspicious: 3, Normal: 15

**Why Deterministic Split?**

With rare classes (fraud = 13%), random stratified splits can fail to ensure
fraud samples in all splits. Manual control guarantees:
- At least 10 fraud users in training (for learning)
- At least 5 fraud users in validation (for early stopping)
- At least 5 fraud users in test (for evaluation)

## Training Setup

- **Model**: GraphSAGE-based FraudGNN
- **Hidden Dimension**: 64
- **Layers**: 2
- **Dropout**: 0.5
- **Epochs**: 50 (with early stopping, patience=10)
- **Learning Rate**: 0.01
- **Loss**: CrossEntropyLoss with class weighting
- **Device**: CPU

## Results

### Training History

- **Epochs Trained**: 33
- **Best Validation Loss**: 0.0680

### Test Set Performance

**Overall Metrics:**
- Accuracy: 1.0000
- Macro Precision: 1.0000
- Macro Recall: 1.0000
- Macro F1-Score: 1.0000

**Fraud Detection (Class 2) - PRIMARY METRIC:**
- Precision: 1.0000
- Recall: 1.0000
- F1-Score: 1.0000

**Per-Class Performance:**

Normal:
- Precision: 1.0000
- Recall: 1.0000
- F1-Score: 1.0000

Suspicious:
- Precision: 1.0000
- Recall: 1.0000
- F1-Score: 1.0000

Fraud:
- Precision: 1.0000
- Recall: 1.0000
- F1-Score: 1.0000

### Confusion Matrix (Test Set)

```
                Normal  Suspicious       Fraud
      Normal           15            0            0
  Suspicious            0            3            0
       Fraud            0            0            5
```

### Binary Classification (Fraud vs Non-Fraud)

- Precision: 1.0000
- Recall: 1.0000
- F1-Score: 1.0000
- Accuracy: 1.0000
- ROC-AUC: 1.0000

## Interpretation

### Fraud Detection Performance

The model achieved:
- **Recall**: 1.0000 - Of 5 actual fraud cases, detected 5 correctly
- **Precision**: 1.0000 - Of 5 predicted fraud cases, 5 were actually fraud

### Why Perfect Results Don't Mean Production-Ready

**⚠️ Important Caveat**: Perfect results on synthetic data do NOT mean the model is production-ready.

**Reasons:**

1. **Synthetic Data**: Fraud users have **obvious, exaggerated patterns**:
   - Very high message counts (50-100)
   - Very new accounts (1-7 days)
   - Clear spam behavior
   - Real fraud is more subtle and diverse

2. **Controlled Behaviors**: We designed fraud users to be easily distinguishable.
   Real fraudsters adapt and use more sophisticated patterns.

3. **Small Test Set**: Only 5 fraud samples in test set. Perfect performance
   on 5 samples doesn't guarantee performance on thousands.

4. **No Graph Complexity**: Only user-to-user messages. Real graphs have:
   - Listings, devices, transactions
   - Complex multi-hop relationships
   - Temporal evolution
   - Adversarial patterns

5. **No Adversarial Testing**: Real fraudsters actively try to evade detection.
   This experiment doesn't test evasion resistance.

### What This Experiment Actually Validates

✅ **Pipeline Correctness**: End-to-end GNN pipeline works correctly
✅ **Evaluation Protocol**: Deterministic splits enable proper evaluation
✅ **Class Imbalance Handling**: Model can learn from imbalanced data
✅ **Basic Pattern Learning**: Model can distinguish clear fraud patterns

### What's Still Needed for Production

❌ **Real-World Data**: Test on actual BrokeBuy marketplace data
❌ **Adversarial Testing**: Test against adaptive fraudsters
❌ **Larger Scale**: Evaluate on 1000+ users, not 150
❌ **Graph Complexity**: Add listings, devices, transactions
❌ **Temporal Dynamics**: Test on evolving graphs over time
❌ **Baseline Comparison**: Compare with baseline ML models
❌ **False Positive Analysis**: Understand cost of false positives

### Key Observations

1. **Fraud Detection**: Model successfully detected all fraud cases in test set
2. **False Positives**: 0 normal/suspicious users incorrectly flagged as fraud
3. **False Negatives**: 0 fraud cases missed
4. **Perfect Confusion Matrix**: All 23 test samples classified correctly

### Is the Model "Great"?

**Short Answer**: The model works correctly on synthetic data with clear patterns, but this doesn't mean it's production-ready.

**What We Can Say:**
- ✅ The GNN pipeline is **functionally correct**
- ✅ The model can learn fraud patterns when they're **obvious**
- ✅ The evaluation protocol is **sound**
- ✅ Class imbalance handling **works**

**What We Cannot Say:**
- ❌ The model will work on **real-world data**
- ❌ The model can detect **subtle fraud patterns**
- ❌ The model is **production-ready**
- ❌ The model can handle **adversarial fraudsters**

## Comparison with Experiment 1

**Experiment 1**: Pipeline validation only (no fraud in test set)
**Experiment 2**: Meaningful fraud detection evaluation (fraud in all splits)

This experiment demonstrates:
- ✅ GNN can learn fraud patterns when fraud samples are present
- ✅ Deterministic splits enable proper evaluation
- ✅ Class weighting helps with imbalanced data
- ✅ Perfect performance on synthetic data with clear patterns

**However**, perfect results should be interpreted cautiously:
- Synthetic data has obvious fraud patterns
- Real-world fraud is more subtle and adaptive
- Production deployment requires real data testing

## Limitations

- **Synthetic Data**: Not real-world fraud patterns
- **Controlled Behaviors**: Fraud users have obvious, exaggerated patterns
- **Small Dataset**: 150 users (production systems handle 10,000+)
- **Small Test Set**: Only 5 fraud samples in test (too small for statistical significance)
- **No Graph Complexity**: Only user-to-user messages (no listings/devices/transactions)
- **No Adversarial Testing**: Real fraudsters adapt and evade detection
- **Perfect Results Are Expected**: With such clear patterns, perfect performance doesn't indicate production readiness
- **Intended Purpose**: Evaluation protocol validation, not production performance assessment

## Research Interpretation

### Conclusion

This experiment successfully validates:
- The GNN pipeline works end-to-end ✅
- The evaluation protocol enables meaningful assessment ✅
- The model can learn from imbalanced data ✅
- The model can detect fraud when patterns are clear ✅

However, **perfect results on synthetic data with obvious patterns should be interpreted as proof of concept, not production readiness**. Real-world deployment requires testing on actual marketplace data with realistic fraud patterns.

### Next Steps for Production Readiness

1. **Real Data Testing**: Test on actual BrokeBuy marketplace data
2. **Baseline Comparison**: Compare GNN vs baseline ML models
3. **Ablation Studies**: Measure value of graph structure vs flat features
4. **Adversarial Testing**: Test against adaptive fraudsters
5. **Scale Testing**: Evaluate on larger datasets (1000+ users)
6. **Graph Complexity**: Add listings, devices, transactions
7. **Temporal Analysis**: Test on evolving graphs over time

## Reproducibility

- Random seed: 42
- Deterministic split (not random)
- Fixed hyperparameters
- Same code version

---

**Experiment Date**: 2025-12-20 03:12:38
**Status**: Complete
**Interpretation**: Pipeline validation successful, production readiness requires real data testing
