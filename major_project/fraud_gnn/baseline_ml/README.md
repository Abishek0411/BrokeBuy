# 🔬 Baseline ML Models for Fraud Detection

## Purpose

This module implements traditional machine learning models (Logistic Regression, Random Forest, Gradient Boosting) as **baselines** before implementing graph neural networks.

### Why Baselines?

1. **Establish Baseline Performance**: What can traditional ML achieve without graph structure?
2. **Fair Comparison**: Graph models should outperform these baselines to justify the added complexity
3. **Control Experiment**: Isolates the value of graph structure vs. feature engineering
4. **Industry Standard**: Most production fraud detection systems use these models

### Key Constraint

**NO GRAPH FEATURES**: These models use ONLY flat features (individual user attributes). This is intentional to measure what traditional ML can achieve without graph awareness.

## Experimental Setup

### Models Implemented

1. **Logistic Regression**
   - Simple, interpretable, fast
   - Linear decision boundary
   - Good baseline for simple patterns

2. **Random Forest**
   - Non-linear, robust
   - Handles feature interactions
   - Often good performance

3. **Gradient Boosting**
   - Strong performance
   - Complex non-linear patterns
   - Often best traditional ML model

### Features Used

All models use the same flat features (no graph structure):

- `account_age_days`: Age of account
- `messages_sent_per_hour`: Message activity rate
- `listings_posted_per_hour`: Listing creation rate
- `unique_devices_used`: Number of devices
- `reports_received`: User reports count
- `avg_message_similarity`: Text similarity in messages
- `avg_listing_similarity`: Text similarity in listings
- Additional: `listings_count`, `messages_sent`, `transactions_count`, `verification_status`, `avg_listing_price`

### Training Pipeline

1. **Data Preparation**
   - Feature vector construction
   - Train/test split (80/20, stratified)
   - Feature scaling (StandardScaler)

2. **Class Imbalance Handling**
   - Class weights computed automatically
   - Balanced weighting to handle fraud class imbalance
   - Prevents model from always predicting majority class

3. **Model Training**
   - All three models trained on same data
   - Same class weights applied
   - Same random seed for reproducibility

4. **Evaluation**
   - Precision, Recall, F1-score
   - ROC-AUC
   - Confusion matrix
   - Per-class metrics

## Usage Example

```python
from fraud_gnn.baseline_ml import (
    build_feature_matrix,
    convert_feature_dicts_to_matrix,
    complete_training_pipeline,
    compare_models
)

# Build feature vectors
feature_matrix, user_ids = build_feature_matrix(
    users=users_data,
    user_listings=user_listings_dict,
    user_messages=user_messages_dict,
    user_devices=user_devices_dict
)

# Convert to numpy matrix
feature_names = list(feature_matrix[0].keys())
X = convert_feature_dicts_to_matrix(feature_matrix, feature_names)
y = np.array([labels[uid] for uid in user_ids])

# Train all models
results = complete_training_pipeline(
    X=X,
    y=y,
    feature_names=feature_names,
    test_size=0.2,
    use_scaling=True,
    class_weight_method='balanced',
    random_state=42,
    output_dir='models/baseline_ml'
)

# Evaluate models
model_results = compare_models(
    models=results['models'],
    X_test=results['X_test'],
    y_test=results['y_test']
)
```

## Expected Limitations

### 1. Cannot Detect Network Patterns

**Problem**: These models only see individual user features, not connections.

**Examples**:
- Cannot detect Sybil attacks (multiple accounts sharing device)
- Cannot detect collusion networks (coordinated fraud)
- Cannot use "guilt by association" (connected to fraudsters)

**Impact**: Will miss fraud that requires graph structure to detect.

### 2. Limited to Flat Features

**Problem**: Only uses individual user attributes, not relational patterns.

**Examples**:
- Cannot see that User A and User B share a device
- Cannot see circular transaction patterns
- Cannot see message network structure

**Impact**: May underperform on complex fraud patterns.

### 3. Feature Engineering Required

**Problem**: Requires manual feature engineering (what features to include?).

**Examples**:
- Must manually define "messages_per_hour"
- Must manually compute text similarity
- Must manually identify suspicious patterns

**Impact**: Limited by human feature engineering ability.

### 4. Class Imbalance Challenges

**Problem**: Fraud is rare (1-10% of users), making it hard to learn.

**Solutions Applied**:
- Class weights to balance training
- Stratified train/test splits
- Focus on recall (catching fraud) over accuracy

**Impact**: May still struggle with very rare fraud patterns.

### 5. No Temporal Dynamics

**Problem**: Models see static features, not temporal evolution.

**Examples**:
- Cannot see that user was normal for months, then suddenly spamming
- Cannot see fraud pattern evolution over time
- Cannot adapt to new fraud patterns

**Impact**: May miss temporal fraud patterns.

## Expected Performance

Based on typical fraud detection benchmarks:

- **Logistic Regression**: ~70-75% precision, ~60-70% recall
- **Random Forest**: ~75-80% precision, ~70-75% recall
- **Gradient Boosting**: ~80-85% precision, ~75-80% recall

**Note**: Actual performance depends on:
- Data quality
- Feature engineering
- Class distribution
- Fraud pattern complexity

## Why Graph Models Should Outperform

Graph neural networks should outperform these baselines because:

1. **Network Structure**: Can see connections between users (device sharing, messages, transactions)
2. **Pattern Discovery**: Can automatically discover complex fraud patterns
3. **Relational Context**: Can use "guilt by association" (connected to fraudsters)
4. **Feature Learning**: Can learn graph-based features automatically

**Expected Improvement**:
- +5-10% precision
- +10-15% recall
- Better at detecting network-based fraud (Sybil, collusion)

## Evaluation Metrics

### Why Recall is Critical

**Recall** = True Positives / (True Positives + False Negatives)

In fraud detection:
- **False Negatives (Missed Fraud)**: Very costly!
- **False Positives (Legitimate User Flagged)**: Less costly

Therefore, we prioritize **high recall** (catching fraud) even if it means some false positives.

### Tradeoff: Precision vs Recall

- **High Recall, Low Precision**: Catch most fraud, but flag many false positives
  - Use case: Initial screening, manual review queue
  
- **Low Recall, High Precision**: Catch few fraud, but very accurate
  - Use case: Final blocking decisions (after verification)
  
- **Balanced**: Moderate recall and precision
  - Use case: General fraud detection

## Reproducibility

### Requirements

- Same random seed (42)
- Same train/test split (stratified)
- Same feature scaling
- Same class weights

### Reproducing Results

1. Use same code version
2. Use same random seed
3. Use same data
4. Use same hyperparameters

## Files

- `feature_vector.py`: Feature construction (flat features only)
- `models.py`: Model definitions (Logistic Regression, Random Forest, Gradient Boosting)
- `train.py`: Training pipeline (split, scaling, class weights, training)
- `evaluate.py`: Evaluation metrics (precision, recall, F1, ROC-AUC, confusion matrix)
- `README.md`: This file

## Next Steps

After establishing baseline performance:

1. **Implement Graph Models**: GNNs that use graph structure
2. **Compare Performance**: Graph models vs. baselines
3. **Analyze Improvements**: Where does graph structure help most?
4. **Feature Importance**: Which graph patterns are most predictive?

---

**Status**: Baseline Implementation Complete  
**Purpose**: Control Experiment Before GNNs  
**Constraint**: NO Graph Features

