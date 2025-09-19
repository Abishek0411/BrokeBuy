#!/usr/bin/env python3
"""
Test script to verify local MongoDB connection and data
"""

import asyncio
import motor.motor_asyncio
from dotenv import load_dotenv
import os

load_dotenv()

async def test_mongodb():
    try:
        # Create new client for testing
        client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGO_URI"))
        db = client["brokebuy"]
        
        # Test connection
        await client.admin.command('ping')
        print("✅ MongoDB connection successful")
        
        # List collections
        collections = await db.list_collection_names()
        print(f"✅ Collections found: {collections}")
        
        # Test each collection
        for collection_name in collections:
            collection = db[collection_name]
            count = await collection.count_documents({})
            print(f"✅ {collection_name}: {count} documents")
        
        # Test a sample query
        users = await db.users.find_one()
        if users:
            print(f"✅ Sample user found: {users.get('username', 'No username')}")
        
        print("\n🎉 All tests passed! Local MongoDB is working correctly.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_mongodb())
