# 🔗 Integration Notes: Major Project & BrokeBuy

## Core Principle: Loose Coupling

**The Major Project modules are designed as independent Trust & Safety engines that BrokeBuy consumes, not tightly integrated components.**

This document explains why BrokeBuy is NOT tightly coupled to the research models and how the integration boundary works.

---

## Why BrokeBuy is NOT Tightly Coupled

### 1. Separation of Concerns

**BrokeBuy Core Logic** (Business Logic):
- User registration and authentication
- Listing creation and management
- Transaction processing
- Messaging between users
- Wallet and payment handling

**Major Project Modules** (Trust & Safety):
- Fraud detection and risk scoring
- Face verification for identity
- Privacy-preserving biometrics
- Research and experimentation

**Key Point**: BrokeBuy's business logic operates independently. The research modules provide **advisory services** (risk scores, verification results) that BrokeBuy uses to make decisions, but they don't control core functionality.

### 2. Research Independence

The Major Project is **research-oriented**. This means:
- Models may change frequently during research
- Experiments may require different architectures
- Evaluation may require A/B testing different approaches
- Research code should not break production systems

**Solution**: Research modules are isolated and communicate through well-defined interfaces (contracts), not direct code dependencies.

### 3. Deployment Flexibility

Research modules can be:
- **Enabled/Disabled**: BrokeBuy can operate without them (graceful degradation)
- **Versioned**: Different versions can be tested simultaneously
- **Replaced**: Alternative implementations can be swapped in
- **Scaled Independently**: Modules can be deployed as separate services

---

## Integration Architecture

### Current Architecture (Skeleton Phase)

```
┌─────────────────────────────────────────────────────────┐
│                    BrokeBuy Backend                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Routes     │  │   Models    │  │   Utils      │   │
│  │  (FastAPI)   │  │  (MongoDB)  │  │  (Business)  │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         │                 │                 │            │
│         └─────────────────┼─────────────────┘            │
│                           │                               │
└───────────────────────────┼───────────────────────────────┘
                            │
                            │ (Calls via Interface)
                            │
┌───────────────────────────┼───────────────────────────────┐
│                    Major Project                          │
│  ┌──────────────────┐      ┌──────────────────┐          │
│  │   fraud_gnn/     │      │  face_privacy/   │          │
│  │                  │      │                  │          │
│  │  - Graph Builder │      │  - Face Verifier │          │
│  │  - Risk Scoring  │      │  - Embeddings    │          │
│  │  - GNN Models    │      │  - Federated     │          │
│  └──────────────────┘      └──────────────────┘          │
└─────────────────────────────────────────────────────────┘
```

### Future Architecture (API Boundary)

```
┌─────────────────────────────────────────────────────────┐
│                    BrokeBuy Backend                      │
│                                                           │
│  POST /listings/create                                   │
│    → Calls fraud_gnn API → Gets risk_score              │
│    → If risk_score > 0.8: Require approval              │
│    → Else: Create listing                                │
│                                                           │
│  POST /auth/verify-face                                  │
│    → Calls face_privacy API → Gets verification_result   │
│    → If verified: Allow access                           │
│    → Else: Reject                                        │
└─────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/gRPC
                            │
┌───────────────────────────┼───────────────────────────────┐
│         Major Project APIs (Future)                       │
│                                                           │
│  POST /major-project/fraud-gnn/risk-score                │
│  POST /major-project/face-privacy/verify                  │
└─────────────────────────────────────────────────────────┘
```

---

## How Models Behave Like External Trust & Safety Engine

### 1. Stateless Service Model

Research modules operate as **stateless services**:
- Each request is independent
- No shared state between requests
- Can be scaled horizontally
- Can be replaced without affecting other components

### 2. Contract-Based Communication

Communication happens through **well-defined contracts**:

**Fraud Detection Contract** (`fraud_gnn/risk_contract.md`):
```python
# Input: GraphSnapshot
# Output: RiskScore (0-1)
risk_score = compute_risk_score(graph_snapshot, entity_id, entity_type)
```

**Face Verification Contract** (`face_privacy/embedding_contract.md`):
```python
# Input: FaceEmbedding, FaceEmbedding
# Output: VerificationResult
result = verify(embedding_1, embedding_2, threshold=0.8)
```

### 3. Advisory Role

Research modules provide **advisory information**, not commands:

```python
# BrokeBuy makes the decision, modules provide input
risk_score = fraud_gnn.get_risk_score(user_id)  # Advisory

if risk_score > 0.8:
    # BrokeBuy decides what to do
    require_verification(user_id)  # BrokeBuy action
    apply_rate_limits(user_id)     # BrokeBuy action
```

