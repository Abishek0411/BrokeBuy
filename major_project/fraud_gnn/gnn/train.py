"""
Training Loop for Graph Neural Network

This module provides the training loop for the FraudGNN model, including
class-weighted loss, early stopping, and model checkpointing.

Why Overfitting is a Risk
--------------------------

GNNs are prone to overfitting because:

1. **Small Datasets**: Fraud detection datasets are often small (thousands of
   users), while GNNs have many parameters. This leads to overfitting.

2. **Graph Structure**: The graph structure provides rich information, but
   if the training graph is small, the model might memorize specific patterns
   rather than learning generalizable fraud patterns.

3. **Class Imbalance**: Fraud is rare, so the model might overfit to the
   few fraud examples it sees, learning spurious patterns.

4. **Message Passing Depth**: Deep GNNs (many layers) can overfit by
   creating overly complex representations that don't generalize.

Signs of Overfitting:
- Training accuracy >> Validation accuracy
- Validation loss increases while training loss decreases
- Model performs well on training data but poorly on test data

Solutions:
- Early stopping (stop when validation loss stops improving)
- Dropout (randomly zero features during training)
- Weight decay (L2 regularization)
- Shallow networks (fewer layers)

Why Early Stopping is Used
---------------------------

Early stopping prevents overfitting by:

1. **Monitoring Validation Loss**: We track validation loss during training.
   When it stops improving (or starts increasing), we stop training.

2. **Best Model Checkpoint**: We save the model with the best validation
   performance, not the final model. This ensures we use the model that
   generalizes best.

3. **Automatic Stopping**: Instead of training for a fixed number of epochs,
   we stop when the model stops improving. This saves computation and
   prevents overfitting.

4. **Patience Parameter**: We wait for N epochs without improvement before
   stopping. This prevents stopping too early due to noise in validation loss.

Benefits:
- Prevents overfitting
- Saves training time
- Automatically finds optimal stopping point
- No need to manually tune number of epochs
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch_geometric.data import Data
import os
from typing import Dict, Optional, Tuple
import numpy as np

from .model import FraudGNN


def compute_class_weights(labels: torch.Tensor) -> torch.Tensor:
    """
    Compute class weights for imbalanced data.
    
    Args:
        labels: Tensor of labels (n_nodes,)
        
    Returns:
        Class weights tensor (n_classes,)
    """
    # Count occurrences of each class
    unique_labels, counts = torch.unique(labels[labels >= 0], return_counts=True)
    n_classes = len(unique_labels)
    total = counts.sum().float()
    
    # Compute weights: inverse frequency
    weights = torch.zeros(n_classes)
    for i, label in enumerate(unique_labels):
        weights[label] = total / (n_classes * counts[i].float())
    
    return weights


def train_epoch(
    model: FraudGNN,
    data: Data,
    optimizer: optim.Optimizer,
    criterion: nn.Module,
    device: torch.device
) -> Tuple[float, float]:
    """
    Train for one epoch.
    
    Args:
        model: FraudGNN model
        data: PyTorch Geometric Data object
        optimizer: Optimizer
        criterion: Loss function
        device: Device (CPU or GPU)
        
    Returns:
        Tuple of (train_loss, train_accuracy)
    """
    model.train()
    optimizer.zero_grad()
    
    # Forward pass
    out = model(data)
    
    # Compute loss only on labeled training nodes
    train_mask = data.train_mask
    train_labels = data.y[train_mask]
    train_out = out[train_mask]
    
    loss = criterion(train_out, train_labels)
    
    # Backward pass
    loss.backward()
    optimizer.step()
    
    # Compute accuracy
    pred = train_out.argmax(dim=1)
    correct = (pred == train_labels).sum().item()
    accuracy = correct / train_labels.size(0) if train_labels.size(0) > 0 else 0.0
    
    return loss.item(), accuracy


def validate(
    model: FraudGNN,
    data: Data,
    criterion: nn.Module,
    device: torch.device
) -> Tuple[float, float]:
    """
    Validate the model.
    
    Args:
        model: FraudGNN model
        data: PyTorch Geometric Data object
        criterion: Loss function
        device: Device (CPU or GPU)
        
    Returns:
        Tuple of (val_loss, val_accuracy)
    """
    model.eval()
    
    with torch.no_grad():
        out = model(data)
        
        # Compute loss only on labeled validation nodes
        val_mask = data.val_mask
        val_labels = data.y[val_mask]
        val_out = out[val_mask]
        
        loss = criterion(val_out, val_labels)
        
        # Compute accuracy
        pred = val_out.argmax(dim=1)
        correct = (pred == val_labels).sum().item()
        accuracy = correct / val_labels.size(0) if val_labels.size(0) > 0 else 0.0
    
    return loss.item(), accuracy


def train_model(
    model: FraudGNN,
    data: Data,
    epochs: int = 100,
    lr: float = 0.01,
    weight_decay: float = 5e-4,
    patience: int = 10,
    device: torch.device = None,
    checkpoint_dir: Optional[str] = None
) -> Dict:
    """
    Complete training loop with early stopping.
    
    Args:
        model: FraudGNN model
        data: PyTorch Geometric Data object
        epochs: Maximum number of epochs
        lr: Learning rate
        weight_decay: L2 regularization weight
        patience: Early stopping patience (epochs without improvement)
        device: Device (CPU or GPU)
        checkpoint_dir: Directory to save checkpoints
        
    Returns:
        Dictionary with training history and best model state
    """
    if device is None:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    model = model.to(device)
    data = data.to(device)
    
    # Compute class weights
    class_weights = compute_class_weights(data.y)
    class_weights = class_weights.to(device)
    
    # Loss function with class weights
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    
    # Optimizer
    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
    
    # Training history
    history = {
        'train_loss': [],
        'train_acc': [],
        'val_loss': [],
        'val_acc': []
    }
    
    # Early stopping
    best_val_loss = float('inf')
    patience_counter = 0
    best_model_state = None
    
    # Create checkpoint directory
    if checkpoint_dir:
        os.makedirs(checkpoint_dir, exist_ok=True)
    
    print("Starting training...")
    print(f"Device: {device}")
    print(f"Epochs: {epochs}")
    print(f"Patience: {patience}")
    print(f"Class weights: {class_weights}")
    
    for epoch in range(epochs):
        # Train
        train_loss, train_acc = train_epoch(model, data, optimizer, criterion, device)
        
        # Validate
        val_loss, val_acc = validate(model, data, criterion, device)
        
        # Record history
        history['train_loss'].append(train_loss)
        history['train_acc'].append(train_acc)
        history['val_loss'].append(val_loss)
        history['val_acc'].append(val_acc)
        
        # Print progress
        if (epoch + 1) % 10 == 0 or epoch == 0:
            print(f"Epoch {epoch+1:3d} | Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.4f} | "
                  f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.4f}")
        
        # Early stopping check
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            best_model_state = model.state_dict().copy()
            
            # Save checkpoint
            if checkpoint_dir:
                checkpoint_path = os.path.join(checkpoint_dir, 'best_model.pt')
                torch.save({
                    'epoch': epoch,
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'val_loss': val_loss,
                    'val_acc': val_acc,
                }, checkpoint_path)
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"\nEarly stopping at epoch {epoch+1}")
                print(f"Best validation loss: {best_val_loss:.4f}")
                break
    
    # Load best model
    if best_model_state is not None:
        model.load_state_dict(best_model_state)
        print("Loaded best model state")
    
    return {
        'model': model,
        'history': history,
        'best_val_loss': best_val_loss,
        'epochs_trained': epoch + 1
    }


def load_checkpoint(
    model: FraudGNN,
    checkpoint_path: str,
    device: torch.device = None
) -> FraudGNN:
    """
    Load a trained model from checkpoint.
    
    Args:
        model: FraudGNN model (architecture)
        checkpoint_path: Path to checkpoint file
        device: Device (CPU or GPU)
        
    Returns:
        Model with loaded weights
    """
    if device is None:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model = model.to(device)
    
    print(f"Loaded checkpoint from epoch {checkpoint['epoch']}")
    print(f"Validation loss: {checkpoint['val_loss']:.4f}")
    print(f"Validation accuracy: {checkpoint['val_acc']:.4f}")
    
    return model

