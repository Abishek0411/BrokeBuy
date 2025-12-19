"""
Graph Data Loader for PyTorch Geometric

This module converts GraphSnapshot objects into PyTorch Geometric Data objects
that can be used for training graph neural networks.

How Heterogeneous Data is Simplified for Training
--------------------------------------------------

Our graph is heterogeneous (multiple node types: users, listings, devices).
However, PyTorch Geometric's basic Data class expects homogeneous graphs
(single node type). We simplify by:

1. **Node Type Mapping**: Map all node types to a single node index space
   - Users: indices 0 to N_users-1
   - Listings: indices N_users to N_users+N_listings-1
   - Devices: indices N_users+N_listings to N_users+N_listings+N_devices-1

2. **Edge Type Preservation**: Different edge types are combined into a single
   edge index, but we can track edge types if needed for heterogeneous GNNs.

3. **Feature Alignment**: All node types use the same feature dimension
   (padding/zero-padding if needed).

4. **Target Nodes**: Only user nodes have labels (fraud detection target).
   Listing and device nodes don't have labels (they're auxiliary nodes).

Why Users are the Primary Prediction Target
--------------------------------------------

1. **Business Goal**: We want to detect fraudulent users, not fraudulent
   listings or devices. A listing might be spam, but the real problem is
   the user who created it.

2. **Label Availability**: We have labels (normal/suspicious/fraud) for users
   from the labeling strategy. We don't have labels for listings or devices.

3. **Actionability**: We can take action on users (ban, verify, rate limit).
   Actions on listings or devices are secondary.

4. **Network Effects**: By predicting user fraud, we indirectly catch
   fraudulent listings and devices through the graph structure.

5. **Evaluation**: User-level predictions are easier to evaluate and interpret.
"""

from typing import Dict, List, Tuple, Optional
import numpy as np
import torch
from torch_geometric.data import Data

from ..schema import GraphSnapshot, UserNode, ListingNode, DeviceNode


