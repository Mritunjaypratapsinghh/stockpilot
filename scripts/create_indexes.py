#!/usr/bin/env python3
"""
StockPilot Database Index Creation Script
Run this script to create all required indexes for optimal performance.

Usage:
    cd backend
    source venv/bin/activate
    python -m scripts.create_indexes
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB = os.getenv("MONGODB_DB", "stockpilot")

# Index definitions: (collection, index_fields, options)
INDEXES = [
    # Users collection
    ("users", [("email", 1)], {"unique": True}),
    ("users", [("settings.daily_digest", 1)], {}),
    ("users", [("settings.alerts_enabled", 1)], {}),
    ("users", [("settings.hourly_alerts", 1)], {}),
    
    # Holdings collection
    ("holdings", [("user_id", 1)], {}),
    ("holdings", [("user_id", 1), ("symbol", 1)], {"unique": True}),
    ("holdings", [("symbol", 1)], {}),
    
    # Alerts collection
    ("alerts", [("user_id", 1)], {}),
    ("alerts", [("user_id", 1), ("is_active", 1)], {}),
    ("alerts", [("is_active", 1), ("notification_sent", 1)], {}),
    ("alerts", [("alert_type", 1), ("is_active", 1)], {}),
    
    # Watchlist collection
    ("watchlist", [("user_id", 1)], {}),
    ("watchlist", [("user_id", 1), ("symbol", 1)], {"unique": True}),
    
    # Transactions collection
    ("transactions", [("user_id", 1)], {}),
    ("transactions", [("user_id", 1), ("date", -1)], {}),
    
    # Dividends collection
    ("dividends", [("user_id", 1)], {}),
    ("dividends", [("user_id", 1), ("ex_date", -1)], {}),
    
    # Goals collection
    ("goals", [("user_id", 1)], {}),
    
    # SIPs collection
    ("sips", [("user_id", 1)], {}),
    
    # Assets collection (for networth)
    ("assets", [("user_id", 1)], {}),
    
    # Networth history collection
    ("networth_history", [("user_id", 1), ("date", -1)], {}),
    ("networth_history", [("user_id", 1), ("date", 1)], {}),
    
    # Portfolio snapshots collection
    ("portfolio_snapshots", [("user_id", 1), ("date", -1)], {}),
    ("portfolio_snapshots", [("user_id", 1), ("date", 1)], {}),
    
    # Notifications collection
    ("notifications", [("user_id", 1), ("read", 1)], {}),
    ("notifications", [("user_id", 1), ("created_at", -1)], {}),
    
    # IPOs collection
    ("ipos", [("status", 1)], {}),
    ("ipos", [("status", 1), ("price_band.high", 1)], {}),
    ("ipos", [("dates.close", 1), ("status", 1)], {}),
    
    # Signal history collection
    ("signal_history", [("user_id", 1), ("date", 1)], {}),
    
    # Advisor history collection
    ("advisor_history", [("user_id", 1), ("date", 1)], {}),
    
    # Daily digest collection
    ("daily_digest", [("user_id", 1), ("date", -1)], {}),
    
    # Price cache collection
    ("price_cache", [("symbol", 1)], {}),
    ("price_cache", [("updated_at", 1)], {}),
]

async def create_indexes():
    if not MONGODB_URI:
        print("❌ MONGODB_URI not set in environment")
        return
    
    print(f"Connecting to MongoDB: {MONGODB_DB}")
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[MONGODB_DB]
    
    # Test connection
    await client.admin.command('ping')
    print("✅ Connected to MongoDB\n")
    
    created = 0
    skipped = 0
    errors = 0
    
    for collection_name, index_fields, options in INDEXES:
        try:
            collection = db[collection_name]
            index_name = await collection.create_index(index_fields, **options)
            print(f"✅ {collection_name}: {index_name}")
            created += 1
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                print(f"⏭️  {collection_name}: {index_fields} (already exists)")
                skipped += 1
            else:
                print(f"❌ {collection_name}: {index_fields} - {e}")
                errors += 1
    
    print(f"\n{'='*50}")
    print(f"Summary: {created} created, {skipped} skipped, {errors} errors")
    print(f"Total indexes: {created + skipped}")
    
    # List all indexes per collection
    print(f"\n{'='*50}")
    print("Current indexes by collection:\n")
    
    collections = await db.list_collection_names()
    for coll_name in sorted(collections):
        indexes = await db[coll_name].index_information()
        if len(indexes) > 1:  # More than just _id
            print(f"{coll_name}:")
            for idx_name, idx_info in indexes.items():
                if idx_name != "_id_":
                    print(f"  - {idx_name}: {idx_info.get('key')}")
    
    client.close()
    print("\n✅ Done!")

if __name__ == "__main__":
    asyncio.run(create_indexes())
