"""Tests for analytics endpoints."""
import pytest
from datetime import datetime, timedelta


class TestUsageEndpoint:
    """Tests for GET /v1/analytics/usage"""
    
    def test_usage_stats_success(self, client, auth_headers, test_requests):
        """Test getting usage statistics."""
        response = client.get(
            "/v1/analytics/usage?days=30",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "total_requests" in data
        assert "total_cost_usd" in data
        assert "avg_latency_ms" in data
        assert "success_rate" in data
        assert "by_provider" in data
        assert "by_model" in data
        assert "daily_stats" in data
        
        # Verify counts
        assert data["total_requests"] == 10
        assert data["success_rate"] == 0.9  # 9 success, 1 error
        
        # Verify provider breakdown
        assert len(data["by_provider"]) == 1
        assert data["by_provider"][0]["provider"] == "openai"
        assert data["by_provider"][0]["requests"] == 10
        
        # Verify model breakdown
        assert len(data["by_model"]) == 2
        model_ids = [m["model"] for m in data["by_model"]]
        assert "gpt-4o-mini" in model_ids
        assert "gpt-4o" in model_ids
    
    def test_usage_stats_different_days(self, client, auth_headers, test_requests):
        """Test filtering by different day ranges."""
        # Get last 7 days (should have fewer requests)
        response = client.get(
            "/v1/analytics/usage?days=7",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have fewer than 10 requests
        assert data["total_requests"] < 10
        assert data["total_requests"] >= 1
    
    def test_usage_stats_no_data(self, client, auth_headers):
        """Test with no requests in database."""
        response = client.get(
            "/v1/analytics/usage?days=30",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_requests"] == 0
        assert data["total_cost_usd"] == 0.0
        assert data["avg_latency_ms"] == 0
        assert data["success_rate"] == 0.0
        assert len(data["by_provider"]) == 0
        assert len(data["by_model"]) == 0
        assert len(data["daily_stats"]) == 0
    
    def test_usage_stats_invalid_days(self, client, auth_headers):
        """Test with invalid days parameter."""
        # Days too large
        response = client.get(
            "/v1/analytics/usage?days=999",
            headers=auth_headers
        )
        assert response.status_code == 422  # Validation error
        
        # Days too small
        response = client.get(
            "/v1/analytics/usage?days=0",
            headers=auth_headers
        )
        assert response.status_code == 422
    
    def test_usage_stats_unauthorized(self, client):
        """Test without API key."""
        response = client.get("/v1/analytics/usage?days=30")
        assert response.status_code == 422  # Missing header


class TestRequestsListEndpoint:
    """Tests for GET /v1/analytics/requests"""
    
    def test_get_requests_default(self, client, auth_headers, test_requests):
        """Test getting paginated requests with defaults."""
        response = client.get(
            "/v1/analytics/requests",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "requests" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "total_pages" in data
        
        # Verify pagination
        assert data["total"] == 10
        assert data["page"] == 1
        assert data["per_page"] == 20
        assert data["total_pages"] == 1
        assert len(data["requests"]) == 10
        
        # Check request structure
        req = data["requests"][0]
        assert "id" in req
        assert "created_at" in req
        assert "model" in req
        assert "provider" in req
        assert "prompt_preview" in req
        assert "input_tokens" in req
        assert "output_tokens" in req
        assert "total_cost_usd" in req
        assert "latency_ms" in req
        assert "status" in req
    
    def test_get_requests_pagination(self, client, auth_headers, test_requests):
        """Test pagination with smaller page size."""
        response = client.get(
            "/v1/analytics/requests?page=1&per_page=5",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 10
        assert data["page"] == 1
        assert data["per_page"] == 5
        assert data["total_pages"] == 2
        assert len(data["requests"]) == 5
        
        # Get page 2
        response = client.get(
            "/v1/analytics/requests?page=2&per_page=5",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert len(data["requests"]) == 5
    
    def test_get_requests_filter_by_model(self, client, auth_headers, test_requests):
        """Test filtering by model."""
        response = client.get(
            "/v1/analytics/requests?model=gpt-4o-mini",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have 5 requests (alternating pattern)
        assert data["total"] == 5
        
        # All should be gpt-4o-mini
        for req in data["requests"]:
            assert req["model"] == "gpt-4o-mini"
    
    def test_get_requests_filter_by_status(self, client, auth_headers, test_requests):
        """Test filtering by status."""
        # Get only successful requests
        response = client.get(
            "/v1/analytics/requests?status=success",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 9
        
        for req in data["requests"]:
            assert req["status"] == "success"
        
        # Get only errors
        response = client.get(
            "/v1/analytics/requests?status=error",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["requests"][0]["status"] == "error"
    
    def test_get_requests_search(self, client, auth_headers, test_requests):
        """Test search functionality."""
        response = client.get(
            "/v1/analytics/requests?search=prompt 5",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should find the request with "Test prompt 5"
        assert data["total"] >= 1
        assert any("5" in req["prompt_preview"] for req in data["requests"])
    
    def test_get_requests_date_range(self, client, auth_headers, test_requests):
        """Test date range filtering."""
        # Get only recent requests (last 7 days)
        start_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
        
        response = client.get(
            f"/v1/analytics/requests?start_date={start_date}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have fewer than total
        assert data["total"] < 10
    
    def test_get_requests_combined_filters(self, client, auth_headers, test_requests):
        """Test multiple filters at once."""
        response = client.get(
            "/v1/analytics/requests?model=gpt-4o-mini&status=success&per_page=3",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have filtered results
        assert data["total"] <= 5  # Can't be more than gpt-4o-mini count
        assert len(data["requests"]) <= 3  # Respects per_page
        
        for req in data["requests"]:
            assert req["model"] == "gpt-4o-mini"
            assert req["status"] == "success"
    
    def test_get_requests_empty_results(self, client, auth_headers, test_requests):
        """Test with filters that return no results."""
        response = client.get(
            "/v1/analytics/requests?model=nonexistent-model",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 0
        assert len(data["requests"]) == 0
    
    def test_get_requests_prompt_preview_truncation(self, client, auth_headers, db, test_user, test_provider, test_models):
        """Test that long prompts are truncated in preview."""
        from src.models.schemas import Request
        import uuid
        
        # Create request with long prompt
        long_prompt = "A" * 100
        req = Request(
            id=uuid.uuid4(),
            user_id=test_user.id,
            model_id=test_models[0].id,
            provider_id=test_provider.id,
            prompt_text=long_prompt,
            response_text="Response",
            status="success",
            latency_ms=1000
        )
        db.add(req)
        db.commit()
        
        response = client.get(
            "/v1/analytics/requests",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Find our long prompt request
        long_req = next(r for r in data["requests"] if "A" in r["prompt_preview"])
        
        # Should be truncated to 50 chars + "..."
        assert len(long_req["prompt_preview"]) == 53  # 50 + "..."
        assert long_req["prompt_preview"].endswith("...")


class TestRequestDetailEndpoint:
    """Tests for GET /v1/analytics/requests/{id}"""
    
    def test_get_request_detail_success(self, client, auth_headers, test_requests):
        """Test getting single request detail."""
        request_id = str(test_requests[0].id)
        
        response = client.get(
            f"/v1/analytics/requests/{request_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check all fields present
        assert data["id"] == request_id
        assert "created_at" in data
        assert "completed_at" in data
        assert data["model"] in ["gpt-4o-mini", "gpt-4o"]
        assert data["provider"] == "openai"
        assert data["prompt_text"] == "Test prompt 0"
        assert data["response_text"] == "Test response 0"
        assert data["status"] == "success"
        
        # Check token and cost fields
        assert isinstance(data["input_tokens"], int)
        assert isinstance(data["output_tokens"], int)
        assert isinstance(data["total_cost_usd"], float)
        assert isinstance(data["latency_ms"], int)
    
    def test_get_request_detail_error_request(self, client, auth_headers, test_requests):
        """Test getting detail of failed request."""
        # Get the error request (last one)
        request_id = str(test_requests[-1].id)
        
        response = client.get(
            f"/v1/analytics/requests/{request_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "error"
        assert data["error_message"] == "Test error"
        assert data["response_text"] is None
    
    def test_get_request_detail_not_found(self, client, auth_headers):
        """Test with nonexistent request ID."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        response = client.get(
            f"/v1/analytics/requests/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_request_detail_wrong_user(self, client, db, test_provider, test_models, test_requests):
        """Test accessing another user's request."""
        from src.models.schemas import User
        import uuid
        
        # Create another user
        other_user = User(
            id=uuid.uuid4(),
            api_key="other_user_key",
            is_active=True
        )
        db.add(other_user)
        db.commit()
        
        # Try to access first user's request with second user's key
        request_id = str(test_requests[0].id)
        
        response = client.get(
            f"/v1/analytics/requests/{request_id}",
            headers={"X-API-Key": "other_user_key"}
        )
        
        assert response.status_code == 404  # Not found (correct - shouldn't reveal existence)


class TestModelsEndpoint:
    """Tests for GET /v1/analytics/models"""
    
    def test_get_models_success(self, client, auth_headers, test_models):
        """Test getting list of available models."""
        response = client.get(
            "/v1/analytics/models",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == 2
        
        # Check model structure
        model = data[0]
        assert "id" in model
        assert "model_id" in model
        assert "display_name" in model
        assert "provider" in model
        assert "input_price_per_1m_tokens" in model
        assert "output_price_per_1m_tokens" in model
        assert "context_window" in model
        assert "is_active" in model
        
        # Verify data
        model_ids = [m["model_id"] for m in data]
        assert "gpt-4o-mini" in model_ids
        assert "gpt-4o" in model_ids
        
        for m in data:
            assert m["provider"] == "openai"
            assert m["is_active"] is True
    
    def test_get_models_only_active(self, client, auth_headers, db, test_provider):
        """Test that only active models are returned."""
        from src.models.schemas import Model
        
        # Add inactive model
        inactive = Model(
            provider_id=test_provider.id,
            model_id="gpt-3.5-turbo",
            display_name="GPT-3.5 Turbo",
            input_price_per_1m_tokens=0.50,
            output_price_per_1m_tokens=1.50,
            is_active=False
        )
        db.add(inactive)
        db.commit()
        
        response = client.get(
            "/v1/analytics/models",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should not include inactive model
        model_ids = [m["model_id"] for m in data]
        assert "gpt-3.5-turbo" not in model_ids
    
    def test_get_models_empty(self, client, auth_headers):
        """Test with no models in database."""
        response = client.get(
            "/v1/analytics/models",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0


class TestAuthentication:
    """Tests for API key authentication across all endpoints."""
    
    def test_invalid_api_key(self, client):
        """Test with invalid API key."""
        headers = {"X-API-Key": "invalid_key"}
        
        response = client.get("/v1/analytics/usage", headers=headers)
        assert response.status_code == 401
        
        response = client.get("/v1/analytics/requests", headers=headers)
        assert response.status_code == 401
        
        response = client.get("/v1/analytics/models", headers=headers)
        assert response.status_code == 401
    
    def test_missing_api_key(self, client):
        """Test without API key header."""
        response = client.get("/v1/analytics/usage")
        assert response.status_code == 422  # Validation error
        
        response = client.get("/v1/analytics/requests")
        assert response.status_code == 422
    
    def test_inactive_user(self, client, db, test_user):
        """Test with deactivated user."""
        # Deactivate user
        test_user.is_active = False
        db.commit()
        
        headers = {"X-API-Key": test_user.api_key}
        
        response = client.get("/v1/analytics/usage", headers=headers)
        assert response.status_code == 401