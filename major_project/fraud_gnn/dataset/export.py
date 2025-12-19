"""
Dataset Export Module

This module provides functions to export graph snapshots, features, and labels
to formats suitable for machine learning experiments and reproducibility.

Why JSON/CSV Format?
---------------------

1. **Human Readable**: JSON and CSV are text-based and can be inspected
   without special tools. This aids debugging and understanding.

2. **Language Agnostic**: Can be read by Python, R, MATLAB, etc.
   This allows researchers using different tools to work with the data.

3. **Version Control Friendly**: Text formats work well with git, allowing
   dataset versions to be tracked.

4. **Reproducibility**: Exact same data can be exported and shared, ensuring
   experiments are reproducible.

5. **Standard Formats**: JSON and CSV are widely supported and don't require
   proprietary software.

Alternative Formats Considered:
- **HDF5**: Binary, efficient but less readable
- **Pickle**: Python-specific, not portable
- **Parquet**: Good for large data but requires special tools
- **GraphML**: Graph-specific but less flexible

We chose JSON/CSV for maximum accessibility and reproducibility, even if
it means larger file sizes.
"""

import json
import csv
from typing import Dict, List, Any
from pathlib import Path
from datetime import datetime

from ..schema import GraphSnapshot, UserNode, ListingNode, DeviceNode, MessageEdge


def export_node_features(
    graph_snapshot: GraphSnapshot,
    output_path: str,
    format: str = "json"
) -> None:
    """
    Export node features to a file.
    
    Exports features for all node types (users, listings, devices) in a
    format suitable for machine learning.
    
    Format:
    - JSON: Nested structure with node types as keys
    - CSV: Separate CSV files for each node type
    
    Args:
        graph_snapshot: GraphSnapshot to export
        output_path: Path to output file (or directory for CSV)
        format: Export format ("json" or "csv")
        
    Example:
        >>> export_node_features(snapshot, "features.json", format="json")
        >>> # Creates features.json with user, listing, device features
    """
    if format == "json":
        _export_node_features_json(graph_snapshot, output_path)
    elif format == "csv":
        _export_node_features_csv(graph_snapshot, output_path)
    else:
        raise ValueError(f"Unsupported format: {format}")


def _export_node_features_json(graph_snapshot: GraphSnapshot, output_path: str) -> None:
    """Export node features as JSON."""
    data = {
        'metadata': {
            'timestamp': graph_snapshot.timestamp.isoformat(),
            'node_counts': {
                'users': len(graph_snapshot.user_nodes),
                'listings': len(graph_snapshot.listing_nodes),
                'devices': len(graph_snapshot.device_nodes)
            }
        },
        'users': [
            {
                'user_id': node.user_id,
                'account_age_days': node.account_age_days,
                'listings_count': node.listings_count,
                'transactions_count': node.transactions_count,
                'messages_sent': node.messages_sent,
                'messages_received': node.messages_received,
                'avg_listing_price': node.avg_listing_price,
                'verification_status': node.verification_status,
                'created_at': node.created_at.isoformat() if node.created_at else None
            }
            for node in graph_snapshot.user_nodes.values()
        ],
        'listings': [
            {
                'listing_id': node.listing_id,
                'seller_id': node.seller_id,
                'price': node.price,
                'category': node.category,
                'condition': node.condition,
                'views_count': node.views_count,
                'messages_count': node.messages_count,
                'is_sold': node.is_sold,
                'days_active': node.days_active,
                'created_at': node.created_at.isoformat() if node.created_at else None
            }
            for node in graph_snapshot.listing_nodes.values()
        ],
        'devices': [
            {
                'device_id': node.device_id,
                'user_count': node.user_count,
                'user_ids': list(node.user_ids),
                'first_seen': node.first_seen.isoformat() if node.first_seen else None,
                'last_seen': node.last_seen.isoformat() if node.last_seen else None
            }
            for node in graph_snapshot.device_nodes.values()
        ]
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)


