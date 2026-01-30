"""Test configuration and fixtures"""
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.main import app
from app.models.documents import User, Holding, Alert


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db():
    """Initialize test database"""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    await init_beanie(
        database=client.stockpilot_test,
        document_models=[User, Holding, Alert]
    )
    yield client.stockpilot_test
    await client.drop_database("stockpilot_test")


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for testing"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def test_user_data():
    return {"email": "test@example.com", "password": "testpass123", "name": "Test User"}
