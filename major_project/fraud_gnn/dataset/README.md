# 📊 Fraud Detection Dataset

This folder contains the dataset construction pipeline for graph-based fraud detection experiments.

## Overview

The dataset is constructed from BrokeBuy marketplace data and represents a heterogeneous graph with nodes (users, listings, devices) and edges (messages, transactions, device associations). The dataset is designed for research reproducibility and machine learning experiments.

## Dataset Composition

### Node Types

1. **User Nodes** (`UserNode`)
   - Represent marketplace users
   - Features: account age, activity counts, verification status
   - Count: Variable (typically 100-10,000 users per snapshot)

2. **Listing Nodes** (`ListingNode`)
   - Represent product listings
   - Features: price, category, condition, views, messages
   - Count: Variable (typically 500-50,000 listings per snapshot)

3. **Device Nodes** (`DeviceNode`)
   - Represent device fingerprints
   - Features: user count, first seen, last seen
   - Count: Variable (typically 50-5,000 devices per snapshot)

### Edge Types

1. **Message Edges** (`MessageEdge`)
   - User-to-user communication
   - Directed: from_user → to_user
   - Features: message count, average response time
   - Count: Variable (typically 1,000-100,000 edges)

2. **Transaction Edges**
   - User purchases listing
   - Directed: buyer → listing
   - Count: Variable (typically 100-10,000 edges)

3. **Creates Edges**
   - User creates listing
   - Directed: seller → listing
   - Count: Equal to number of listings

4. **Device Edges**
   - User uses device
   - Undirected (represented as directed: user → device)
   - Count: Variable (typically 200-20,000 edges)

5. **View Edges**
   - User views listing
   - Directed: viewer → listing
   - Count: Variable (typically 10,000-1,000,000 edges, may be sampled)

## Graph Snapshot Concept

The dataset uses **time-bounded snapshots** rather than a single static graph. This allows:

- **Temporal Analysis**: Study how fraud patterns evolve over time
- **Reproducibility**: Exact same graph state for experiments
- **Training/Testing Split**: Train on historical snapshots, test on future ones
- **Pattern Discovery**: Identify emerging fraud patterns

A snapshot represents the graph state at a specific point in time, with activities (listings, messages) filtered to a time window.

## Labeling Approach

### Label Types

- **0: Normal** - Legitimate user with no fraud indicators
- **1: Suspicious** - User exhibits some fraud indicators but not conclusive
- **2: Spam/Fraud** - User exhibits multiple strong fraud indicators

### Labeling Rules

Labels are assigned using rule-based heuristics that capture known fraud patterns:

1. **Message Burst Rate**: Users sending many messages in short time
2. **Listing Burst Rate**: Users creating many listings quickly
3. **Device Sharing**: Multiple users sharing same device (Sybil attack)
4. **Account Age vs Activity**: New accounts with unusually high activity
5. **Network Isolation**: Accounts with no connections
6. **Suspicious Network**: Accounts connected to many high-risk accounts

### Why Rule-Based Labeling?

- **Scalability**: Can label thousands of users automatically
- **Consistency**: Same rules applied to all users
- **Explainability**: We know exactly why a user was labeled
- **Weak Supervision**: Even imperfect labels can train good models

### Label Quality

**Important**: These labels are **approximations** of ground truth, not perfect labels. Reasons:

- Unknown fraud: Many fraudsters are never caught
- False positives: Legitimate users might exhibit suspicious patterns
- Context missing: Rules can't capture all context
- Evolving patterns: Fraud patterns change over time

This is acceptable for research because:
- GNNs can learn patterns beyond the labeling rules
- Comparative evaluation is still valid (same labels for all models)
- Real-world systems also have imperfect ground truth

## Dataset Files

### Construction Files

- `snapshot_builder.py` - Builds graph snapshots from raw data
- `labeling.py` - Rule-based labeling strategy
- `rules_baseline.py` - Baseline detector (no graph awareness)
- `export.py` - Export functions for ML experiments

### Export Formats

The dataset can be exported in two formats:

1. **JSON** (default)
   - Human-readable
   - Single file per data type
   - Easy to inspect and debug

2. **CSV**
   - Spreadsheet-compatible
   - Separate files per node/edge type
   - Good for data analysis tools

### Export Structure

```
dataset/
├── nodes.json (or nodes/ directory for CSV)
│   ├── users
│   ├── listings
│   └── devices
├── edges.json (or edges/ directory for CSV)
│   ├── message_edges
│   ├── transaction_edges
│   ├── creates_edges
│   ├── device_edges
│   └── view_edges
├── labels.json (or labels.csv)
└── metadata.json
```

## Usage Example

```python
from fraud_gnn.dataset import (
    GraphSnapshotBuilder,
    label_users,
    export_complete_dataset
)

# Build snapshot
builder = GraphSnapshotBuilder()
snapshot = builder.build_snapshot(
    users=users_data,
    listings=listings_data,
    messages=messages_data,
    devices=devices_data,
    start_time=datetime(2024, 1, 1),
    end_time=datetime(2024, 1, 31)
)

# Label users
labels = label_users(snapshot)

# Export dataset
export_complete_dataset(
    graph_snapshot=snapshot,
    labels=labels,
    output_dir="dataset/2024_01",
    format="json"
)
```

## Ethical Considerations

### Data Privacy

- **No PII**: User IDs are anonymized/hashed
- **No Content**: Listing descriptions and message content are not included
- **Aggregated Data**: Only aggregated statistics (counts, rates) are used
- **Research Purpose**: Data is used solely for research, not commercial purposes

### Bias Considerations

- **Labeling Bias**: Rule-based labeling may have biases (e.g., flagging new users)
- **Data Bias**: Dataset reflects BrokeBuy user base, which may not be representative
- **Evaluation Bias**: Models should be evaluated on diverse test sets

### Responsible Use

- **No Discrimination**: Models should not discriminate based on protected attributes
- **Transparency**: Labeling rules are documented and explainable
- **Fairness**: Models should be evaluated for fairness across user groups
- **Privacy**: No attempt to de-anonymize users or extract sensitive information

## Reproducibility

### Version Control

- Dataset construction code is version-controlled
- Export timestamps are included in metadata
- Labeling rules are documented and fixed

### Reproducibility Steps

1. Use same code version
2. Use same input data
3. Use same time windows
4. Use same labeling rules
5. Export with same format

### Sharing Datasets

When sharing datasets for reproducibility:
- Include metadata.json with all parameters
- Document data source and time windows
- Include labeling rule documentation
- Anonymize user IDs if sharing externally

## Limitations

1. **Time Window**: Snapshots represent a specific time period, may miss long-term patterns
2. **Sampling**: View edges may be sampled if too numerous
3. **Incomplete Data**: Some features may be missing for some nodes
4. **Label Quality**: Labels are approximations, not perfect ground truth
5. **Scale**: Large graphs may require optimization or sampling

## Future Enhancements

- [ ] Temporal graph sequences (multiple snapshots over time)
- [ ] Dynamic edge weights based on interaction frequency
- [ ] Additional node types (categories, locations)
- [ ] Additional edge types (reviews, favorites)
- [ ] Graph sampling strategies for large graphs
- [ ] Active learning for label improvement

---

**Last Updated**: [Date]  
**Dataset Version**: 1.0.0  
**Status**: Research Dataset

