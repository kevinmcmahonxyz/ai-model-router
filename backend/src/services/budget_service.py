"""Budget enforcement service."""
from typing import Optional, Dict
from sqlalchemy.orm import Session

from src.models.schemas import User


class BudgetService:
    """Manage user spending limits and budget enforcement."""
    
    def __init__(self, db: Session):
        """
        Initialize budget service.
        
        Args:
            db: SQLAlchemy session
        """
        self.db = db
    
    def get_user_spending(self, user_id) -> Dict[str, float]:
        """
        Get current spending for a user.
        
        Args:
            user_id: User UUID
        
        Returns:
            Dict with spending info
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return {
                "total_spent": 0.0,
                "spending_limit": None,
                "remaining_budget": None,
                "budget_used_percentage": 0.0
            }
        
        total_spent = user.total_spent_usd or 0.0
        spending_limit = user.spending_limit_usd
        
        remaining_budget = None
        budget_used_percentage = 0.0
        
        if spending_limit is not None:
            remaining_budget = max(0, spending_limit - total_spent)
            budget_used_percentage = (total_spent / spending_limit * 100) if spending_limit > 0 else 0.0
        
        return {
            "total_spent_usd": round(total_spent, 6),
            "spending_limit_usd": spending_limit,
            "remaining_budget_usd": round(remaining_budget, 6) if remaining_budget is not None else None,
            "budget_used_percentage": round(budget_used_percentage, 2)
        }
    
    def check_budget(self, user_id, estimated_cost: float) -> Dict[str, any]:
        """
        Check if user can afford a request.
        
        Args:
            user_id: User UUID
            estimated_cost: Estimated cost in USD
        
        Returns:
            Dict with approval status and details
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return {
                "approved": False,
                "reason": "User not found"
            }
        
        # No spending limit = unlimited budget
        if user.spending_limit_usd is None:
            return {
                "approved": True,
                "reason": "No spending limit set"
            }
        
        total_spent = user.total_spent_usd or 0.0
        spending_limit = user.spending_limit_usd
        
        # Check if this request would exceed budget
        would_exceed = (total_spent + estimated_cost) > spending_limit
        
        if would_exceed:
            remaining = max(0, spending_limit - total_spent)
            return {
                "approved": False,
                "reason": "Budget exceeded",
                "total_spent_usd": round(total_spent, 6),
                "spending_limit_usd": spending_limit,
                "remaining_budget_usd": round(remaining, 6),
                "estimated_cost_usd": round(estimated_cost, 6),
                "would_exceed_by_usd": round((total_spent + estimated_cost) - spending_limit, 6)
            }
        
        return {
            "approved": True,
            "reason": "Within budget",
            "total_spent_usd": round(total_spent, 6),
            "spending_limit_usd": spending_limit,
            "remaining_budget_usd": round(spending_limit - total_spent, 6)
        }
    
    def update_spending(self, user_id, cost: float) -> None:
        """
        Update user's total spending after a request.
        
        Args:
            user_id: User UUID
            cost: Actual cost in USD
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if user:
            user.total_spent_usd = (user.total_spent_usd or 0.0) + cost
            self.db.commit()
    
    def set_spending_limit(self, user_id, limit_usd: Optional[float]) -> None:
        """
        Set spending limit for a user.
        
        Args:
            user_id: User UUID
            limit_usd: Spending limit in USD (None = unlimited)
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if user:
            user.spending_limit_usd = limit_usd
            self.db.commit()
    
    def reset_spending(self, user_id) -> None:
        """
        Reset user's spending counter to zero.
        
        Args:
            user_id: User UUID
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if user:
            user.total_spent_usd = 0.0
            self.db.commit()