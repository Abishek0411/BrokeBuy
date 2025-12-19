"""
Baseline ML Models for Fraud Detection

This module defines traditional machine learning models (Logistic Regression,
Random Forest, Gradient Boosting) that serve as baselines before implementing
graph neural networks.

These models use ONLY flat features (no graph structure) to establish what
traditional ML can achieve without graph awareness.

Why These Models?
-----------------

1. **Logistic Regression**: Simple, interpretable, fast baseline
   - Good for understanding feature importance
   - Fast training and inference
   - Linear decision boundary (may miss complex patterns)

2. **Random Forest**: Non-linear, robust, handles feature interactions
   - Can capture non-linear patterns
   - Handles feature interactions automatically
   - Less interpretable than logistic regression

3. **Gradient Boosting**: Strong performance, handles complex patterns
   - Often best-performing traditional ML model
   - Can capture complex non-linear patterns
   - More prone to overfitting

These three models provide a range of complexity and performance, allowing
us to see how much graph structure adds beyond the best traditional ML.
"""

from typing import List, Dict, Optional
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier


class LogisticRegressionModel:
    """
    Logistic Regression model for fraud detection.
    
    This is the simplest baseline model. It learns a linear decision boundary
    in the feature space, making it fast and interpretable.
    
    Advantages:
    - Fast training and inference
    - Interpretable (can see feature coefficients)
    - Good baseline for simple patterns
    
    Limitations:
    - Linear decision boundary (may miss complex patterns)
    - Cannot capture feature interactions well
    - May underperform on non-linear fraud patterns
    """
    
    def __init__(self, class_weight: Optional[Dict] = None, random_state: int = 42):
        """
        Initialize Logistic Regression model.
        
        Args:
            class_weight: Optional dictionary for class weights to handle imbalance
            random_state: Random seed for reproducibility
        """
        self.model = LogisticRegression(
            class_weight=class_weight,
            random_state=random_state,
            max_iter=1000,
            solver='lbfgs'  # Good for small to medium datasets
        )
        self.feature_names = None
    
    def train(self, X: np.ndarray, y: np.ndarray) -> None:
        """
        Train the logistic regression model.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            y: Labels (n_samples,) - should be 0, 1, or 2
        """
        self.model.fit(X, y)
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class labels.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            
        Returns:
            Predicted labels (n_samples,)
        """
        return self.model.predict(X)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class probabilities.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            
        Returns:
            Probability matrix (n_samples, n_classes)
        """
        return self.model.predict_proba(X)
    
    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """
        Get feature importance (coefficients).
        
        For binary classification, returns coefficients for the positive class.
        For multi-class, returns average absolute coefficients.
        
        Returns:
            Dictionary mapping feature names to importance scores
        """
        if self.feature_names is None:
            return None
        
        # For multi-class, average absolute coefficients across classes
        if len(self.model.coef_.shape) > 1:
            importances = np.mean(np.abs(self.model.coef_), axis=0)
        else:
            importances = np.abs(self.model.coef_[0])
        
        return dict(zip(self.feature_names, importances))


class RandomForestModel:
    """
    Random Forest model for fraud detection.
    
    This is a more complex baseline that can capture non-linear patterns
    and feature interactions through an ensemble of decision trees.
    
    Advantages:
    - Captures non-linear patterns
    - Handles feature interactions automatically
    - Robust to outliers
    - Can provide feature importance
    
    Limitations:
    - Less interpretable than logistic regression
    - May overfit with small datasets
    - Slower than logistic regression
    """
    
    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: Optional[int] = None,
        class_weight: Optional[Dict] = None,
        random_state: int = 42
    ):
        """
        Initialize Random Forest model.
        
        Args:
            n_estimators: Number of trees in the forest
            max_depth: Maximum depth of trees (None = no limit)
            class_weight: Optional dictionary for class weights
            random_state: Random seed for reproducibility
        """
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            class_weight=class_weight,
            random_state=random_state,
            n_jobs=-1  # Use all CPU cores
        )
        self.feature_names = None
    
    def train(self, X: np.ndarray, y: np.ndarray) -> None:
        """
        Train the random forest model.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            y: Labels (n_samples,) - should be 0, 1, or 2
        """
        self.model.fit(X, y)
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class labels.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            
        Returns:
            Predicted labels (n_samples,)
        """
        return self.model.predict(X)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class probabilities.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            
        Returns:
            Probability matrix (n_samples, n_classes)
        """
        return self.model.predict_proba(X)
    
    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """
        Get feature importance from random forest.
        
        Returns:
            Dictionary mapping feature names to importance scores
        """
        if self.feature_names is None:
            return None
        
        importances = self.model.feature_importances_
        return dict(zip(self.feature_names, importances))


class GradientBoostingModel:
    """
    Gradient Boosting model for fraud detection.
    
    This is the most complex baseline model, using boosting to iteratively
    improve predictions. Often achieves the best performance among traditional ML.
    
    Advantages:
    - Often best-performing traditional ML model
    - Can capture complex non-linear patterns
    - Handles feature interactions well
    - Can provide feature importance
    
    Limitations:
    - More prone to overfitting
    - Slower training than random forest
    - Less interpretable
    - Requires careful hyperparameter tuning
    """
    
    def __init__(
        self,
        n_estimators: int = 100,
        learning_rate: float = 0.1,
        max_depth: int = 3,
        class_weight: Optional[Dict] = None,
        random_state: int = 42
    ):
        """
        Initialize Gradient Boosting model.
        
        Args:
            n_estimators: Number of boosting stages
            learning_rate: Learning rate (shrinkage)
            max_depth: Maximum depth of trees
            class_weight: Optional dictionary for class weights
            random_state: Random seed for reproducibility
        """
        self.model = GradientBoostingClassifier(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            random_state=random_state
        )
        # Note: GradientBoostingClassifier doesn't support class_weight directly
        # We'll handle class imbalance through sample_weight in training
        self.class_weight = class_weight
        self.feature_names = None
    
    def train(self, X: np.ndarray, y: np.ndarray) -> None:
        """
        Train the gradient boosting model.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            y: Labels (n_samples,) - should be 0, 1, or 2
        """
        # Handle class weights through sample weights
        sample_weight = None
        if self.class_weight:
            sample_weight = np.array([self.class_weight.get(label, 1.0) for label in y])
        
        self.model.fit(X, y, sample_weight=sample_weight)
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class labels.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            
        Returns:
            Predicted labels (n_samples,)
        """
        return self.model.predict(X)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict class probabilities.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            
        Returns:
            Probability matrix (n_samples, n_classes)
        """
        return self.model.predict_proba(X)
    
    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """
        Get feature importance from gradient boosting.
        
        Returns:
            Dictionary mapping feature names to importance scores
        """
        if self.feature_names is None:
            return None
        
        importances = self.model.feature_importances_
        return dict(zip(self.feature_names, importances))


def convert_feature_dicts_to_matrix(feature_dicts: List[Dict], feature_names: List[str]) -> np.ndarray:
    """
    Convert list of feature dictionaries to numpy matrix.
    
    Args:
        feature_dicts: List of feature dictionaries
        feature_names: List of feature names (in order)
        
    Returns:
        Feature matrix (n_samples, n_features)
    """
    matrix = []
    for feat_dict in feature_dicts:
        row = [feat_dict.get(name, 0.0) for name in feature_names]
        matrix.append(row)
    return np.array(matrix)

