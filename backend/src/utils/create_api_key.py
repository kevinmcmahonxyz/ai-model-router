"""Create a test API key."""
import sys
import secrets
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.models.database import SessionLocal
from src.models.schemas import User


def create_test_user():
    """Create a test user with API key."""
    db = SessionLocal()
    
    try:
        # Generate random API key
        api_key = f"test_{secrets.token_urlsafe(32)}"
        
        user = User(
            api_key=api_key,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print(f"✅ Created test user")
        print(f"User ID: {user.id}")
        print(f"API Key: {api_key}")
        print(f"\n⚠️  Save this API key - you'll need it to test the API!")
        
        return api_key
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_test_user()