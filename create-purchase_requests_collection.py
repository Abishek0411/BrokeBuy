from pymongo import MongoClient, ASCENDING, DESCENDING
from datetime import datetime

# --- CONFIG ---
MONGO_URI = "mongodb+srv://abishekram0411:Dt1Fcyqxbkz0yFu7@cluster0.gab1psq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"  # Change this to your actual DB connection
DB_NAME = "brokebuy"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

def create_purchase_requests_collection():
    if "purchase_requests" not in db.list_collection_names():
        db.create_collection("purchase_requests")
        print("✅ Created 'purchase_requests' collection.")
    else:
        print("ℹ️ 'purchase_requests' collection already exists.")

    # Indexes for purchase requests
    db.purchase_requests.create_index([("listing_id", ASCENDING)])
    db.purchase_requests.create_index([("buyer_id", ASCENDING)])
    db.purchase_requests.create_index([("seller_id", ASCENDING)])
    db.purchase_requests.create_index([("status", ASCENDING)])
    db.purchase_requests.create_index([("created_at", DESCENDING)])
    print("✅ Indexes added to 'purchase_requests' collection.")


def run_migration():
    print("🚀 Starting migration...")

    create_purchase_requests_collection

    print("🎉 Migration completed successfully!")


if __name__ == "__main__":
    run_migration()
