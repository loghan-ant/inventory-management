"""
Tests for purchase order API endpoints (in-memory).
"""
import pytest


class TestPurchaseOrderEndpoints:
    """Test suite for /api/purchase-orders endpoints."""

    def _payload(self, backlog_item_id="1", supplier="Acme Supply Co",
                 qty=350, unit_cost=22.40, due="2026-06-15", notes="Rush order"):
        return {
            "backlog_item_id": backlog_item_id,
            "supplier_name": supplier,
            "quantity": qty,
            "unit_cost": unit_cost,
            "expected_delivery_date": due,
            "notes": notes,
        }

    def test_create_purchase_order_success(self, client):
        """POST creates a PO with an id, 'Pending' status, and a created_date."""
        response = client.post("/api/purchase-orders", json=self._payload(backlog_item_id="100"))
        assert response.status_code == 200

        po = response.json()
        assert po["id"].startswith("PO-")
        assert po["backlog_item_id"] == "100"
        assert po["supplier_name"] == "Acme Supply Co"
        assert po["quantity"] == 350
        assert abs(po["unit_cost"] - 22.40) < 0.01
        assert po["expected_delivery_date"] == "2026-06-15"
        assert po["status"] == "Pending"
        assert "-" in po["created_date"]
        assert po["notes"] == "Rush order"

    def test_get_purchase_order_by_backlog_item(self, client):
        """GET returns the PO created for a given backlog item."""
        created = client.post("/api/purchase-orders", json=self._payload(backlog_item_id="101")).json()

        response = client.get("/api/purchase-orders/101")
        assert response.status_code == 200

        po = response.json()
        assert po["id"] == created["id"]
        assert po["backlog_item_id"] == "101"

    def test_get_nonexistent_purchase_order_404(self, client):
        """GET for a backlog item with no PO returns 404."""
        response = client.get("/api/purchase-orders/no-such-backlog-item")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_purchase_order_missing_fields_rejected(self, client):
        """Missing required fields returns 422."""
        response = client.post("/api/purchase-orders", json={"backlog_item_id": "1"})
        assert response.status_code == 422

    def test_create_purchase_order_optional_notes(self, client):
        """Notes is optional; a PO can be created without it."""
        payload = self._payload(backlog_item_id="102")
        del payload["notes"]

        response = client.post("/api/purchase-orders", json=payload)
        assert response.status_code == 200
        assert response.json()["notes"] is None

    def test_created_po_reflected_in_backlog(self, client):
        """Creating a PO flips has_purchase_order to True for that backlog item."""
        # Backlog item "2" exists in the dataset.
        client.post("/api/purchase-orders", json=self._payload(backlog_item_id="2"))

        backlog = client.get("/api/backlog").json()
        item = next((b for b in backlog if b["id"] == "2"), None)
        assert item is not None
        assert item["has_purchase_order"] is True
