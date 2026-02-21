# 🛡️ Threat Model

## Overview

This document defines the attacker models and threats that the Major Project aims to mitigate. It maps each threat to the module(s) that address it and explains the defense mechanisms.

## Attacker Models

### 1. Spam Account Attacker

**Description**: An attacker creates multiple accounts to post spam listings, send spam messages, or manipulate the marketplace.

**Capabilities**:
- Create multiple accounts with fake credentials
- Post many listings quickly
- Send bulk messages to users
- Use automation tools (bots) for account creation and posting

**Goals**:
- Flood marketplace with spam listings
- Send unsolicited messages to users
- Manipulate search results or trending items
- Waste platform resources

**Mitigation Module**: `fraud_gnn/`

**Defense Mechanisms**:
- **Graph-based Detection**: Detect accounts with unusual activity patterns (high listing rate, high message rate)
- **Network Analysis**: Identify accounts that are isolated or have suspicious connection patterns
- **Device Fingerprinting**: Detect multiple accounts from the same device
- **Rate Limiting**: Apply stricter rate limits based on risk scores

**Detection Signals**:
- High listings_per_day ratio
- High messages_per_day ratio
- Isolated accounts (few connections)
- Multiple accounts sharing same device
- Suspicious message patterns (bulk messaging)

---

### 2. Sybil Attack Attacker

**Description**: An attacker creates multiple fake accounts that interact with each other to build fake credibility, manipulate reviews, or create fake transactions.

**Capabilities**:
- Create many coordinated accounts
- Make accounts interact with each other (messages, transactions, reviews)
- Build fake reputation through fake interactions
- Coordinate attacks across multiple accounts

**Goals**:
- Build fake credibility for accounts
- Manipulate listing popularity through fake views/transactions
- Create fake positive reviews
- Evade detection by appearing legitimate individually

**Mitigation Module**: `fraud_gnn/`

**Defense Mechanisms**:
- **Device Node Analysis**: Detect multiple accounts sharing the same device
- **Network Structure Analysis**: Identify circular interaction patterns (A → B → C → A)
- **Graph Neural Networks**: Learn patterns of coordinated account behavior
- **Subgraph Analysis**: Analyze neighborhoods to detect Sybil clusters

**Detection Signals**:
- Multiple users sharing same device (DeviceNode.user_count > threshold)
- Circular message/transaction patterns
- Accounts with high mutual connections but low external connections
- Suspicious device sharing patterns

---

### 3. Identity Spoofing Attacker

**Description**: An attacker attempts to impersonate another user by using their photos or creating fake accounts with stolen identities.

**Capabilities**:
- Use photos of other people (stolen from social media, etc.)
- Create accounts with fake identities
- Attempt to verify using someone else's face
- Use deepfake or manipulated images

**Goals**:
- Impersonate legitimate users
- Gain access to accounts through identity verification
- Create accounts with fake identities
- Evade identity verification checks

**Mitigation Module**: `face_privacy/`

**Defense Mechanisms**:
- **Face Embedding Verification**: Compare face embeddings to detect impersonation
- **Liveness Detection**: Detect if face is from a photo/video (future enhancement)
- **Similarity Thresholds**: Use strict thresholds to prevent false matches
- **Multi-factor Authentication**: Combine face verification with other factors

**Detection Signals**:
- Low similarity score between claimed identity and verification image
- Mismatch between stored embedding and new verification attempt
- Suspicious verification patterns (multiple failed attempts)

---

### 4. Collusion Network Attacker

**Description**: A group of attackers coordinate to manipulate the marketplace through fake transactions, price manipulation, or review manipulation.

**Capabilities**:
- Coordinate multiple accounts
- Create fake transactions between accounts
- Manipulate prices through coordinated buying/selling
- Create fake positive reviews

**Goals**:
- Manipulate listing prices
- Create fake transaction history
- Build fake reputation through coordinated actions
- Evade individual account detection

**Mitigation Module**: `fraud_gnn/`

**Defense Mechanisms**:
- **Graph Structure Analysis**: Detect clusters of accounts with suspicious interaction patterns
- **Transaction Pattern Analysis**: Identify circular or suspicious transaction patterns
- **Network Community Detection**: Identify tightly-knit groups of accounts
- **Economic Pattern Analysis**: Detect price manipulation through transaction analysis

**Detection Signals**:
- Circular transaction patterns (A buys from B, B buys from C, C buys from A)
- Tightly connected account clusters with few external connections
- Unusual pricing patterns in transactions
- High transaction rate between specific account groups

---

### 5. Data Privacy Attacker

**Description**: An attacker (internal or external) attempts to extract sensitive user data, particularly face images or biometric data.

**Capabilities**:
- Access to database (through breach or insider threat)
- Attempt to reverse-engineer embeddings to reconstruct faces
- Use embeddings for cross-platform tracking
- Extract demographic information from embeddings

**Goals**:
- Steal user face images
- Track users across platforms
- Extract sensitive biometric data
- Violate user privacy

**Mitigation Module**: `face_privacy/`

**Defense Mechanisms**:
- **Embedding Storage**: Store only embeddings, not raw images
- **Irreversible Embeddings**: Use embeddings that cannot be reverse-engineered
- **Privacy-Preserving Verification**: Verify without exposing raw images
- **Access Controls**: Limit access to embeddings with proper authentication

