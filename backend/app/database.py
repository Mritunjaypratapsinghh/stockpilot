from motor.motor_asyncio import AsyncIOMotorClient
from .config import get_settings

settings = get_settings()

client: AsyncIOMotorClient = None
db = None

async def connect_db():
    global client, db
    try:
        client = AsyncIOMotorClient(settings.mongodb_uri, serverSelectionTimeoutMS=10000)
        db = client[settings.mongodb_db]
        # Test connection
        await client.admin.command('ping')
        # Create indexes
        await db.holdings.create_index([("user_id", 1), ("symbol", 1)])
        await db.alerts.create_index([("user_id", 1), ("is_active", 1)])
        print(f"✅ Connected to MongoDB: {settings.mongodb_db}")
    except Exception as e:
        print(f"⚠️ MongoDB connection failed: {e}")
        print("⚠️ Running without database - some features won't work")
        # Don't raise - allow app to start for testing

async def close_db():
    global client
    if client:
        client.close()
        print("MongoDB connection closed")

def get_db():
    return db
