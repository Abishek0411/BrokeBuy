import os

# General environment flag
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()

# Scraper service base URL; default to local dev when not provided
SCRAPER_BASE_URL = os.getenv("SCRAPER_BASE_URL") or (
    "http://localhost:3001" if ENVIRONMENT != "docker" else "http://scraper:3001"
)

# Global toggle for safety/spam/abuse guards
SAFETY_GUARDS_ENABLED = os.getenv("SAFETY_GUARDS_ENABLED", "true").lower() == "true"

# DEMO ONLY – NOT FOR PRODUCTION
# Demo mode flag for project review demos
# Default: False - must be explicitly enabled for demos
# When enabled, demo routes will be accessible
# This flag should NEVER be True in production or research pipelines
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"


