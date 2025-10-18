"""Model selection service for cost optimization."""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from src.models.schemas import Model, Provider
from src.services.token_estimator import TokenEstimator


class ModelSelector:
    """Select optimal model based on cost and constraints."""
    
    def __init__(self, db: Session):
        """
        Initialize selector with database session.
        
        Args:
            db: SQLAlchemy session for querying models
        """
        self.db = db
        self.estimator = TokenEstimator()
    
    def get_cheapest_model(
        self,
        messages: List[Dict[str, str]],
        expected_output_tokens: int = 500,
        provider_filter: Optional[List[str]] = None,
        exclude_models: Optional[List[str]] = None
    ) -> Optional[Dict]:
        """
        Find the cheapest model for a given request.
        
        Args:
            messages: List of message dicts
            expected_output_tokens: Expected response length
            provider_filter: Optional list of provider names to consider
            exclude_models: Optional list of model IDs to exclude
        
        Returns:
            Dict with model info and cost estimate, or None if no models available
        """
        # Query active models with their providers
        query = self.db.query(Model, Provider).join(
            Provider, Model.provider_id == Provider.id
        ).filter(
            Model.is_active == True,
            Provider.is_active == True
        )
        
        # Apply provider filter if specified
        if provider_filter:
            query = query.filter(Provider.name.in_(provider_filter))
        
        # Apply model exclusion if specified
        if exclude_models:
            query = query.filter(~Model.model_id.in_(exclude_models))
        
        models = query.all()
        
        if not models:
            return None
        
        # Calculate estimated cost for each model
        model_costs = []
        
        for model, provider in models:
            cost_estimate = self.estimator.estimate_cost(
                messages=messages,
                model_id=model.model_id,
                input_price_per_1m=model.input_price_per_1m_tokens,
                output_price_per_1m=model.output_price_per_1m_tokens,
                expected_output_tokens=expected_output_tokens
            )
            
            model_costs.append({
                "model_id": model.model_id,
                "model_db_id": model.id,
                "display_name": model.display_name,
                "provider_name": provider.name,
                "provider_id": provider.id,
                "estimated_cost": cost_estimate["estimated_total_cost_usd"],
                "cost_breakdown": cost_estimate
            })
        
        # Sort by estimated cost (cheapest first)
        model_costs.sort(key=lambda x: x["estimated_cost"])
        
        return model_costs[0] if model_costs else None
    
    def get_ranked_models(
        self,
        messages: List[Dict[str, str]],
        expected_output_tokens: int = 500,
        provider_filter: Optional[List[str]] = None,
        max_cost: Optional[float] = None
    ) -> List[Dict]:
        """
        Get all models ranked by cost.
        
        Args:
            messages: List of message dicts
            expected_output_tokens: Expected response length
            provider_filter: Optional list of provider names
            max_cost: Optional maximum cost threshold in USD
        
        Returns:
            List of model dicts sorted by cost (cheapest first)
        """
        # Query active models
        query = self.db.query(Model, Provider).join(
            Provider, Model.provider_id == Provider.id
        ).filter(
            Model.is_active == True,
            Provider.is_active == True
        )
        
        if provider_filter:
            query = query.filter(Provider.name.in_(provider_filter))
        
        models = query.all()
        
        # Calculate costs
        model_costs = []
        
        for model, provider in models:
            cost_estimate = self.estimator.estimate_cost(
                messages=messages,
                model_id=model.model_id,
                input_price_per_1m=model.input_price_per_1m_tokens,
                output_price_per_1m=model.output_price_per_1m_tokens,
                expected_output_tokens=expected_output_tokens
            )
            
            estimated_cost = cost_estimate["estimated_total_cost_usd"]
            
            # Apply max cost filter
            if max_cost is not None and estimated_cost > max_cost:
                continue
            
            model_costs.append({
                "model_id": model.model_id,
                "model_db_id": model.id,
                "display_name": model.display_name,
                "provider_name": provider.name,
                "provider_id": provider.id,
                "estimated_cost": estimated_cost,
                "cost_breakdown": cost_estimate,
                "input_price_per_1m": model.input_price_per_1m_tokens,
                "output_price_per_1m": model.output_price_per_1m_tokens
            })
        
        # Sort by cost
        model_costs.sort(key=lambda x: x["estimated_cost"])
        
        return model_costs
    
    def get_model_comparison(
        self,
        messages: List[Dict[str, str]],
        expected_output_tokens: int = 500
    ) -> Dict:
        """
        Compare all available models for a request.
        
        Args:
            messages: List of message dicts
            expected_output_tokens: Expected response length
        
        Returns:
            Dict with comparison data
        """
        ranked = self.get_ranked_models(messages, expected_output_tokens)
        
        if not ranked:
            return {
                "total_models": 0,
                "cheapest": None,
                "most_expensive": None,
                "cost_range": None,
                "models": []
            }
        
        cheapest = ranked[0]
        most_expensive = ranked[-1]
        cost_range = most_expensive["estimated_cost"] - cheapest["estimated_cost"]
        
        return {
            "total_models": len(ranked),
            "cheapest": cheapest,
            "most_expensive": most_expensive,
            "cost_range_usd": round(cost_range, 8),
            "potential_savings_usd": round(cost_range, 8),
            "savings_percentage": round(
                (cost_range / most_expensive["estimated_cost"]) * 100, 2
            ) if most_expensive["estimated_cost"] > 0 else 0,
            "models": ranked
        }