def _export_node_features_csv(graph_snapshot: GraphSnapshot, output_dir: str) -> None:
    """Export node features as CSV files (one per node type)."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Export users
    users_file = output_path / 'users.csv'
    with open(users_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'user_id', 'account_age_days', 'listings_count', 'transactions_count',
            'messages_sent', 'messages_received', 'avg_listing_price',
            'verification_status', 'created_at'
        ])
        writer.writeheader()
        for node in graph_snapshot.user_nodes.values():
            writer.writerow({
                'user_id': node.user_id,
                'account_age_days': node.account_age_days,
                'listings_count': node.listings_count,
                'transactions_count': node.transactions_count,
                'messages_sent': node.messages_sent,
                'messages_received': node.messages_received,
                'avg_listing_price': node.avg_listing_price,
                'verification_status': node.verification_status,
                'created_at': node.created_at.isoformat() if node.created_at else ''
            })
    
    # Export listings
    listings_file = output_path / 'listings.csv'
    with open(listings_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'listing_id', 'seller_id', 'price', 'category', 'condition',
            'views_count', 'messages_count', 'is_sold', 'days_active', 'created_at'
        ])
        writer.writeheader()
        for node in graph_snapshot.listing_nodes.values():
            writer.writerow({
                'listing_id': node.listing_id,
                'seller_id': node.seller_id,
                'price': node.price,
                'category': node.category,
                'condition': node.condition,
                'views_count': node.views_count,
                'messages_count': node.messages_count,
                'is_sold': node.is_sold,
                'days_active': node.days_active,
                'created_at': node.created_at.isoformat() if node.created_at else ''
            })
    
    # Export devices
    devices_file = output_path / 'devices.csv'
    with open(devices_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'device_id', 'user_count', 'user_ids', 'first_seen', 'last_seen'
        ])
        writer.writeheader()
        for node in graph_snapshot.device_nodes.values():
            writer.writerow({
                'device_id': node.device_id,
                'user_count': node.user_count,
                'user_ids': ','.join(node.user_ids),  # CSV: comma-separated
                'first_seen': node.first_seen.isoformat() if node.first_seen else '',
                'last_seen': node.last_seen.isoformat() if node.last_seen else ''
            })


def export_edge_lists(
    graph_snapshot: GraphSnapshot,
    output_path: str,
    format: str = "json"
) -> None:
    """
    Export edge lists to a file.
    
    Exports all edge types (messages, transactions, creates, device, views)
    in a format suitable for graph processing.
    
    Args:
        graph_snapshot: GraphSnapshot to export
        output_path: Path to output file
        format: Export format ("json" or "csv")
    """
    if format == "json":
        _export_edge_lists_json(graph_snapshot, output_path)
    elif format == "csv":
        _export_edge_lists_csv(graph_snapshot, output_path)
    else:
        raise ValueError(f"Unsupported format: {format}")


def _export_edge_lists_json(graph_snapshot: GraphSnapshot, output_path: str) -> None:
    """Export edge lists as JSON."""
    data = {
        'metadata': {
            'timestamp': graph_snapshot.timestamp.isoformat(),
            'edge_counts': {
                'messages': len(graph_snapshot.message_edges),
                'transactions': len(graph_snapshot.transaction_edges),
                'creates': len(graph_snapshot.creates_edges),
                'devices': len(graph_snapshot.device_edges),
                'views': len(graph_snapshot.view_edges)
            }
        },
        'message_edges': [
            {
                'from_user_id': edge.from_user_id,
                'to_user_id': edge.to_user_id,
                'message_count': edge.message_count,
                'avg_response_time_seconds': edge.avg_response_time_seconds,
                'first_message_at': edge.first_message_at.isoformat(),
                'last_message_at': edge.last_message_at.isoformat()
            }
            for edge in graph_snapshot.message_edges
        ],
        'transaction_edges': [
            {'user_id': user_id, 'listing_id': listing_id}
            for user_id, listing_id in graph_snapshot.transaction_edges
        ],
        'creates_edges': [
            {'user_id': user_id, 'listing_id': listing_id}
            for user_id, listing_id in graph_snapshot.creates_edges
        ],
        'device_edges': [
            {'user_id': user_id, 'device_id': device_id}
            for user_id, device_id in graph_snapshot.device_edges
        ],
        'view_edges': [
            {'user_id': user_id, 'listing_id': listing_id}
            for user_id, listing_id in graph_snapshot.view_edges
        ]
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)


def _export_edge_lists_csv(graph_snapshot: GraphSnapshot, output_dir: str) -> None:
    """Export edge lists as CSV files (one per edge type)."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Message edges
    messages_file = output_path / 'message_edges.csv'
    with open(messages_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'from_user_id', 'to_user_id', 'message_count',
            'avg_response_time_seconds', 'first_message_at', 'last_message_at'
        ])
        writer.writeheader()
        for edge in graph_snapshot.message_edges:
            writer.writerow({
                'from_user_id': edge.from_user_id,
                'to_user_id': edge.to_user_id,
                'message_count': edge.message_count,
                'avg_response_time_seconds': edge.avg_response_time_seconds,
                'first_message_at': edge.first_message_at.isoformat(),
                'last_message_at': edge.last_message_at.isoformat()
            })
    
    # Transaction edges
    transactions_file = output_path / 'transaction_edges.csv'
    with open(transactions_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['user_id', 'listing_id'])
        writer.writerows(graph_snapshot.transaction_edges)
    
    # Creates edges
    creates_file = output_path / 'creates_edges.csv'
    with open(creates_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['user_id', 'listing_id'])
        writer.writerows(graph_snapshot.creates_edges)
    
    # Device edges
    devices_file = output_path / 'device_edges.csv'
    with open(devices_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['user_id', 'device_id'])
        writer.writerows(graph_snapshot.device_edges)
    
    # View edges
    views_file = output_path / 'view_edges.csv'
    with open(views_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['user_id', 'listing_id'])
        writer.writerows(graph_snapshot.view_edges)