def load_graph_snapshot(
    snapshot: GraphSnapshot,
    labels: Dict[str, int],
    feature_extractor=None
) -> Data:
    """
    Convert GraphSnapshot to PyTorch Geometric Data object.
    
    This function:
    1. Extracts node features for all node types
    2. Creates edge indices for all edge types
    3. Maps user IDs to node indices
    4. Creates labels tensor (only for user nodes)
    5. Creates train/val/test masks
    
    Args:
        snapshot: GraphSnapshot object
        labels: Dictionary mapping user_id -> label (0, 1, or 2)
        feature_extractor: Optional function to extract features from nodes
                          If None, uses default feature extraction
        
    Returns:
        PyTorch Geometric Data object with:
        - x: Node features (n_nodes, n_features)
        - edge_index: Edge indices (2, n_edges)
        - y: Node labels (n_nodes,) - only user nodes have labels, others are -1
        - train_mask: Boolean mask for training nodes
        - val_mask: Boolean mask for validation nodes
        - test_mask: Boolean mask for test nodes
        - node_type: Node type indicator (0=user, 1=listing, 2=device)
    """
    # Step 1: Create node ID to index mapping
    user_ids = list(snapshot.user_nodes.keys())
    listing_ids = list(snapshot.listing_nodes.keys())
    device_ids = list(snapshot.device_nodes.keys())
    
    # Create mappings: node_id -> node_index
    user_id_to_idx = {uid: idx for idx, uid in enumerate(user_ids)}
    listing_id_to_idx = {
        lid: idx + len(user_ids)
        for idx, lid in enumerate(listing_ids)
    }
    device_id_to_idx = {
        did: idx + len(user_ids) + len(listing_ids)
        for idx, did in enumerate(device_ids)
    }
    
    total_nodes = len(user_ids) + len(listing_ids) + len(device_ids)
    
    # Step 2: Extract node features
    if feature_extractor is None:
        feature_extractor = _default_feature_extractor
    
    # Extract features for each node type
    user_features = [
        feature_extractor(snapshot.user_nodes[uid], snapshot, 'user')
        for uid in user_ids
    ]
    listing_features = [
        feature_extractor(snapshot.listing_nodes[lid], snapshot, 'listing')
        for lid in listing_ids
    ]
    device_features = [
        feature_extractor(snapshot.device_nodes[did], snapshot, 'device')
        for did in device_ids
    ]
    
    # Combine all features
    all_features = user_features + listing_features + device_features
    
    # Convert to tensor and pad to same dimension if needed
    feature_dim = max(len(f) for f in all_features) if all_features else 0
    if feature_dim == 0:
        # Default feature dimension if no features
        feature_dim = 10
        all_features = [[0.0] * feature_dim] * total_nodes
    
    # Pad features to same dimension
    padded_features = []
    for feat in all_features:
        if len(feat) < feature_dim:
            feat = feat + [0.0] * (feature_dim - len(feat))
        padded_features.append(feat[:feature_dim])
    
    x = torch.tensor(padded_features, dtype=torch.float)
    
    # Step 3: Create edge indices
    edge_list = []
    
    # Message edges: user -> user
    for edge in snapshot.message_edges:
        from_idx = user_id_to_idx.get(edge.from_user_id)
        to_idx = user_id_to_idx.get(edge.to_user_id)
        if from_idx is not None and to_idx is not None:
            edge_list.append([from_idx, to_idx])
    
    # Creates edges: user -> listing
    for user_id, listing_id in snapshot.creates_edges:
        user_idx = user_id_to_idx.get(user_id)
        listing_idx = listing_id_to_idx.get(listing_id)
        if user_idx is not None and listing_idx is not None:
            edge_list.append([user_idx, listing_idx])
    
    # Transaction edges: user -> listing
    for user_id, listing_id in snapshot.transaction_edges:
        user_idx = user_id_to_idx.get(user_id)
        listing_idx = listing_id_to_idx.get(listing_id)
        if user_idx is not None and listing_idx is not None:
            edge_list.append([user_idx, listing_idx])
    
    # Device edges: user -> device
    for user_id, device_id in snapshot.device_edges:
        user_idx = user_id_to_idx.get(user_id)
        device_idx = device_id_to_idx.get(device_id)
        if user_idx is not None and device_idx is not None:
            edge_list.append([user_idx, device_idx])
    
    # View edges: user -> listing (optional, might be too many)
    for user_id, listing_id in snapshot.view_edges[:10000]:  # Limit views
        user_idx = user_id_to_idx.get(user_id)
        listing_idx = listing_id_to_idx.get(listing_id)
        if user_idx is not None and listing_idx is not None:
            edge_list.append([user_idx, listing_idx])
    
    # Convert to edge_index format (2, n_edges)
    if edge_list:
        edge_index = torch.tensor(edge_list, dtype=torch.long).t().contiguous()
    else:
        edge_index = torch.empty((2, 0), dtype=torch.long)
    
    # Step 4: Create labels (only for user nodes)
    y = torch.full((total_nodes,), -1, dtype=torch.long)
    for uid, label in labels.items():
        if uid in user_id_to_idx:
            idx = user_id_to_idx[uid]
            y[idx] = label
    
    # Step 5: Create train/val/test masks (only for user nodes with labels)
    labeled_user_indices = [idx for idx, label in enumerate(y[:len(user_ids)]) if label >= 0]
    
    if len(labeled_user_indices) > 0:
        # Split labeled users into train/val/test
        np.random.seed(42)
        np.random.shuffle(labeled_user_indices)
        
        n_train = int(0.7 * len(labeled_user_indices))
        n_val = int(0.15 * len(labeled_user_indices))
        
        train_indices = labeled_user_indices[:n_train]
        val_indices = labeled_user_indices[n_train:n_train + n_val]
        test_indices = labeled_user_indices[n_train + n_val:]
        
        train_mask = torch.zeros(total_nodes, dtype=torch.bool)
        val_mask = torch.zeros(total_nodes, dtype=torch.bool)
        test_mask = torch.zeros(total_nodes, dtype=torch.bool)
        
        train_mask[train_indices] = True
        val_mask[val_indices] = True
        test_mask[test_indices] = True
    else:
        # No labels available
        train_mask = torch.zeros(total_nodes, dtype=torch.bool)
        val_mask = torch.zeros(total_nodes, dtype=torch.bool)
        test_mask = torch.zeros(total_nodes, dtype=torch.bool)
    
    # Step 6: Create node type indicator
    node_type = torch.zeros(total_nodes, dtype=torch.long)
    node_type[len(user_ids):len(user_ids) + len(listing_ids)] = 1  # Listings
    node_type[len(user_ids) + len(listing_ids):] = 2  # Devices
    
    # Create PyTorch Geometric Data object
    data = Data(
        x=x,
        edge_index=edge_index,
        y=y,
        train_mask=train_mask,
        val_mask=val_mask,
        test_mask=test_mask,
        node_type=node_type,
        num_nodes=total_nodes
    )
    
    return data


def _default_feature_extractor(node, snapshot: GraphSnapshot, node_type: str) -> List[float]:
    """
    Default feature extractor for nodes.
    
    Extracts simple features from nodes. In practice, this should use
    the feature extraction functions from features.py.
    
    Args:
        node: Node object (UserNode, ListingNode, or DeviceNode)
        snapshot: GraphSnapshot for context
        node_type: Type of node ('user', 'listing', 'device')
        
    Returns:
        List of feature values
    """
    features = []
    
    if node_type == 'user' and isinstance(node, UserNode):
        features = [
            float(node.account_age_days),
            float(node.listings_count),
            float(node.transactions_count),
            float(node.messages_sent),
            float(node.messages_received),
            float(node.avg_listing_price),
            1.0 if node.verification_status else 0.0
        ]
    elif node_type == 'listing' and isinstance(node, ListingNode):
        features = [
            float(node.price),
            float(node.views_count),
            float(node.messages_count),
            float(node.days_active),
            1.0 if node.is_sold else 0.0
        ]
    elif node_type == 'device' and isinstance(node, DeviceNode):
        features = [
            float(node.user_count),
            float((node.last_seen - node.first_seen).days) if node.last_seen and node.first_seen else 0.0
        ]
    
    # Pad to minimum dimension
    if len(features) < 10:
        features = features + [0.0] * (10 - len(features))
    
    return features[:10]


def create_data_loader(data: Data, batch_size: Optional[int] = None):
    """
    Create a data loader for batching (if needed).
    
    For small graphs, we typically use the full graph. For large graphs,
    we might need batching or subgraph sampling.
    
    Args:
        data: PyTorch Geometric Data object
        batch_size: Optional batch size (None = use full graph)
        
    Returns:
        Data loader or data object
    """
    # For now, return data as-is (full graph training)
    # In future, can implement batching or subgraph sampling
    return data

