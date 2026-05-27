"""
Tests for restocking API endpoints.
"""
import pytest


class TestRestockRecommendationsEndpoint:
    """Test suite for GET /api/restocking/recommendations."""

    def test_get_recommendations_structure(self, client):
        """Test that recommendations response has the expected envelope + item fields."""
        response = client.get("/api/restocking/recommendations?budget=10000")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)
        assert "budget" in data
        assert "total_cost" in data
        assert "remaining_budget" in data
        assert "items" in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) > 0

        first = data["items"][0]
        for field in (
            "item_sku",
            "item_name",
            "category",
            "demand_gap",
            "recommended_quantity",
            "unit_cost",
            "line_cost",
            "lead_time_days",
            "included",
        ):
            assert field in first

    def test_recommendations_large_budget_includes_all_nonzero_gap(self, client):
        """With a very large budget, every item with demand_gap > 0 is included."""
        response = client.get("/api/restocking/recommendations?budget=1000000")
        assert response.status_code == 200

        data = response.json()
        for item in data["items"]:
            if item["demand_gap"] > 0:
                assert item["included"] is True
            else:
                # Zero-gap items are never included regardless of budget
                assert item["included"] is False

    def test_recommendations_zero_budget_excludes_all(self, client):
        """With zero budget, no items are included and total_cost is 0."""
        response = client.get("/api/restocking/recommendations?budget=0")
        assert response.status_code == 200

        data = response.json()
        assert data["total_cost"] == 0
        assert data["remaining_budget"] == 0
        for item in data["items"]:
            assert item["included"] is False

    def test_recommendations_total_within_budget(self, client):
        """Included items' line costs sum to total_cost, which never exceeds budget."""
        budget = 5000
        response = client.get(f"/api/restocking/recommendations?budget={budget}")
        assert response.status_code == 200

        data = response.json()
        included_sum = sum(i["line_cost"] for i in data["items"] if i["included"])
        assert abs(data["total_cost"] - included_sum) < 0.01
        assert data["total_cost"] <= budget
        assert abs(data["remaining_budget"] - (budget - data["total_cost"])) < 0.01

    def test_recommendations_sorted_by_demand_gap_desc(self, client):
        """Items are returned sorted by demand_gap descending."""
        response = client.get("/api/restocking/recommendations?budget=10000")
        assert response.status_code == 200

        gaps = [i["demand_gap"] for i in response.json()["items"]]
        assert gaps == sorted(gaps, reverse=True)

    def test_recommendations_line_cost_calculation(self, client):
        """line_cost == recommended_quantity * unit_cost for every item."""
        response = client.get("/api/restocking/recommendations?budget=10000")
        assert response.status_code == 200

        for item in response.json()["items"]:
            expected = item["recommended_quantity"] * item["unit_cost"]
            assert abs(item["line_cost"] - expected) < 0.01

    def test_recommendations_lead_time_types(self, client):
        """lead_time_days is a positive integer."""
        response = client.get("/api/restocking/recommendations?budget=10000")
        assert response.status_code == 200

        for item in response.json()["items"]:
            assert isinstance(item["lead_time_days"], int)
            assert item["lead_time_days"] > 0


class TestRestockOrdersEndpoint:
    """Test suite for POST/GET /api/restocking/orders."""

    def _line(self, sku="WDG-001", name="Industrial Widget Type A",
              category="Actuators", qty=10, unit_cost=18.5):
        return {
            "item_sku": sku,
            "item_name": name,
            "category": category,
            "quantity": qty,
            "unit_cost": unit_cost,
            "line_cost": round(qty * unit_cost, 2),
        }

    def test_submit_order_success(self, client):
        """Submitting a valid order returns 200 with order_number, lead time, expected_delivery."""
        payload = {"budget": 1000.0, "items": [self._line()]}
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 200

        order = response.json()
        assert "id" in order
        assert order["order_number"].startswith("RST-")
        assert order["status"] == "Submitted"
        assert isinstance(order["lead_time_days"], int)
        assert order["lead_time_days"] > 0
        assert "-" in order["submitted_date"]
        assert "-" in order["expected_delivery"]
        assert abs(order["total_value"] - 185.0) < 0.01
        assert len(order["items"]) == 1

    def test_submit_order_empty_items_rejected(self, client):
        """Submitting with no items returns 400."""
        response = client.post("/api/restocking/orders", json={"budget": 1000.0, "items": []})
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
        assert "at least one" in data["detail"].lower()

    def test_submit_order_over_budget_rejected(self, client):
        """Submitting items whose total exceeds budget returns 400."""
        payload = {"budget": 50.0, "items": [self._line(qty=10, unit_cost=18.5)]}  # 185 > 50
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
        assert "budget" in data["detail"].lower()

    def test_submit_order_lead_time_is_max_category(self, client):
        """Order lead time equals the slowest category among its items."""
        payload = {
            "budget": 5000.0,
            "items": [
                self._line(sku="A", category="Actuators", qty=1, unit_cost=10.0),       # 5d
                self._line(sku="B", category="Power Supplies", qty=1, unit_cost=10.0),  # 12d
            ],
        }
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 200
        assert response.json()["lead_time_days"] == 12

    def test_get_orders_contains_submitted(self, client):
        """GET /restocking/orders returns previously submitted orders, newest first."""
        # Submit a fresh order
        payload = {"budget": 500.0, "items": [self._line(qty=1, unit_cost=18.5)]}
        post_resp = client.post("/api/restocking/orders", json=payload)
        assert post_resp.status_code == 200
        new_id = post_resp.json()["id"]

        # List orders
        response = client.get("/api/restocking/orders")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # Newest first → our just-submitted order is at index 0
        assert data[0]["id"] == new_id
