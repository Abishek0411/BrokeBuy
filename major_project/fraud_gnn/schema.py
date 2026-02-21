"""
Graph Schema Definitions for Fraud Detection

This module defines the data structures representing nodes and edges in the
heterogeneous graph used for fraud detection. These are NOT database models,
but rather in-memory graph representations.

The graph structure:
- Nodes: Users, Listings, Devices
- Edges: Messages, Transactions, Device-User associations
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from datetime import datetime
from enum import Enum


class NodeType(str, Enum):
    """Types of nodes in the heterogeneous graph."""
    USER = "user"
    LISTING = "listing"
    DEVICE = "device"


class EdgeType(str, Enum):
    """Types of edges in the heterogeneous graph."""
    MESSAGE = "message"           # User -> User (communication)
    TRANSACTION = "transaction"   # User -> Listing (purchase/sale)
    CREATES = "creates"           # User -> Listing (listing creation)
    USES_DEVICE = "uses_device"   # User -> Device (device association)
    VIEWS = "views"               # User -> Listing (viewing behavior)


@dataclass
class UserNode:
    """
    Represents a user node in the fraud detection graph.
    
    Attributes:
        user_id: Unique identifier for the user
        account_age_days: Age of the account in days
        listings_count: Number of listings created
        transactions_count: Number of completed transactions
        messages_sent: Number of messages sent
        messages_received: Number of messages received
        avg_listing_price: Average price of listings created
        verification_status: Whether the user is verified
        risk_score: Computed risk score (0-1), None if not computed yet
        features: Extracted feature vector (to be populated by features.py)
        created_at: Account creation timestamp
    """
    user_id: str
    account_age_days: int
    listings_count: int
    transactions_count: int
    messages_sent: int
    messages_received: int
    avg_listing_price: float
    verification_status: bool
    risk_score: Optional[float] = None
    features: Optional[List[float]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __hash__(self):
        return hash(self.user_id)


@dataclass
class ListingNode:
    """
    Represents a listing node in the fraud detection graph.
    
    Attributes:
        listing_id: Unique identifier for the listing
        seller_id: ID of the user who created the listing
        price: Listing price
        category: Category of the item
        condition: Condition of the item (new, used, etc.)
        views_count: Number of times the listing was viewed
        messages_count: Number of messages related to this listing
        is_sold: Whether the listing has been sold
        days_active: Number of days the listing has been active
        risk_score: Computed risk score (0-1), None if not computed yet
        features: Extracted feature vector (to be populated by features.py)
        created_at: Listing creation timestamp
    """
    listing_id: str
    seller_id: str
    price: float
    category: str
    condition: str
    views_count: int
    messages_count: int
    is_sold: bool
    days_active: int
    risk_score: Optional[float] = None
    features: Optional[List[float]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __hash__(self):
        return hash(self.listing_id)


@dataclass
class DeviceNode:
    """
    Represents a device node in the fraud detection graph.
    
    Device fingerprinting helps detect:
    - Multiple accounts from the same device (potential Sybil attack)
    - Shared devices between suspicious users
    
    Attributes:
        device_id: Unique device fingerprint (hash of device characteristics)
        user_count: Number of users associated with this device
        user_ids: Set of user IDs using this device
        first_seen: First time this device was seen
        last_seen: Most recent time this device was seen
        risk_score: Computed risk score (0-1), None if not computed yet
        features: Extracted feature vector (to be populated by features.py)
    """
    device_id: str
    user_count: int
    user_ids: Set[str] = field(default_factory=set)
    first_seen: datetime = field(default_factory=datetime.utcnow)
    last_seen: datetime = field(default_factory=datetime.utcnow)
    risk_score: Optional[float] = None
    features: Optional[List[float]] = None
    
    def __hash__(self):
        return hash(self.device_id)


@dataclass
class MessageEdge:
    """
    Represents a message edge between two users.
    
    Message patterns can reveal:
    - Spam rings (users messaging each other in coordinated patterns)
    - Suspicious communication (very short time between messages)
    - One-sided communication (potential harassment)
    
    Attributes:
        from_user_id: Source user ID
        to_user_id: Target user ID
        message_count: Number of messages in this conversation
        avg_response_time_seconds: Average time between messages
        first_message_at: Timestamp of first message
        last_message_at: Timestamp of most recent message
        features: Extracted feature vector (to be populated by features.py)
    """
    from_user_id: str
    to_user_id: str
    message_count: int
    avg_response_time_seconds: float
    first_message_at: datetime
    last_message_at: datetime
    features: Optional[List[float]] = None
    
    def __hash__(self):
        return hash((self.from_user_id, self.to_user_id))


@dataclass
class GraphSnapshot:
    """
    Represents a complete snapshot of the marketplace graph at a point in time.
    
    This is the primary input to the GNN model for fraud detection.
    The graph is heterogeneous, containing multiple node types and edge types.
    
    Attributes:
        timestamp: When this snapshot was created
        user_nodes: Dictionary mapping user_id -> UserNode
        listing_nodes: Dictionary mapping listing_id -> ListingNode
        device_nodes: Dictionary mapping device_id -> DeviceNode
        message_edges: List of MessageEdge objects
        transaction_edges: List of (user_id, listing_id) tuples representing transactions
        creates_edges: List of (user_id, listing_id) tuples representing listing creation
        device_edges: List of (user_id, device_id) tuples representing device associations
        view_edges: List of (user_id, listing_id) tuples representing views (sampled if too many)
        
    Note: Edge lists use tuples for efficiency. Full edge objects can be reconstructed
    from node data if needed.
    """
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_nodes: Dict[str, UserNode] = field(default_factory=dict)
    listing_nodes: Dict[str, ListingNode] = field(default_factory=dict)
    device_nodes: Dict[str, DeviceNode] = field(default_factory=dict)
    message_edges: List[MessageEdge] = field(default_factory=list)
    transaction_edges: List[tuple] = field(default_factory=list)  # (user_id, listing_id)
    creates_edges: List[tuple] = field(default_factory=list)      # (user_id, listing_id)
    device_edges: List[tuple] = field(default_factory=list)      # (user_id, device_id)
    view_edges: List[tuple] = field(default_factory=list)        # (user_id, listing_id)
    
    def get_node_count(self) -> int:
        """Get total number of nodes in the graph."""
        return len(self.user_nodes) + len(self.listing_nodes) + len(self.device_nodes)
    
    def get_edge_count(self) -> int:
        """Get total number of edges in the graph."""
        return (len(self.message_edges) + 
                len(self.transaction_edges) + 
                len(self.creates_edges) + 
                len(self.device_edges) + 
                len(self.view_edges))
    
    def get_user_by_id(self, user_id: str) -> Optional[UserNode]:
        """Get a user node by ID."""
        return self.user_nodes.get(user_id)
    
    def get_listing_by_id(self, listing_id: str) -> Optional[ListingNode]:
        """Get a listing node by ID."""
        return self.listing_nodes.get(listing_id)
    
    def get_device_by_id(self, device_id: str) -> Optional[DeviceNode]:
        """Get a device node by ID."""
        return self.device_nodes.get(device_id)