**Key Point**: Modules don't directly modify BrokeBuy state. They provide information that BrokeBuy uses to make decisions.

---

## API Boundaries (Future Implementation)

### Where API Boundaries Will Exist

While no API endpoints are implemented yet, the future integration will use these boundaries:

#### 1. Fraud Detection API

**Endpoint**: `POST /major-project/fraud-gnn/risk-score`

**Request**:
```json
{
  "entity_id": "user_123",
  "entity_type": "user",
  "graph_snapshot_id": "snapshot_2024_01_15"
}
```

**Response**:
```json
{
  "risk_score": 0.73,
  "risk_level": "high",
  "factors": ["new_account", "device_sharing", "suspicious_network"],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**BrokeBuy Usage**:
```python
# In listings route
risk_response = call_fraud_api(entity_id=user_id, entity_type="user")
if risk_response["risk_score"] > 0.8:
    raise HTTPException(403, "Account verification required")
```

#### 2. Face Verification API

**Endpoint**: `POST /major-project/face-privacy/verify`

**Request**:
```json
{
  "embedding_1": [0.123, -0.456, ...],
  "embedding_2": [0.789, -0.012, ...],
  "threshold": 0.8,
  "context": "login"
}
```

**Response**:
```json
{
  "is_match": true,
  "similarity_score": 0.92,
  "confidence": 0.12,
  "model_version": "facenet_v1"
}
```

**BrokeBuy Usage**:
```python
# In auth route
verification = call_face_api(embedding_1, embedding_2)
if not verification["is_match"]:
    raise HTTPException(401, "Face verification failed")
```

---

## Data Flow

### Fraud Detection Flow

```
1. BrokeBuy Event (e.g., user creates listing)
   ↓
2. BrokeBuy builds GraphSnapshot from database
   ↓
3. BrokeBuy calls fraud_gnn.get_risk_score(graph_snapshot, user_id)
   ↓
4. fraud_gnn returns risk_score (0-1)
   ↓
5. BrokeBuy makes decision based on risk_score
   - If risk_score > 0.8: Require verification
   - If risk_score > 0.6: Apply rate limits
   - Else: Allow operation
```

### Face Verification Flow

```
1. User uploads face image for verification
   ↓
2. BrokeBuy extracts embedding using face_privacy.generate_embedding()
   ↓
3. BrokeBuy retrieves stored embedding from database
   ↓
4. BrokeBuy calls face_privacy.verify(embedding_1, embedding_2)
   ↓
5. face_privacy returns VerificationResult
   ↓
6. BrokeBuy makes decision based on result
   - If is_match: Allow access
   - Else: Reject verification
```

---

## Graceful Degradation

### What Happens If Modules Are Unavailable?

**Fraud Detection**:
- If fraud_gnn is unavailable: BrokeBuy operates with default risk scores (0.5)
- Basic rate limiting still applies
- Manual review may be required for suspicious cases

**Face Verification**:
- If face_privacy is unavailable: Fall back to alternative verification (email, phone)
- Users can still access the platform
- High-security operations may be temporarily restricted

**Key Point**: BrokeBuy can operate independently. Research modules enhance security but are not required for core functionality.

---

## Development Workflow

### Phase 1: Skeleton (Current)
- ✅ Define contracts and interfaces
- ✅ Create stub implementations
- ✅ Document integration points
- ❌ No actual API calls yet

### Phase 2: Implementation
- Implement actual models and algorithms
- Create internal functions (not APIs yet)
- Test with BrokeBuy data
- Validate contracts

### Phase 3: API Integration
- Create API endpoints for research modules
- Integrate with BrokeBuy routes
- Add error handling and fallbacks
- Deploy as separate services (optional)

### Phase 4: Production
- Monitor performance and accuracy
- A/B test different models
- Iterate based on results
- Scale independently

---

## Key Takeaways

1. **Loose Coupling**: Research modules are independent services, not tightly integrated code
2. **Contract-Based**: Communication happens through well-defined contracts
3. **Advisory Role**: Modules provide information, BrokeBuy makes decisions
4. **Graceful Degradation**: BrokeBuy can operate without research modules
5. **Future APIs**: Integration will happen through API boundaries, not direct code dependencies
6. **Research Independence**: Research can evolve without breaking BrokeBuy

---

**Last Updated**: [Date]  
**Status**: Architecture & Integration Design Complete

