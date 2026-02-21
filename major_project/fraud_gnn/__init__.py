"""
Fraud Detection Module using Graph Neural Networks

This module implements graph-based fraud and spam detection for the BrokeBuy marketplace.
It uses heterogeneous graphs and GNNs to detect complex fraud patterns that rule-based
systems cannot capture.
"""

# Core components
from .schema import (
    UserNode,
    ListingNode,
    DeviceNode,
    MessageEdge,
    GraphSnapshot,
    NodeType,
    EdgeType
)

# Feature extraction (stubs)
from .features import (
    extract_user_features,
    extract_listing_features,
    extract_message_features,
    extract_device_features,
    normalize_features
)

# Graph construction (stubs)
from .graph_builder import (
    build_graph_from_brokebuy_data,
    add_user_to_graph,
    add_listing_to_graph,
    add_message_to_graph,
    add_transaction_to_graph,
    get_subgraph_around_node
)

__all__ = [
    # Schema
    "UserNode",
    "ListingNode",
    "DeviceNode",
    "MessageEdge",
    "GraphSnapshot",
    "NodeType",
    "EdgeType",
    # Features
    "extract_user_features",
    "extract_listing_features",
    "extract_message_features",
    "extract_device_features",
    "normalize_features",
    # Graph Builder
    "build_graph_from_brokebuy_data",
    "add_user_to_graph",
    "add_listing_to_graph",
    "add_message_to_graph",
    "add_transaction_to_graph",
    "get_subgraph_around_node",
]

