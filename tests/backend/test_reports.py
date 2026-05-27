"""
Tests for reports API endpoints (quarterly + monthly trends), including the
global filters (warehouse / category / status / month) added so the Reports
page honors the filter bar like the rest of the app.
"""
import pytest


class TestQuarterlyReportEndpoint:
    """Test suite for GET /api/reports/quarterly."""

    def test_get_quarterly_structure(self, client):
        """Returns a list of quarters with the expected fields."""
        response = client.get("/api/reports/quarterly")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        for field in ("quarter", "total_orders", "total_revenue", "avg_order_value", "fulfillment_rate"):
            assert field in data[0]

    def test_quarterly_sorted_by_quarter(self, client):
        """Quarters are returned in ascending order."""
        data = client.get("/api/reports/quarterly").json()
        quarters = [q["quarter"] for q in data]
        assert quarters == sorted(quarters)

    def test_quarterly_avg_order_value_calculation(self, client):
        """avg_order_value == total_revenue / total_orders for each quarter."""
        for q in client.get("/api/reports/quarterly").json():
            if q["total_orders"] > 0:
                expected = q["total_revenue"] / q["total_orders"]
                assert abs(q["avg_order_value"] - expected) < 0.01

    def test_quarterly_total_orders_matches_orders_endpoint(self, client):
        """Sum of quarterly total_orders equals the number of orders (all are 2025)."""
        total = sum(q["total_orders"] for q in client.get("/api/reports/quarterly").json())
        assert total == len(client.get("/api/orders").json())

    def test_quarterly_warehouse_filter(self, client):
        """A warehouse filter restricts the aggregation to that warehouse's orders."""
        tokyo_orders = len(client.get("/api/orders?warehouse=Tokyo").json())
        quarterly = client.get("/api/reports/quarterly?warehouse=Tokyo").json()
        assert sum(q["total_orders"] for q in quarterly) == tokyo_orders
        # And it should be a strict subset of the unfiltered total.
        assert tokyo_orders < len(client.get("/api/orders").json())

    def test_quarterly_status_filter(self, client):
        """A status filter restricts the aggregation; fulfillment is 100% for Delivered."""
        delivered = len(client.get("/api/orders?status=Delivered").json())
        quarterly = client.get("/api/reports/quarterly?status=Delivered").json()
        assert sum(q["total_orders"] for q in quarterly) == delivered
        for q in quarterly:
            assert q["fulfillment_rate"] == 100.0

    def test_quarterly_month_filter_limits_to_one_quarter(self, client):
        """Filtering by Q1-2025 returns only the Q1 quarter."""
        quarterly = client.get("/api/reports/quarterly?month=Q1-2025").json()
        assert [q["quarter"] for q in quarterly] == ["Q1-2025"]

    def test_quarterly_single_month_filter(self, client):
        """Filtering by a single month (2025-01) only includes Q1."""
        quarterly = client.get("/api/reports/quarterly?month=2025-01").json()
        assert {q["quarter"] for q in quarterly}.issubset({"Q1-2025"})


class TestMonthlyTrendsEndpoint:
    """Test suite for GET /api/reports/monthly-trends."""

    def test_get_monthly_structure(self, client):
        """Returns a list of months with the expected fields."""
        response = client.get("/api/reports/monthly-trends")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        for field in ("month", "order_count", "revenue", "delivered_count"):
            assert field in data[0]

    def test_monthly_sorted_by_month(self, client):
        """Months are returned in ascending order."""
        data = client.get("/api/reports/monthly-trends").json()
        months = [m["month"] for m in data]
        assert months == sorted(months)

    def test_monthly_order_count_matches_orders_endpoint(self, client):
        """Sum of monthly order_count equals the total number of orders."""
        total = sum(m["order_count"] for m in client.get("/api/reports/monthly-trends").json())
        assert total == len(client.get("/api/orders").json())

    def test_monthly_category_filter(self, client):
        """A category filter restricts the aggregation to that category's orders."""
        sensors = len(client.get("/api/orders?category=Sensors").json())
        monthly = client.get("/api/reports/monthly-trends?category=Sensors").json()
        assert sum(m["order_count"] for m in monthly) == sensors

    def test_monthly_month_filter_limits_to_one_month(self, client):
        """Filtering by a single month returns only that month."""
        monthly = client.get("/api/reports/monthly-trends?month=2025-03").json()
        assert [m["month"] for m in monthly] == ["2025-03"]

    def test_monthly_revenue_matches_orders_endpoint(self, client):
        """Sum of monthly revenue equals the sum of order total_value."""
        orders_total = sum(o["total_value"] for o in client.get("/api/orders").json())
        monthly_total = sum(m["revenue"] for m in client.get("/api/reports/monthly-trends").json())
        assert abs(orders_total - monthly_total) < 0.01
