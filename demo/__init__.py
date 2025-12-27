"""
DEMO ONLY – NOT FOR PRODUCTION

Demo package for project review demonstrations.

This package contains demo-only functionality that:
- Is completely isolated from production code
- Does not affect core logic or ML training
- Only works when DEMO_MODE=True in configuration
- Uses simulated/mock data for demonstrations

IMPORTANT: This code should NEVER be used in production or research pipelines.
"""

from .fraud_simulation import compute_demo_risk_score, get_demo_risk_category

__all__ = [
    'compute_demo_risk_score',
    'get_demo_risk_category',
]

