from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime

# --- CONFIG ---
MONGO_URI = "mongodb+srv://abishekram0411:Dt1Fcyqxbkz0yFu7@cluster0.gab1psq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"  # Change this to your actual DB connection
DB_NAME = "brokebuy"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

def create_notifications_collection():
    if "notifications" not in db.list_collection_names():
        db.create_collection("notifications")
        print("✅ Created 'notifications' collection.")
    else:
        print("ℹ️ 'notifications' collection already exists.")

    # Indexes for notifications
    db.notifications.create_index([("user_id", ASCENDING), ("is_read", ASCENDING)])
    db.notifications.create_index([("timestamp", DESCENDING)])
    print("✅ Indexes added to 'notifications' collection.")


def create_buy_requests_indexes():
    # Ensure indexes on listings for buy requests
    db.listings.create_index([("buy_requests.buyer_id", ASCENDING)])
    db.listings.create_index([("buy_requests.status", ASCENDING)])
    print("✅ Indexes added to 'listings' for buy requests.")


def run_migration():
    print("🚀 Starting migration...")

    create_notifications_collection()
    create_buy_requests_indexes()

    print("🎉 Migration completed successfully!")


if __name__ == "__main__":
    run_migration()
