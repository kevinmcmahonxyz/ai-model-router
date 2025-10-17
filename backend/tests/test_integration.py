"""Integration tests for full workflows."""
import pytest
from datetime import datetime


class TestDashboardWorkflow:
    """Test complete dashboard data flow."""
    
    def test_complete_analytics_workflow(self, client, auth_headers, test_requests):
        """
        Test a realistic dashboard workflow:
        1. Load overview stats
        2. Browse request history
        3. View specific request detail
        4. Check available models
        """
        
        # Step 1: Load overview dashboard
        response = client.get(
            "/v1/analytics/usage?days=30",
            headers=auth_headers
        )
        assert response.status_code == 200
        overview = response.json()
        
        # Verify we have data
        assert overview["total_requests"] > 0
        assert overview["total_cost_usd"] > 0
        assert len(overview["by_model"]) > 0
        
        # Step 2: Get first page of request history
        response = client.get(
            "/v1/analytics/requests?page=1&per_page=5",
            headers=auth_headers
        )
        assert response.status_code == 200
        history = response.json()
        
        assert len(history["requests"]) > 0
        assert history["total"] == overview["total_requests"]
        
        # Step 3: Click on first request to see details
        first_request_id = history["requests"][0]["id"]
        response = client.get(
            f"/v1/analytics/requests/{first_request_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        detail = response.json()
        
        # Verify detail matches summary
        assert detail["id"] == first_request_id
        assert detail["model"] == history["requests"][0]["model"]
        assert detail["prompt_text"] is not None
        
        # Step 4: Get available models for filtering
        response = client.get(
            "/v1/analytics/models",
            headers=auth_headers
        )
        assert response.status_code == 200
        models = response.json()
        
        assert len(models) > 0
        
        # Step 5: Filter history by one of the models
        model_to_filter = models[0]["model_id"]
        response = client.get(
            f"/v1/analytics/requests?model={model_to_filter}",
            headers=auth_headers
        )
        assert response.status_code == 200
        filtered = response.json()
        
        # All results should match the filter
        for req in filtered["requests"]:
            assert req["model"] == model_to_filter
    
    def test_cost_calculation_consistency(self, client, auth_headers, test_requests):
        """
        Verify cost calculations are consistent across endpoints.
        """
        # Get total from usage endpoint
        response = client.get(
            "/v1/analytics/usage?days=30",
            headers=auth_headers
        )
        assert response.status_code == 200
        usage_total_cost = response.json()["total_cost_usd"]
        
        # Get all requests and sum their costs
        response = client.get(
            "/v1/analytics/requests?per_page=100",
            headers=auth_headers
        )
        assert response.status_code == 200
        requests_data = response.json()
        
        manual_total = sum(req["total_cost_usd"] for req in requests_data["requests"])
        
        # Should match (within floating point precision)
        assert abs(usage_total_cost - manual_total) < 0.000001
    
    def test_date_range_filtering_consistency(self, client, auth_headers, test_requests):
        """
        Verify date filtering works consistently across endpoints.
        """
        # Get last 7 days from usage
        response = client.get(
            "/v1/analytics/usage?days=7",
            headers=auth_headers
        )
        assert response.status_code == 200
        usage_count = response.json()["total_requests"]
        
        # Get same period from requests endpoint
        from datetime import timedelta
        start_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
        
        response = client.get(
            f"/v1/analytics/requests?start_date={start_date}&per_page=100",
            headers=auth_headers
        )
        assert response.status_code == 200
        requests_count = response.json()["total"]
        
        # Should match
        assert usage_count == requests_count
    
    def test_pagination_completeness(self, client, auth_headers, test_requests):
        """
        Verify pagination returns all records when traversing pages.
        """
        # Get total count
        response = client.get(
            "/v1/analytics/requests?per_page=3",
            headers=auth_headers
        )
        assert response.status_code == 200
        first_page = response.json()
        
        total = first_page["total"]
        total_pages = first_page["total_pages"]
        
        # Collect all IDs across pages
        all_ids = set()
        for page in range(1, total_pages + 1):
            response = client.get(
                f"/v1/analytics/requests?page={page}&per_page=3",
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            
            for req in data["requests"]:
                all_ids.add(req["id"])
        
        # Should have collected all unique requests
        assert len(all_ids) == total
    
    def test_search_finds_all_matches(self, client, auth_headers, test_requests):
        """
        Verify search functionality finds all matching records.
        """
        # Search for "Test" which should be in all prompts
        response = client.get(
            "/v1/analytics/requests?search=Test&per_page=100",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should find all requests (all have "Test" in prompt)
        assert data["total"] == len(test_requests)
        
        # Search for specific number
        response = client.get(
            "/v1/analytics/requests?search=prompt 3&per_page=100",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should find exactly one
        assert data["total"] == 1
        assert "3" in data["requests"][0]["prompt_preview"]


class TestErrorHandling:
    """Test error scenarios."""
    
    def test_invalid_request_id_format(self, client, auth_headers):
        """Test with malformed UUID."""
        response = client.get(
            "/v1/analytics/requests/not-a-uuid",
            headers=auth_headers
        )
        # FastAPI validation should catch this
        assert response.status_code in [404, 422]
    
    def test_invalid_pagination_parameters(self, client, auth_headers, test_requests):
        """Test with invalid pagination values."""
        # Negative page
        response = client.get(
            "/v1/analytics/requests?page=-1",
            headers=auth_headers
        )
        assert response.status_code == 422
        
        # Per page too large
        response = client.get(
            "/v1/analytics/requests?per_page=1000",
            headers=auth_headers
        )
        assert response.status_code == 422
    
    def test_invalid_date_format(self, client, auth_headers, test_requests):
        """Test with malformed date."""
        response = client.get(
            "/v1/analytics/requests?start_date=not-a-date",
            headers=auth_headers
        )
        assert response.status_code == 422