def export_labels(
    labels: Dict[str, int],
    output_path: str,
    format: str = "json"
) -> None:
    """
    Export user labels to a file.
    
    Labels are:
    - 0: Normal
    - 1: Suspicious
    - 2: Spam/Fraud
    
    Args:
        labels: Dictionary mapping user_id -> label
        output_path: Path to output file
        format: Export format ("json" or "csv")
    """
    if format == "json":
        data = {
            'metadata': {
                'total_users': len(labels),
                'label_distribution': {
                    'normal': sum(1 for l in labels.values() if l == 0),
                    'suspicious': sum(1 for l in labels.values() if l == 1),
                    'fraud': sum(1 for l in labels.values() if l == 2)
                }
            },
            'labels': [
                {'user_id': user_id, 'label': label}
                for user_id, label in labels.items()
            ]
        }
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    elif format == "csv":
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['user_id', 'label'])
            writer.writeheader()
            for user_id, label in labels.items():
                writer.writerow({'user_id': user_id, 'label': label})
    
    else:
        raise ValueError(f"Unsupported format: {format}")


def export_complete_dataset(
    graph_snapshot: GraphSnapshot,
    labels: Dict[str, int],
    output_dir: str,
    format: str = "json"
) -> None:
    """
    Export complete dataset (nodes, edges, labels) to a directory.
    
    This is a convenience function that exports everything needed for
    machine learning experiments.
    
    Args:
        graph_snapshot: GraphSnapshot to export
        labels: User labels
        output_dir: Directory to export to
        format: Export format ("json" or "csv")
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Export nodes
    if format == "json":
        export_node_features(graph_snapshot, str(output_path / 'nodes.json'), format)
        export_edge_lists(graph_snapshot, str(output_path / 'edges.json'), format)
        export_labels(labels, str(output_path / 'labels.json'), format)
    else:
        export_node_features(graph_snapshot, str(output_path), format)
        export_edge_lists(graph_snapshot, str(output_path), format)
        export_labels(labels, str(output_path / 'labels.csv'), format)
    
    # Export metadata
    metadata = {
        'snapshot_timestamp': graph_snapshot.timestamp.isoformat(),
        'node_counts': {
            'users': len(graph_snapshot.user_nodes),
            'listings': len(graph_snapshot.listing_nodes),
            'devices': len(graph_snapshot.device_nodes)
        },
        'edge_counts': {
            'messages': len(graph_snapshot.message_edges),
            'transactions': len(graph_snapshot.transaction_edges),
            'creates': len(graph_snapshot.creates_edges),
            'devices': len(graph_snapshot.device_edges),
            'views': len(graph_snapshot.view_edges)
        },
        'label_distribution': {
            'normal': sum(1 for l in labels.values() if l == 0),
            'suspicious': sum(1 for l in labels.values() if l == 1),
            'fraud': sum(1 for l in labels.values() if l == 2)
        }
    }
    
    metadata_file = output_path / 'metadata.json'
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

