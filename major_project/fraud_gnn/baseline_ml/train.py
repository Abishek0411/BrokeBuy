"""
Training Pipeline for Baseline ML Models

This module provides a complete training pipeline for baseline ML models,
including train/test splitting, class imbalance handling, model training,
and model persistence.

Why Class Imbalance Matters in Fraud Detection
----------------------------------------------

Fraud detection is inherently imbalanced:
- Most users are legitimate (normal class: 90-99%)
- Few users are fraudulent (fraud class: 1-10%)

This imbalance causes problems:
1. **Accuracy is Misleading**: A model that predicts "normal" for everyone
   achieves 99% accuracy but catches 0% of fraud. This is useless!

2. **Model Bias**: Models learn to always predict the majority class
   because it minimizes loss on imbalanced data.

3. **False Negatives are Costly**: Missing fraud (false negative) is much
   worse than flagging a legitimate user (false positive). We need to
   catch fraud even if it means some false positives.

Solutions:
- **Class Weights**: Weight fraud class higher during training
- **Resampling**: Oversample fraud cases or undersample normal cases
- **Evaluation Metrics**: Use precision, recall, F1 instead of accuracy
- **Threshold Tuning**: Adjust decision threshold to favor recall

Why Accuracy Alone is Misleading
---------------------------------

Example: 1000 users, 990 normal, 10 fraud

Model A: Always predicts "normal"
- Accuracy: 99% (990/1000 correct)
- Recall: 0% (0/10 fraud caught)
- **Useless!**

Model B: Catches 8/10 fraud, flags 20 false positives
- Accuracy: 97.8% (978/1000 correct)
- Recall: 80% (8/10 fraud caught)
- **Much better!**

Accuracy doesn't tell the whole story. We need metrics that focus on
the minority class (fraud).
"""

import pickle
from typing import Dict, List, Tuple, Optional
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from .models import (
    LogisticRegressionModel,
    RandomForestModel,
    GradientBoostingModel
)


