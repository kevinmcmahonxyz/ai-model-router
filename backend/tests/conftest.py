"""Pytest configuration and fixtures."""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import uuid
import os

from src.main import app
from src.models.database import Base, get_db
from src.models.schemas import User, Provider, Model, Request


# Use test PostgreSQL database
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://router_user:router_password@localhost:5433/router_test_db"
)

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db):
    """Create a test user."""
    user = User(
        id=uuid.uuid4(),
        api_key="test_api_key_12345",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_provider(db):
    """Create a test provider."""
    provider = Provider(
        name="openai",
        base_url="https://api.openai.com/v1",
        is_active=True
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return provider


@pytest.fixture
def test_models(db, test_provider):
    """Create test models."""
    models = [
        Model(
            provider_id=test_provider.id,
            model_id="gpt-4o-mini",
            display_name="GPT-4o Mini",
            input_price_per_1m_tokens=0.15,
            output_price_per_1m_tokens=0.60,
            context_window=128000,
            is_active=True
        ),
        Model(
            provider_id=test_provider.id,
            model_id="gpt-4o",
            display_name="GPT-4o",
            input_price_per_1m_tokens=2.50,
            output_price_per_1m_tokens=10.00,
            context_window=128000,
            is_active=True
        )
    ]
    for model in models:
        db.add(model)
    db.commit()
    for model in models:
        db.refresh(model)
    return models


@pytest.fixture
def test_requests(db, test_user, test_provider, test_models):
    """Create test requests with varied data."""
    requests = []
    
    # Create 10 requests over the last 30 days
    for i in range(10):
        model = test_models[i % 2]  # Alternate between models
        days_ago = i * 3  # Spread over 30 days
        created_at = datetime.utcnow() - timedelta(days=days_ago)
        
        input_tokens = 50 + (i * 10)
        output_tokens = 100 + (i * 20)
        input_cost = (input_tokens / 1_000_000) * model.input_price_per_1m_tokens
        output_cost = (output_tokens / 1_000_000) * model.output_price_per_1m_tokens
        
        status = "success" if i < 9 else "error"  # One error
        
        req = Request(
            id=uuid.uuid4(),
            user_id=test_user.id,
            model_id=model.id,
            provider_id=test_provider.id,
            prompt_text=f"Test prompt {i}",
            response_text=f"Test response {i}" if status == "success" else None,
            input_tokens=input_tokens if status == "success" else None,
            output_tokens=output_tokens if status == "success" else None,
            total_tokens=input_tokens + output_tokens if status == "success" else None,
            input_cost_usd=round(input_cost, 8) if status == "success" else None,
            output_cost_usd=round(output_cost, 8) if status == "success" else None,
            total_cost_usd=round(input_cost + output_cost, 8) if status == "success" else None,
            latency_ms=1000 + (i * 100),
            status=status,
            error_message="Test error" if status == "error" else None,
            created_at=created_at,
            completed_at=created_at
        )
        db.add(req)
        requests.append(req)
    
    db.commit()
    for req in requests:
        db.refresh(req)
    return requests


@pytest.fixture
def auth_headers(test_user):
    """Return authentication headers for test user."""
    return {"X-API-Key": test_user.api_key}