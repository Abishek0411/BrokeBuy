import random
import torch
from datetime import datetime, timedelta
from collections import defaultdict


from major_project.fraud_gnn.schema import (
    UserNode, ListingNode, MessageEdge, DeviceNode, GraphSnapshot
)
from major_project.fraud_gnn.dataset.snapshot_builder import GraphSnapshotBuilder
from major_project.fraud_gnn.dataset.labeling import label_users
from major_project.fraud_gnn.gnn.data_loader import load_graph_snapshot
from major_project.fraud_gnn.gnn.model import FraudGNN
from major_project.fraud_gnn.gnn.train import train_model
from major_project.fraud_gnn.gnn.evaluate import evaluate_gnn

# -----------------------------
# 1. Create synthetic entities
# -----------------------------
users = []

for i in range(30):
    is_spam = i < 5  # first 5 users are spammers

    users.append(
        UserNode(
            user_id=f"user_{i}",
            account_age_days=random.randint(1, 30) if is_spam else random.randint(60, 300),
            listings_count=random.randint(10, 20) if is_spam else random.randint(1, 5),
            transactions_count=0 if is_spam else random.randint(1, 10),
            messages_sent=random.randint(40, 80) if is_spam else random.randint(5, 15),
            messages_received=random.randint(1, 5) if is_spam else random.randint(5, 20),
            avg_listing_price=random.uniform(100, 500),
            verification_status=False if is_spam else True
        )
    )


# Inject 5 spam users
spam_users = set(u.user_id for u in users[:5])

listings = []
devices = []

# -----------------------------
# 2. Generate RAW message events
# -----------------------------
raw_messages = []

for u in users:
    is_spam = u.user_id in spam_users
    msg_count = random.randint(20, 40) if is_spam else random.randint(3, 8)

    start_time = datetime.now()

    for i in range(msg_count):
        raw_messages.append({
            "from": u.user_id,
            "to": random.choice(users).user_id,
            "timestamp": start_time + timedelta(seconds=random.randint(1, 300))
        })

# -----------------------------
# 3. Aggregate into MessageEdge
# -----------------------------
message_groups = defaultdict(list)

for msg in raw_messages:
    key = (msg["from"], msg["to"])
    message_groups[key].append(msg["timestamp"])

messages = []

for (from_user, to_user), timestamps in message_groups.items():
    timestamps.sort()
    message_count = len(timestamps)

    if message_count > 1:
        response_times = [
            (timestamps[i] - timestamps[i - 1]).total_seconds()
            for i in range(1, message_count)
        ]
        avg_response_time = sum(response_times) / len(response_times)
    else:
        avg_response_time = 0.0

    messages.append(
        MessageEdge(
            from_user_id=from_user,
            to_user_id=to_user,
            message_count=message_count,
            avg_response_time_seconds=avg_response_time,
            first_message_at=timestamps[0],
            last_message_at=timestamps[-1],
            features=None
        )
    )

# -----------------------------
# 2. Build snapshot
# -----------------------------
builder = GraphSnapshotBuilder()
# -----------------------------
# Convert schema objects to dicts (simulate DB export)
# -----------------------------
user_dicts = []
for u in users:
    user_dicts.append({
        "user_id": u.user_id,
        "account_age_days": u.account_age_days,
        "listings_count": u.listings_count,
        "transactions_count": u.transactions_count,
        "messages_sent": u.messages_sent,
        "messages_received": u.messages_received,
        "avg_listing_price": u.avg_listing_price,
        "verification_status": u.verification_status,
        # snapshot_builder expects created_at
        "created_at": datetime.now() - timedelta(days=u.account_age_days)
    })

message_dicts = []
for m in messages:
    message_dicts.append({
        "from_user_id": m.from_user_id,
        "to_user_id": m.to_user_id,
        "message_count": m.message_count,
        "avg_response_time_seconds": m.avg_response_time_seconds,
        "first_message_at": m.first_message_at,
        "last_message_at": m.last_message_at
    })

snapshot = builder.build_snapshot(
    users=user_dicts,
    listings=[],
    messages=message_dicts,
    devices=[],
    start_time=datetime.now() - timedelta(days=1),
    end_time=datetime.now()
)

# -----------------------------
# 3. Label users
# -----------------------------
labels = label_users(snapshot)

# Force 1-2 users as fraud for testing fraud detection
# Override labels for first 2 users to be fraud (label=2)
fraud_user_ids = list(snapshot.user_nodes.keys())[:2]  # First 2 users
for user_id in fraud_user_ids:
    labels[user_id] = 2  # Force as fraud
    print(f"Forced {user_id} as fraud for testing")

snapshot.labels = labels

# -----------------------------
# 4. Convert to PyG data
# -----------------------------
data = load_graph_snapshot(snapshot, labels)

# -----------------------------
# 5. Train GNN
# -----------------------------
model = FraudGNN(
    input_dim=data.x.shape[1],
    hidden_dim=32,
    output_dim=3
)

training_results = train_model(
    model=model,
    data=data,
    epochs=30,
    lr=0.01
)

# Extract the trained model from the results dictionary
trained_model = training_results['model']

# -----------------------------
# 6. Evaluate
# -----------------------------
metrics = evaluate_gnn(trained_model, data)
print("\nGNN Evaluation Metrics:")
print(metrics)
