from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from fastapi import HTTPException
import asyncio
from .config import get_settings
from .logger import logger
from .models.documents import ALL_DOCUMENTS

settings = get_settings()

client: AsyncIOMotorClient = None
db = None

async def connect_db(max_retries: int = 3, retry_delay: int = 2):
    """Connect to MongoDB with retry logic and connection pooling"""
    global client, db
    
    for attempt in range(1, max_retries + 1):
        try:
            client = AsyncIOMotorClient(
                settings.mongodb_uri,
                serverSelectionTimeoutMS=10000,
                maxPoolSize=50,
                minPoolSize=5,
                maxIdleTimeMS=30000,
                retryWrites=True,
                retryReads=True
            )
            db = client[settings.mongodb_db]
            await client.admin.command('ping')
            
            # Initialize Beanie with all document models
            await init_beanie(database=db, document_models=ALL_DOCUMENTS)
            logger.info(f"✅ Connected to MongoDB: {settings.mongodb_db} (Beanie initialized)")
            return
        except Exception as e:
            logger.warning(f"MongoDB connection attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                await asyncio.sleep(retry_delay * attempt)
            else:
                logger.error("❌ MongoDB connection failed after all retries")
                raise RuntimeError(f"Database connection failed: {e}")

async def close_db():
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed")

def get_db():
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    return db