def prepare_train_test_split(
    X: np.ndarray,
    y: np.ndarray,
    test_size: float = 0.2,
    random_state: int = 42,
    stratify: bool = True
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Split data into training and testing sets.
    
    Uses stratification to ensure class distribution is maintained in
    both train and test sets (important for imbalanced data).
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Labels (n_samples,)
        test_size: Proportion of data for testing (default: 0.2)
        random_state: Random seed for reproducibility
        stratify: Whether to stratify by class labels
        
    Returns:
        Tuple of (X_train, X_test, y_train, y_test)
    """
    stratify_param = y if stratify else None
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state,
        stratify=stratify_param
    )
    
    return X_train, X_test, y_train, y_test


def compute_class_weights(y: np.ndarray, method: str = 'balanced') -> Dict[int, float]:
    """
    Compute class weights for handling class imbalance.
    
    Methods:
    - 'balanced': Automatically balance classes (sklearn default)
    - 'inverse': Weight inversely proportional to class frequency
    - 'custom': Custom weights (can be specified)
    
    Why Class Weights?
    ------------------
    
    Instead of resampling data, we can weight the loss function so that
    misclassifying a fraud case is penalized more than misclassifying
    a normal case. This makes the model focus on learning fraud patterns.
    
    Args:
        y: Labels (n_samples,)
        method: Method for computing weights ('balanced', 'inverse', or 'custom')
        
    Returns:
        Dictionary mapping class label -> weight
    """
    from collections import Counter
    
    class_counts = Counter(y)
    n_classes = len(class_counts)
    total_samples = len(y)
    
    if method == 'balanced':
        # sklearn's balanced: n_samples / (n_classes * class_count)
        weights = {}
        for class_label, count in class_counts.items():
            weights[class_label] = total_samples / (n_classes * count)
        return weights
    
    elif method == 'inverse':
        # Inverse frequency: total_samples / (n_classes * class_count)
        # Same as balanced, but explicit
        weights = {}
        for class_label, count in class_counts.items():
            weights[class_label] = total_samples / (n_classes * count)
        return weights
    
    else:
        # Equal weights (no balancing)
        return {label: 1.0 for label in class_counts.keys()}


def train_model(
    model,
    X_train: np.ndarray,
    y_train: np.ndarray,
    class_weights: Optional[Dict[int, float]] = None
) -> None:
    """
    Train a model with optional class weights.
    
    Args:
        model: Model instance (LogisticRegressionModel, RandomForestModel, etc.)
        X_train: Training features (n_samples, n_features)
        y_train: Training labels (n_samples,)
        class_weights: Optional dictionary of class weights
    """
    # Set class weights if model supports it
    if class_weights is not None:
        if hasattr(model, 'model'):
            # For sklearn models wrapped in our classes
            if hasattr(model.model, 'set_params'):
                try:
                    model.model.set_params(class_weight=class_weights)
                except:
                    # Some models don't support class_weight
                    pass
            # For GradientBoosting, we handle it in the train method
            if isinstance(model, GradientBoostingModel):
                model.class_weight = class_weights
    
    # Train the model
    model.train(X_train, y_train)


def train_all_models(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    class_weights: Optional[Dict[int, float]] = None,
    random_state: int = 42
) -> Dict[str, any]:
    """
    Train all baseline models and return trained models.
    
    Args:
        X_train: Training features
        y_train: Training labels
        X_test: Test features (for validation during training)
        y_test: Test labels (for validation during training)
        class_weights: Optional class weights
        random_state: Random seed
        
    Returns:
        Dictionary mapping model names to trained model instances
    """
    models = {}
    
    # Train Logistic Regression
    print("Training Logistic Regression...")
    lr_model = LogisticRegressionModel(class_weight=class_weights, random_state=random_state)
    train_model(lr_model, X_train, y_train, class_weights)
    models['logistic_regression'] = lr_model
    
    # Train Random Forest
    print("Training Random Forest...")
    rf_model = RandomForestModel(class_weight=class_weights, random_state=random_state)
    train_model(rf_model, X_train, y_train, class_weights)
    models['random_forest'] = rf_model
    
    # Train Gradient Boosting
    print("Training Gradient Boosting...")
    gb_model = GradientBoostingModel(class_weight=class_weights, random_state=random_state)
    train_model(gb_model, X_train, y_train, class_weights)
    models['gradient_boosting'] = gb_model
    
    return models


def scale_features(
    X_train: np.ndarray,
    X_test: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, StandardScaler]:
    """
    Scale features using StandardScaler (zero mean, unit variance).
    
    Why Scale Features?
    --------------------
    
    Some models (especially Logistic Regression) are sensitive to feature scales.
    Scaling ensures all features contribute equally to the model.
    
    Important: Fit scaler on training data only, then transform both
    train and test. Never fit on test data (data leakage!).
    
    Args:
        X_train: Training features
        X_test: Test features
        
    Returns:
        Tuple of (X_train_scaled, X_test_scaled, scaler)
    """
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    return X_train_scaled, X_test_scaled, scaler


def save_model(model, filepath: str) -> None:
    """
    Save a trained model to disk using pickle.
    
    Args:
        model: Trained model instance
        filepath: Path to save the model
    """
    with open(filepath, 'wb') as f:
        pickle.dump(model, f)
    print(f"Model saved to {filepath}")


def load_model(filepath: str):
    """
    Load a trained model from disk.
    
    Args:
        filepath: Path to the saved model
        
    Returns:
        Loaded model instance
    """
    with open(filepath, 'rb') as f:
        model = pickle.load(f)
    print(f"Model loaded from {filepath}")
    return model


def save_all_models(models: Dict[str, any], output_dir: str) -> None:
    """
    Save all trained models to disk.
    
    Args:
        models: Dictionary mapping model names to model instances
        output_dir: Directory to save models in
    """
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    for name, model in models.items():
        filepath = os.path.join(output_dir, f"{name}.pkl")
        save_model(model, filepath)


def complete_training_pipeline(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: List[str],
    test_size: float = 0.2,
    use_scaling: bool = True,
    class_weight_method: str = 'balanced',
    random_state: int = 42,
    output_dir: Optional[str] = None
) -> Dict[str, any]:
    """
    Complete training pipeline from data to saved models.
    
    This function orchestrates the entire training process:
    1. Train/test split
    2. Feature scaling (optional)
    3. Class weight computation
    4. Model training
    5. Model persistence (optional)
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Labels (n_samples,)
        feature_names: List of feature names
        test_size: Proportion for test set
        use_scaling: Whether to scale features
        class_weight_method: Method for computing class weights
        random_state: Random seed
        output_dir: Optional directory to save models
        
    Returns:
        Dictionary containing:
        - 'models': Trained models
        - 'X_train', 'X_test', 'y_train', 'y_test': Data splits
        - 'scaler': Feature scaler (if used)
        - 'class_weights': Class weights used
    """
    # Step 1: Train/test split
    print("Splitting data into train/test sets...")
    X_train, X_test, y_train, y_test = prepare_train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    
    # Step 2: Feature scaling
    scaler = None
    if use_scaling:
        print("Scaling features...")
        X_train, X_test, scaler = scale_features(X_train, X_test)
    
    # Step 3: Compute class weights
    print("Computing class weights...")
    class_weights = compute_class_weights(y_train, method=class_weight_method)
    print(f"Class weights: {class_weights}")
    
    # Step 4: Train models
    print("Training models...")
    models = train_all_models(
        X_train, y_train, X_test, y_test,
        class_weights=class_weights,
        random_state=random_state
    )
    
    # Set feature names for all models
    for model in models.values():
        model.feature_names = feature_names
    
    # Step 5: Save models (optional)
    if output_dir:
        print(f"Saving models to {output_dir}...")
        save_all_models(models, output_dir)
    
    return {
        'models': models,
        'X_train': X_train,
        'X_test': X_test,
        'y_train': y_train,
        'y_test': y_test,
        'scaler': scaler,
        'class_weights': class_weights
    }

