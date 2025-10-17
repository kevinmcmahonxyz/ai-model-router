"""Generate test data for dashboard testing."""
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.models.database import SessionLocal
from src.models.schemas import Request, User, Model
import uuid


def generate_test_requests(num_requests: int = 50):
    """Generate random test requests."""
    db = SessionLocal()
    
    try:
        # Get test user
        user = db.query(User).first()
        if not user:
            print("❌ No user found. Run create_api_key.py first")
            return
        
        # Get available models
        models = db.query(Model).all()
        if not models:
            print("❌ No models found. Run seed_data.py first")
            return
        
        print(f"Generating {num_requests} test requests...")
        
        sample_prompts = [
            "Explain quantum computing in simple terms",
            "Write a Python function to sort a list",
            "What are the benefits of exercise?",
            "Summarize the history of the internet",
            "How does photosynthesis work?",
            "Write a haiku about coding",
            "What is the capital of France?",
            "Explain machine learning to a 5 year old",
            "Generate a random password",
            "What are best practices for REST APIs?"
        ]
        
        sample_responses = [
            "Here's a detailed explanation...",
            "Certainly! Here's the function...",
            "Exercise has many benefits including...",
            "The internet began in...",
            "Photosynthesis is the process..."
        ]
        
        for i in range(num_requests):
            # Random data
            model = random.choice(models)
            created_at = datetime.utcnow() - timedelta(days=random.randint(0, 29))
            input_tokens = random.randint(20, 200)
            output_tokens = random.randint(30, 300)
            latency_ms = random.randint(500, 3000)
            status = "success" if random.random() > 0.05 else "error"  # 95% success
            
            # Calculate cost
            input_cost = (input_tokens / 1_000_000) * model.input_price_per_1m_tokens
            output_cost = (output_tokens / 1_000_000) * model.output_price_per_1m_tokens
            total_cost = input_cost + output_cost
            
            req = Request(
                id=uuid.uuid4(),
                user_id=user.id,
                model_id=model.id,
                provider_id=model.provider_id,
                prompt_text=random.choice(sample_prompts),
                response_text=random.choice(sample_responses) if status == "success" else None,
                input_tokens=input_tokens if status == "success" else None,
                output_tokens=output_tokens if status == "success" else None,
                total_tokens=input_tokens + output_tokens if status == "success" else None,
                input_cost_usd=round(input_cost, 8) if status == "success" else None,
                output_cost_usd=round(output_cost, 8) if status == "success" else None,
                total_cost_usd=round(total_cost, 8) if status == "success" else None,
                latency_ms=latency_ms,
                status=status,
                error_message="Rate limit exceeded" if status == "error" else None,
                created_at=created_at,
                completed_at=created_at
            )
            db.add(req)
            
            if (i + 1) % 10 == 0:
                print(f"  Generated {i + 1}/{num_requests}...")
        
        db.commit()
        print(f"✅ Successfully generated {num_requests} test requests!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    generate_test_requests(50)