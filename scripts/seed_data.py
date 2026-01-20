import asyncio, os, hashlib, sys
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

async def seed():
    client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
    db = client[os.getenv("MONGODB_DB", "stockpilot")]
    
    user = await db.users.find_one({"email": "demo@stockpilot.com"})
    if not user:
        r = await db.users.insert_one({"email": "demo@stockpilot.com", "password_hash": hashlib.sha256("demo123".encode()).hexdigest(), "settings": {"alerts_enabled": True}})
        user_id = r.inserted_id
        print("✅ Created demo@stockpilot.com / demo123")
    else:
        user_id = user["_id"]
    
    for h in [{"symbol": "HDFCBANK", "name": "HDFC Bank", "quantity": 7, "avg_price": 996}, {"symbol": "RELIANCE", "name": "Reliance", "quantity": 5, "avg_price": 2450}]:
        if not await db.holdings.find_one({"user_id": user_id, "symbol": h["symbol"]}):
            await db.holdings.insert_one({**h, "user_id": user_id, "exchange": "NSE", "holding_type": "EQUITY", "transactions": []})
            print(f"✅ Added {h['symbol']}")
    
    client.close()
    print("🎉 Done!")

if __name__ == "__main__":
    asyncio.run(seed())
