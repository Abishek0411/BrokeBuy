"""
Graph Snapshot Builder

This module implements the GraphSnapshotBuilder class for creating time-bounded
graph snapshots from BrokeBuy marketplace data.

Why Snapshots Instead of Static Graphs?
----------------------------------------

Fraud detection in marketplaces is inherently temporal. Fraudsters exhibit
behavioral patterns that evolve over time:

1. **Temporal Patterns**: A user might be legitimate for months, then suddenly
   start spamming. A static graph would miss this transition.

2. **Context Matters**: The same behavior (e.g., creating 10 listings) is
   suspicious for a new account but normal for an established seller. Time
   provides this context.

3. **Fraud Evolution**: Attackers adapt. A snapshot from January might show
   different patterns than a snapshot from June. By using time-bounded
   snapshots, we can:
   - Track how fraud patterns evolve
   - Train models on historical snapshots
   - Evaluate model performance on future snapshots
   - Detect emerging fraud patterns

4. **Reproducibility**: Snapshots allow us to:
   - Reproduce experiments with exact same graph state
   - Compare models on identical datasets
   - Debug by examining specific time periods

5. **Scalability**: Instead of maintaining one massive graph, we can:
   - Build snapshots for specific time windows
   - Process snapshots independently
   - Archive old snapshots for historical analysis

How Temporal Behavior Reveals Fraud Patterns
---------------------------------------------

1. **Burst Detection**: Fraudsters often create accounts and immediately
   start spamming. A snapshot covering the first week of an account's life
   reveals this burst pattern.

2. **Coordination Detection**: Sybil attacks involve multiple accounts
   created in a short time window. A snapshot of that window reveals the
   coordination.

3. **Activity Patterns**: Legitimate users have consistent activity over time.
   Fraudsters often have irregular patterns (e.g., high activity for one day,
   then nothing). Snapshots capture these patterns.

4. **Network Evolution**: Fraud networks grow over time. Early snapshots
   might show isolated accounts, while later snapshots reveal the full network.

5. **Seasonal Patterns**: Fraud might spike during certain times (e.g., exam
   periods when students sell books). Snapshots allow us to study these patterns.
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from ..schema import (
    GraphSnapshot,
    UserNode,
    ListingNode,
    DeviceNode,
    MessageEdge,
    NodeType,
    EdgeType
)


class GraphSnapshotBuilder:
    """
    Builder class for creating time-bounded graph snapshots from BrokeBuy data.
    
    A snapshot represents the state of the marketplace graph at a specific
    point in time, or over a specific time window. This allows us to:
    - Study fraud patterns at different time periods
    - Train models on historical data
    - Evaluate models on future data
    - Reproduce experiments
    
    The builder takes raw data (already loaded from database) and constructs
    a GraphSnapshot object with nodes and edges filtered by the time window.
    """
    
    def __init__(self):
        """Initialize the snapshot builder."""
        pass
    
    def build_snapshot(
        self,
        users: List[Dict],
        listings: List[Dict],
        messages: List[Dict],
        devices: List[Dict],
        start_time: datetime,
        end_time: datetime
    ) -> GraphSnapshot:
        """
        Build a GraphSnapshot for the specified time window.
        
        This method creates a time-bounded snapshot by:
        1. Filtering all entities (users, listings, messages, devices) to
           those active in the time window
        2. Creating node objects (UserNode, ListingNode, DeviceNode)
        3. Creating edge objects (MessageEdge) and edge lists
        4. Computing temporal features (account age, days active, etc.)
        
        Time Window Logic:
        - Users: Included if account was created before end_time
        - Listings: Included if created between start_time and end_time
        - Messages: Included if sent between start_time and end_time
        - Devices: Included if seen between start_time and end_time
        - Transactions: Included if occurred between start_time and end_time
        
        Why This Time Window Approach?
        --------------------------------
        - We want to see the state of the graph at end_time
        - But we need historical context (users created before end_time)
        - Activities (listings, messages) are filtered to the window
        - This gives us a "snapshot" of what the graph looked like at end_time,
          with only activities from the window
        
        Args:
            users: List of user documents from database
                Each dict should have: _id, created_at, and other user fields
            listings: List of listing documents from database
                Each dict should have: _id, seller_id, created_at, price, etc.
            messages: List of message documents from database
                Each dict should have: from_user_id, to_user_id, created_at, etc.
            devices: List of device documents from database
                Each dict should have: device_id, user_ids, first_seen, last_seen
            start_time: Start of the time window (inclusive)
            end_time: End of the time window (inclusive)
            
        Returns:
            GraphSnapshot containing nodes and edges for the time window
            
        Example:
            >>> builder = GraphSnapshotBuilder()
            >>> snapshot = builder.build_snapshot(
            ...     users=users_data,
            ...     listings=listings_data,
            ...     messages=messages_data,
            ...     devices=devices_data,
            ...     start_time=datetime(2024, 1, 1),
            ...     end_time=datetime(2024, 1, 31)
            ... )
            >>> print(f"Snapshot has {snapshot.get_node_count()} nodes")
        """
        # Initialize empty snapshot
        snapshot = GraphSnapshot(timestamp=end_time)
        
        # Step 1: Filter and create user nodes
        # Include users created before or during the time window
        # (we need their existence even if they're not active in the window)
        user_nodes = {}
        for user_data in users:
            user_created = self._parse_datetime(user_data.get('created_at'))
            if user_created and user_created <= end_time:
                user_node = self._create_user_node(user_data, end_time)
                user_nodes[user_node.user_id] = user_node
        snapshot.user_nodes = user_nodes
        
        # Step 2: Filter and create listing nodes
        # Include listings created within the time window
        listing_nodes = {}
        listing_activity = defaultdict(int)  # Track activity per user
        for listing_data in listings:
            listing_created = self._parse_datetime(listing_data.get('created_at'))
            if listing_created and start_time <= listing_created <= end_time:
                listing_node = self._create_listing_node(listing_data, end_time)
                listing_nodes[listing_node.listing_id] = listing_node
                # Track listing creation activity
                listing_activity[listing_node.seller_id] += 1
        snapshot.listing_nodes = listing_nodes
        
        # Step 3: Filter and create device nodes
        # Include devices seen during the time window
        device_nodes = {}
        for device_data in devices:
            first_seen = self._parse_datetime(device_data.get('first_seen'))
            last_seen = self._parse_datetime(device_data.get('last_seen'))
            
            # Include device if it was active during the window
            if first_seen and last_seen:
                if (first_seen <= end_time and last_seen >= start_time):
                    device_node = self._create_device_node(device_data)
                    device_nodes[device_node.device_id] = device_node
        snapshot.device_nodes = device_nodes
        
        # Step 4: Filter and create message edges
        # Include messages sent within the time window
        message_edges = []
        message_stats = defaultdict(lambda: {'count': 0, 'times': []})
        
        for message_data in messages:
            message_created = self._parse_datetime(message_data.get('created_at'))
            if message_created and start_time <= message_created <= end_time:
                from_user = message_data.get('from_user_id')
                to_user = message_data.get('to_user_id')
                
                if from_user and to_user and from_user in user_nodes and to_user in user_nodes:
                    # Track message statistics for edge creation
                    edge_key = (from_user, to_user)
                    message_stats[edge_key]['count'] += 1
                    message_stats[edge_key]['times'].append(message_created)
        
        # Create MessageEdge objects from aggregated statistics
        for (from_user, to_user), stats in message_stats.items():
            message_edge = self._create_message_edge(
                from_user, to_user, stats['count'], stats['times']
            )
            message_edges.append(message_edge)
        snapshot.message_edges = message_edges
        
        # Step 5: Create edge lists
        # Creates edges: (user_id, listing_id) for listings created in window
        snapshot.creates_edges = [
            (listing.seller_id, listing.listing_id)
            for listing in listing_nodes.values()
        ]
        
        # Transaction edges: (buyer_id, listing_id) for transactions in window
        # Note: Assuming transactions_data would be passed if available
        # For now, we'll create empty list (can be extended)
        snapshot.transaction_edges = []
        
        # Device edges: (user_id, device_id) for device associations
        device_edges = []
        for device in device_nodes.values():
            for user_id in device.user_ids:
                if user_id in user_nodes:
                    device_edges.append((user_id, device.device_id))
        snapshot.device_edges = device_edges
        
        # View edges: (user_id, listing_id) for views in window
        # Note: Views are typically too numerous, so we might sample them
        # For now, empty list (can be extended with view data)
        snapshot.view_edges = []
        
        # Update user activity counts based on snapshot data
        self._update_user_activity_counts(snapshot)
        
        return snapshot
    
    def _create_user_node(self, user_data: Dict, snapshot_time: datetime) -> UserNode:
        """
        Create a UserNode from user data.
        
        Computes temporal features like account_age_days relative to snapshot time.
        """
        user_id = str(user_data.get('_id', user_data.get('user_id', '')))
        created_at = self._parse_datetime(user_data.get('created_at'))
        
        if created_at:
            account_age_days = (snapshot_time - created_at).days
        else:
            account_age_days = 0
        
        return UserNode(
            user_id=user_id,
            account_age_days=account_age_days,
            listings_count=user_data.get('listings_count', 0),
            transactions_count=user_data.get('transactions_count', 0),
            messages_sent=user_data.get('messages_sent', 0),
            messages_received=user_data.get('messages_received', 0),
            avg_listing_price=user_data.get('avg_listing_price', 0.0),
            verification_status=user_data.get('verification_status', False),
            created_at=created_at or snapshot_time
        )
    
    def _create_listing_node(self, listing_data: Dict, snapshot_time: datetime) -> ListingNode:
        """Create a ListingNode from listing data."""
        listing_id = str(listing_data.get('_id', listing_data.get('listing_id', '')))
        created_at = self._parse_datetime(listing_data.get('created_at'))
        
        if created_at:
            days_active = (snapshot_time - created_at).days
        else:
            days_active = 0
        
        return ListingNode(
            listing_id=listing_id,
            seller_id=str(listing_data.get('seller_id', '')),
            price=float(listing_data.get('price', 0.0)),
            category=listing_data.get('category', ''),
            condition=listing_data.get('condition', ''),
            views_count=listing_data.get('views_count', 0),
            messages_count=listing_data.get('messages_count', 0),
            is_sold=listing_data.get('is_sold', False),
            days_active=days_active,
            created_at=created_at or snapshot_time
        )
    
    def _create_device_node(self, device_data: Dict) -> DeviceNode:
        """Create a DeviceNode from device data."""
        device_id = str(device_data.get('device_id', ''))
        user_ids = device_data.get('user_ids', [])
        
        return DeviceNode(
            device_id=device_id,
            user_count=len(user_ids),
            user_ids=set(str(uid) for uid in user_ids),
            first_seen=self._parse_datetime(device_data.get('first_seen')),
            last_seen=self._parse_datetime(device_data.get('last_seen'))
        )
    
    def _create_message_edge(
        self,
        from_user_id: str,
        to_user_id: str,
        message_count: int,
        message_times: List[datetime]
    ) -> MessageEdge:
        """
        Create a MessageEdge from message statistics.
        
        Computes average response time from message timestamps.
        """
        if len(message_times) < 2:
            avg_response_time = 0.0
        else:
            # Compute average time between consecutive messages
            intervals = []
            sorted_times = sorted(message_times)
            for i in range(1, len(sorted_times)):
                interval = (sorted_times[i] - sorted_times[i-1]).total_seconds()
                intervals.append(interval)
            avg_response_time = sum(intervals) / len(intervals) if intervals else 0.0
        
        return MessageEdge(
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            message_count=message_count,
            avg_response_time_seconds=avg_response_time,
            first_message_at=min(message_times) if message_times else datetime.utcnow(),
            last_message_at=max(message_times) if message_times else datetime.utcnow()
        )
    
    def _update_user_activity_counts(self, snapshot: GraphSnapshot) -> None:
        """
        Update user activity counts based on snapshot data.
        
        This computes activity counts from the snapshot itself, ensuring
        consistency between node attributes and graph structure.
        """
        # Count listings per user
        for listing in snapshot.listing_nodes.values():
            if listing.seller_id in snapshot.user_nodes:
                snapshot.user_nodes[listing.seller_id].listings_count += 1
        
        # Count messages per user
        for message_edge in snapshot.message_edges:
            if message_edge.from_user_id in snapshot.user_nodes:
                snapshot.user_nodes[message_edge.from_user_id].messages_sent += message_edge.message_count
            if message_edge.to_user_id in snapshot.user_nodes:
                snapshot.user_nodes[message_edge.to_user_id].messages_received += message_edge.message_count
    
    def _parse_datetime(self, value) -> Optional[datetime]:
        """
        Parse datetime from various formats.
        
        Handles:
        - datetime objects (return as-is)
        - ISO format strings
        - Unix timestamps
        - None (returns None)
        """
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                # Try ISO format
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except:
                try:
                    # Try Unix timestamp
                    return datetime.fromtimestamp(float(value))
                except:
                    return None
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value)
        return None

