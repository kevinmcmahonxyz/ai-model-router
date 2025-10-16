"""Seed initial data into database."""
import sys
from pathlib import Path

# Add parent directory to path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session
from src.models.database import SessionLocal
from src.models.schemas import Provider, Model


def seed_providers_and_models():
    """Add providers and models to database."""
    db: Session = SessionLocal()
    
    try:
        # ============================================================
        # OPENAI PROVIDER
        # ============================================================
        openai_provider = db.query(Provider).filter(Provider.name == "openai").first()
        
        if not openai_provider:
            openai_provider = Provider(
                name="openai",
                base_url="https://api.openai.com/v1",
                is_active=True
            )
            db.add(openai_provider)
            db.commit()
            db.refresh(openai_provider)
            print(f"✓ Created provider: {openai_provider.name}")
        else:
            print(f"✓ Provider already exists: {openai_provider.name}")
        
        # OpenAI models with current pricing (as of Jan 2025)
        openai_models = [
            {
                "model_id": "gpt-4o",
                "display_name": "GPT-4o",
                "input_price": 2.50,
                "output_price": 10.00,
                "context_window": 128000
            },
            {
                "model_id": "gpt-4o-mini",
                "display_name": "GPT-4o Mini",
                "input_price": 0.15,
                "output_price": 0.60,
                "context_window": 128000
            },
            {
                "model_id": "gpt-3.5-turbo",
                "display_name": "GPT-3.5 Turbo",
                "input_price": 0.50,
                "output_price": 1.50,
                "context_window": 16385
            }
        ]
        
        for model_data in openai_models:
            existing_model = db.query(Model).filter(
                Model.provider_id == openai_provider.id,
                Model.model_id == model_data["model_id"]
            ).first()
            
            if not existing_model:
                model = Model(
                    provider_id=openai_provider.id,
                    model_id=model_data["model_id"],
                    display_name=model_data["display_name"],
                    input_price_per_1m_tokens=model_data["input_price"],
                    output_price_per_1m_tokens=model_data["output_price"],
                    context_window=model_data["context_window"],
                    is_active=True
                )
                db.add(model)
                print(f"  ✓ Created model: {model_data['model_id']}")
            else:
                print(f"  ✓ Model already exists: {model_data['model_id']}")
        
        # ============================================================
        # ANTHROPIC PROVIDER
        # ============================================================
        anthropic_provider = db.query(Provider).filter(Provider.name == "anthropic").first()
        
        if not anthropic_provider:
            anthropic_provider = Provider(
                name="anthropic",
                base_url="https://api.anthropic.com/v1",
                is_active=True
            )
            db.add(anthropic_provider)
            db.commit()
            db.refresh(anthropic_provider)
            print(f"✓ Created provider: {anthropic_provider.name}")
        else:
            print(f"✓ Provider already exists: {anthropic_provider.name}")
        
        # Anthropic models with current pricing (Oct 2025)
        anthropic_models = [
            {
                "model_id": "claude-opus-4-1-20250805",
                "display_name": "Claude Opus 4.1",
                "input_price": 15.00,
                "output_price": 75.00,
                "context_window": 200000
            },
            {
                "model_id": "claude-opus-4-20250514",
                "display_name": "Claude Opus 4",
                "input_price": 15.00,
                "output_price": 75.00,
                "context_window": 200000
            },
            {
                "model_id": "claude-sonnet-4-5-20250929",
                "display_name": "Claude Sonnet 4.5",
                "input_price": 3.00,
                "output_price": 15.00,
                "context_window": 200000
            },
            {
                "model_id": "claude-sonnet-4-20250514",
                "display_name": "Claude Sonnet 4",
                "input_price": 3.00,
                "output_price": 15.00,
                "context_window": 200000
            },
            {
                "model_id": "claude-3-5-haiku-20241022",
                "display_name": "Claude 3.5 Haiku",
                "input_price": 0.80,
                "output_price": 4.00,
                "context_window": 200000
            }
        ]
        
        for model_data in anthropic_models:
            existing_model = db.query(Model).filter(
                Model.provider_id == anthropic_provider.id,
                Model.model_id == model_data["model_id"]
            ).first()
            
            if not existing_model:
                model = Model(
                    provider_id=anthropic_provider.id,
                    model_id=model_data["model_id"],
                    display_name=model_data["display_name"],
                    input_price_per_1m_tokens=model_data["input_price"],
                    output_price_per_1m_tokens=model_data["output_price"],
                    context_window=model_data["context_window"],
                    is_active=True
                )
                db.add(model)
                print(f"  ✓ Created model: {model_data['model_id']}")
            else:
                print(f"  ✓ Model already exists: {model_data['model_id']}")
        
        # ============================================================
        # DEEPSEEK PROVIDER
        # ============================================================
        deepseek_provider = db.query(Provider).filter(Provider.name == "deepseek").first()
        
        if not deepseek_provider:
            deepseek_provider = Provider(
                name="deepseek",
                base_url="https://api.deepseek.com/v1",
                is_active=True
            )
            db.add(deepseek_provider)
            db.commit()
            db.refresh(deepseek_provider)
            print(f"✓ Created provider: {deepseek_provider.name}")
        else:
            print(f"✓ Provider already exists: {deepseek_provider.name}")
        
        # DeepSeek models with current pricing (Oct 2025)
        # Using cache-miss prices (worst case)
        deepseek_models = [
            {
                "model_id": "deepseek-chat",
                "display_name": "DeepSeek Chat",
                "input_price": 0.28,
                "output_price": 0.42,
                "context_window": 64000
            },
            {
                "model_id": "deepseek-reasoner",
                "display_name": "DeepSeek Reasoner",
                "input_price": 0.56,
                "output_price": 1.68,
                "context_window": 64000
            }
        ]
        
        for model_data in deepseek_models:
            existing_model = db.query(Model).filter(
                Model.provider_id == deepseek_provider.id,
                Model.model_id == model_data["model_id"]
            ).first()
            
            if not existing_model:
                model = Model(
                    provider_id=deepseek_provider.id,
                    model_id=model_data["model_id"],
                    display_name=model_data["display_name"],
                    input_price_per_1m_tokens=model_data["input_price"],
                    output_price_per_1m_tokens=model_data["output_price"],
                    context_window=model_data["context_window"],
                    is_active=True
                )
                db.add(model)
                print(f"  ✓ Created model: {model_data['model_id']}")
            else:
                print(f"  ✓ Model already exists: {model_data['model_id']}")
        
        # ============================================================
        # GOOGLE PROVIDER
        # ============================================================
        google_provider = db.query(Provider).filter(Provider.name == "google").first()
        
        if not google_provider:
            google_provider = Provider(
                name="google",
                base_url="https://generativelanguage.googleapis.com",
                is_active=True
            )
            db.add(google_provider)
            db.commit()
            db.refresh(google_provider)
            print(f"✓ Created provider: {google_provider.name}")
        else:
            print(f"✓ Provider already exists: {google_provider.name}")
        
        # Google Gemini models with current pricing (Oct 2025)
        google_models = [
            {
                "model_id": "gemini-2.5-pro",
                "display_name": "Gemini 2.5 Pro",
                "input_price": 1.25,
                "output_price": 10.00,
                "context_window": 200000
            },
            {
                "model_id": "gemini-2.5-flash",
                "display_name": "Gemini 2.5 Flash",
                "input_price": 0.30,
                "output_price": 2.50,
                "context_window": 1000000
            },
            {
                "model_id": "gemini-2.5-flash-lite",
                "display_name": "Gemini 2.5 Flash Lite",
                "input_price": 0.10,
                "output_price": 0.40,
                "context_window": 1000000
            },
            {
                "model_id": "gemini-2.0-flash",
                "display_name": "Gemini 2.0 Flash",
                "input_price": 0.10,
                "output_price": 0.40,
                "context_window": 1000000
            }
        ]
        
        for model_data in google_models:
            existing_model = db.query(Model).filter(
                Model.provider_id == google_provider.id,
                Model.model_id == model_data["model_id"]
            ).first()
            
            if not existing_model:
                model = Model(
                    provider_id=google_provider.id,
                    model_id=model_data["model_id"],
                    display_name=model_data["display_name"],
                    input_price_per_1m_tokens=model_data["input_price"],
                    output_price_per_1m_tokens=model_data["output_price"],
                    context_window=model_data["context_window"],
                    is_active=True
                )
                db.add(model)
                print(f"  ✓ Created model: {model_data['model_id']}")
            else:
                print(f"  ✓ Model already exists: {model_data['model_id']}")
        
        db.commit()
        print("\n✅ Seed data complete!")
        
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_providers_and_models()