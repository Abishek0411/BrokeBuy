"""
Graph Neural Network Model for Fraud Detection

This module implements a GNN model using PyTorch Geometric for fraud detection.
The model uses message passing to learn node representations that capture
both individual node features and network structure.

Why Message Passing Captures Coordinated Fraud
----------------------------------------------

Message passing in GNNs works by:
1. Each node aggregates information from its neighbors
2. The aggregated information is combined with the node's own features
3. This process is repeated across multiple layers

For fraud detection, this means:

1. **Sybil Detection**: If User A and User B share a device, they are connected.
   Through message passing, User A "sees" that User B is suspicious, and vice versa.
   This helps detect coordinated accounts.

2. **Collusion Networks**: Fraudsters often work in groups. Message passing
   propagates fraud signals through the network, so even if one account looks
   legitimate, its connections to fraudsters reveal it.

3. **Device Sharing Patterns**: Multiple users connected to the same device
   create a subgraph pattern. Message passing learns to recognize this pattern
   as suspicious.

4. **Transaction Patterns**: Circular transactions (A->B->C->A) create cycles
   in the graph. Message passing can detect these patterns that flat ML cannot.

5. **Guilt by Association**: Users connected to many fraudsters are more likely
   to be fraudsters themselves. Message passing naturally implements this.

Why GNNs Outperform Flat ML
----------------------------

1. **Network Structure**: GNNs can see connections between entities, while
   flat ML only sees individual features. This is crucial for detecting
   coordinated fraud (Sybil attacks, collusion networks).

2. **Automatic Feature Learning**: GNNs learn graph-based features automatically
   through message passing, while flat ML requires manual feature engineering.

3. **Relational Context**: GNNs understand that "User A shares device with User B"
   is different from "User A and User B are independent". Flat ML cannot capture this.

4. **Pattern Discovery**: GNNs can discover complex fraud patterns (e.g., circular
   transactions, device-sharing clusters) that would be difficult to engineer
   as features.

5. **Scalability**: GNNs can process large graphs efficiently, while flat ML
   would require computing pairwise features (quadratic complexity).

Expected Improvements:
- +5-10% precision over baseline ML
- +10-15% recall over baseline ML
- Better at detecting network-based fraud (Sybil, collusion)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv, GATConv, global_mean_pool
from torch_geometric.data import Data


class FraudGNN(nn.Module):
    """
    Graph Neural Network for fraud detection.
    
    Architecture:
    - Input: Node features (n_nodes, n_features)
    - GraphSAGE/GAT layers: Message passing
    - Dropout: Regularization
    - ReLU: Non-linearity
    - Output: User-level fraud probability (n_users, n_classes)
    
    The model learns node representations that capture both individual
    features and network structure through message passing.
    """
    
    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 64,
        output_dim: int = 3,  # 3 classes: normal, suspicious, fraud
        num_layers: int = 2,
        dropout: float = 0.5,
        use_gat: bool = False,
        heads: int = 1
    ):
        """
        Initialize FraudGNN model.
        
        Args:
            input_dim: Dimension of input node features
            hidden_dim: Dimension of hidden layers
            output_dim: Number of output classes (default: 3)
            num_layers: Number of GNN layers
            dropout: Dropout probability
            use_gat: Whether to use GAT (Graph Attention) instead of GraphSAGE
            heads: Number of attention heads (for GAT)
        """
        super(FraudGNN, self).__init__()
        
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        self.num_layers = num_layers
        self.dropout = dropout
        self.use_gat = use_gat
        
        # Build GNN layers
        self.convs = nn.ModuleList()
        
        if use_gat:
            # Graph Attention Network layers
            self.convs.append(
                GATConv(input_dim, hidden_dim, heads=heads, dropout=dropout)
            )
            for _ in range(num_layers - 1):
                self.convs.append(
                    GATConv(hidden_dim * heads, hidden_dim, heads=heads, dropout=dropout)
                )
            self.final_dim = hidden_dim * heads
        else:
            # GraphSAGE layers
            self.convs.append(SAGEConv(input_dim, hidden_dim))
            for _ in range(num_layers - 1):
                self.convs.append(SAGEConv(hidden_dim, hidden_dim))
            self.final_dim = hidden_dim
        
        # Output layer
        self.classifier = nn.Linear(self.final_dim, output_dim)
        
        # Dropout layer
        self.dropout_layer = nn.Dropout(dropout)
    
    def forward(self, data: Data) -> torch.Tensor:
        """
        Forward pass through the GNN.
        
        Args:
            data: PyTorch Geometric Data object with:
                - x: Node features (n_nodes, n_features)
                - edge_index: Edge indices (2, n_edges)
                - train_mask: Training mask (optional)
        
        Returns:
            Logits for each node (n_nodes, n_classes)
        """
        x, edge_index = data.x, data.edge_index
        
        # Message passing through GNN layers
        for i, conv in enumerate(self.convs):
            x = conv(x, edge_index)
            if i < len(self.convs) - 1:  # Don't apply ReLU after last layer
                x = F.relu(x)
                x = self.dropout_layer(x)
        
        # Final classification
        x = self.classifier(x)
        
        return x
    
    def predict_user_fraud(self, data: Data, user_mask: torch.Tensor = None) -> torch.Tensor:
        """
        Predict fraud probability for user nodes only.
        
        Args:
            data: PyTorch Geometric Data object
            user_mask: Optional mask for user nodes (if None, uses node_type == 0)
        
        Returns:
            Softmax probabilities for user nodes (n_users, n_classes)
        """
        logits = self.forward(data)
        
        # Filter to user nodes only
        if user_mask is None:
            # Assume user nodes are first N nodes (from data_loader)
            # Or use node_type == 0
            if hasattr(data, 'node_type'):
                user_mask = data.node_type == 0
            else:
                # Fallback: assume all nodes are users
                user_mask = torch.ones(data.num_nodes, dtype=torch.bool)
        
        user_logits = logits[user_mask]
        user_probs = F.softmax(user_logits, dim=1)
        
        return user_probs
    
    def get_node_embeddings(self, data: Data) -> torch.Tensor:
        """
        Get node embeddings (before classification layer).
        
        Useful for visualization, similarity search, or transfer learning.
        
        Args:
            data: PyTorch Geometric Data object
        
        Returns:
            Node embeddings (n_nodes, hidden_dim)
        """
        x, edge_index = data.x, data.edge_index
        
        # Message passing (without final classification)
        for i, conv in enumerate(self.convs):
            x = conv(x, edge_index)
            if i < len(self.convs) - 1:
                x = F.relu(x)
                x = self.dropout_layer(x)
        
        return x


class FraudGNNWithAttention(FraudGNN):
    """
    Variant of FraudGNN using Graph Attention Network (GAT).
    
    GAT uses attention mechanisms to weight neighbor contributions, allowing
    the model to focus on more important neighbors.
    
    This can be useful when:
    - Some neighbors are more informative than others
    - We want to learn which connections matter most
    - We need interpretability (attention weights show important neighbors)
    """
    
    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 64,
        output_dim: int = 3,
        num_layers: int = 2,
        dropout: float = 0.5,
        heads: int = 4
    ):
        """
        Initialize GAT-based fraud detection model.
        
        Args:
            input_dim: Dimension of input node features
            hidden_dim: Dimension of hidden layers
            output_dim: Number of output classes
            num_layers: Number of GAT layers
            dropout: Dropout probability
            heads: Number of attention heads (multi-head attention)
        """
        super().__init__(
            input_dim=input_dim,
            hidden_dim=hidden_dim,
            output_dim=output_dim,
            num_layers=num_layers,
            dropout=dropout,
            use_gat=True,
            heads=heads
        )

