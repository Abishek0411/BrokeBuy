import asyncio
import nest_asyncio
from app.database import db
from datetime import datetime
from bson import ObjectId

nest_asyncio.apply()

async def migrate_transactions_to_wallet_history():
    transactions = await db.transactions.find({}).to_list(length=None)

    if not transactions:
        print("No transactions found to migrate.")
        return

    count = 0
    for txn in transactions:
        try:
            migrated_doc = {
                "user_id": txn["user_id"] if isinstance(txn["user_id"], ObjectId) else ObjectId(txn["user_id"]),
                "type": txn.get("type", "credit"),
                "amount": txn["amount"],
                "ref_note": txn.get("ref_note", "Top-up"),
                "timestamp": txn.get("timestamp", datetime.utcnow())
            }

            await db.wallet_history.insert_one(migrated_doc)
            count += 1

        except Exception as e:
            print(f"Failed to migrate txn {txn.get('_id')}: {e}")

    print(f"✅ Migrated {count} transactions.")

    if count > 0:
        await db.transactions.drop()
        print("✅ Dropped 'transactions' collection.")
    else:
        print("⚠️ Nothing was migrated. Transactions collection kept intact.")

if __name__ == "__main__":
    asyncio.run(migrate_transactions_to_wallet_history())