**Detection Signals**:
- Unauthorized access attempts to embedding database
- Unusual query patterns on embeddings
- Attempts to extract large numbers of embeddings

---

### 6. Model Poisoning Attacker (Federated Learning)

**Description**: In a federated learning scenario, a malicious client attempts to poison the global model by sending malicious model updates.

**Capabilities**:
- Control one or more client devices
- Send malicious model updates
- Attempt to degrade model accuracy
- Introduce backdoors in the model

**Goals**:
- Degrade fraud detection accuracy
- Introduce vulnerabilities in face verification
- Make the model accept specific attack patterns
- Compromise the global model

**Mitigation Module**: `face_privacy/` (federated learning component)

**Defense Mechanisms**:
- **Secure Aggregation**: Use cryptographic protocols to aggregate updates securely
- **Anomaly Detection**: Detect and filter out malicious model updates
- **Differential Privacy**: Add noise to updates to prevent poisoning
- **Robust Aggregation**: Use robust aggregation algorithms (median, trimmed mean)

**Detection Signals**:
- Model updates that significantly deviate from expected distribution
- Sudden degradation in model accuracy
- Unusual update patterns from specific clients

---

## Threat Mapping to Modules

### Fraud Detection Module (`fraud_gnn/`)

| Threat | Detection Method | Risk Score Impact |
|--------|------------------|-------------------|
| Spam Accounts | Activity pattern analysis, rate limiting | High risk score → Rate limits applied |
| Sybil Attacks | Device sharing, network structure analysis | High risk score → Account verification required |
| Collusion Networks | Graph community detection, transaction pattern analysis | High risk score → Transaction blocking |
| Price Manipulation | Economic pattern analysis | High risk score → Listing moderation |

### Face Privacy Module (`face_privacy/`)

| Threat | Detection Method | Mitigation |
|--------|------------------|------------|
| Identity Spoofing | Face embedding verification, similarity thresholds | Low similarity → Verification rejected |
| Data Privacy | Embedding storage (not raw images) | Embeddings cannot be reverse-engineered |
| Model Poisoning | Secure aggregation, anomaly detection | Malicious updates filtered out |

---

## Attack Scenarios

### Scenario 1: Coordinated Spam Attack

**Attack**: Attacker creates 100 accounts from 10 devices, posts 1000 spam listings in one day.

**Detection**:
- Device nodes show 10 users per device (suspicious)
- User nodes show high listings_per_day ratio
- Graph structure shows isolated accounts with few connections
- Risk scores > 0.8 for all accounts

**Response**:
- Rate limit all accounts (max 2 listings per day)
- Require verification for accounts with risk > 0.7
- Block accounts with risk > 0.9

---

### Scenario 2: Sybil Reputation Building

**Attack**: Attacker creates 20 accounts, makes them interact with each other to build fake reputation.

**Detection**:
- Device sharing detected (multiple accounts per device)
- Circular message/transaction patterns
- Tightly connected cluster with few external connections
- Risk scores > 0.7 for cluster

**Response**:
- Flag all accounts in cluster for review
- Require additional verification
- Monitor cluster for suspicious activity

---

### Scenario 3: Identity Impersonation

**Attack**: Attacker attempts to verify using someone else's photo.

**Detection**:
- Face embedding similarity < threshold (e.g., 0.8)
- Verification fails

**Response**:
- Reject verification
- Flag account for manual review
- Require additional identity verification

---

### Scenario 4: Database Breach

**Attack**: Attacker gains access to database and attempts to extract face images.

**Mitigation**:
- Only embeddings are stored, not raw images
- Embeddings cannot be reverse-engineered to reconstruct faces
- Access controls limit who can access embeddings

**Impact**: Minimal - attacker cannot reconstruct original faces from embeddings.

---

## Defense-in-Depth Strategy

### Layer 1: Prevention
- Strong authentication and access controls
- Input validation and sanitization
- Rate limiting and throttling

### Layer 2: Detection
- Graph-based fraud detection (fraud_gnn)
- Face verification (face_privacy)
- Anomaly detection and monitoring

### Layer 3: Response
- Automated actions (rate limiting, blocking)
- Manual review for high-risk cases
- User notification and appeal process

### Layer 4: Recovery
- Account recovery procedures
- Data breach response plan
- Model retraining after attacks

---

## Assumptions and Limitations

### Assumptions

1. **Attacker Capabilities**: Attackers have standard capabilities (can create accounts, post content, etc.) but cannot compromise the platform infrastructure itself.

2. **Data Availability**: We have access to user behavior data (listings, messages, transactions) and can build graphs from this data.

3. **Model Accuracy**: GNN models and face verification models achieve acceptable accuracy (>90% for fraud detection, >99% for face verification).

### Limitations

1. **False Positives**: Some legitimate users may be flagged as fraudulent (target: <5% false positive rate).

2. **Adaptive Attackers**: Sophisticated attackers may adapt to detection methods over time, requiring model updates.

3. **Privacy Trade-offs**: Some privacy-preserving techniques may slightly reduce accuracy.

4. **Scalability**: Very large graphs (>100,000 nodes) may require optimization or sampling.

---

**Last Updated**: [Date]  
**Status**: Threat Model Definition Complete

