"""SQLAlchemy models for database tables."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    """Users table - tracks API key holders."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    api_key = Column(String(64), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    spending_limit_usd = Column(Float, nullable=True)
    total_spent_usd = Column(Float, nullable=False, default=0.0)
    comparisons = relationship("Comparison", back_populates="user")
    
    # Relationships
    requests = relationship("Request", back_populates="user")


class Provider(Base):
    """LLM providers (OpenAI, Anthropic, etc.)."""
    __tablename__ = "providers"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    base_url = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    models = relationship("Model", back_populates="provider")
    requests = relationship("Request", back_populates="provider")


class Model(Base):
    """LLM models with pricing information."""
    __tablename__ = "models"
    
    id = Column(Integer, primary_key=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    model_id = Column(String(100), nullable=False)
    display_name = Column(String(100))
    input_price_per_1m_tokens = Column(Float, nullable=False)
    output_price_per_1m_tokens = Column(Float, nullable=False)
    context_window = Column(Integer)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    provider = relationship("Provider", back_populates="models")
    requests = relationship("Request", back_populates="model")

class Comparison(Base):
    """Comparison of multiple models on the same prompt."""
    __tablename__ = "comparisons"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    prompt_text = Column(Text, nullable=False)
    models_used = Column(JSON, nullable=False)  # List of model IDs
    total_cost_usd = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="comparisons")
    requests = relationship("Request", back_populates="comparison")


class Request(Base):
    """Log of all LLM requests and responses."""
    __tablename__ = "requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    comparison_id = Column(UUID(as_uuid=True), ForeignKey("comparisons.id"), nullable=True)
    comparison = relationship("Comparison", back_populates="requests")
    
    # Request/Response content
    prompt_text = Column(Text, nullable=False)
    response_text = Column(Text)
    
    # Token usage
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    total_tokens = Column(Integer)
    
    # Cost tracking
    input_cost_usd = Column(Float)
    output_cost_usd = Column(Float)
    total_cost_usd = Column(Float)
    
    # Performance
    latency_ms = Column(Integer)
    
    # Status
    status = Column(String(20), nullable=False)
    error_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="requests")
    model = relationship("Model", back_populates="requests")
    provider = relationship("Provider", back_populates="requests")