"""
Unit tests for the Transaction Management Module.

Basic test examples for common endpoints and scenarios.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import date, datetime
from decimal import Decimal

from app.main import app

# Create test client
client = TestClient(app)

# Test data
VALID_TRANSACTION = {
    "description": "Test expense",
    "amount": 100.00,
    "type": "expense",
    "category": "Test",
    "transaction_date": date.today().isoformat(),
    "is_personal": False
}

VALID_INCOME = {
    "description": "Test income",
    "amount": 1000.00,
    "type": "income",
    "category": "Revenue",
    "transaction_date": date.today().isoformat(),
    "is_personal": False
}

PERSONAL_EXPENSE = {
    "description": "Personal medical",
    "amount": 200.00,
    "type": "expense",
    "category": "Personal",
    "transaction_date": date.today().isoformat(),
    "is_personal": True
}


class TestRootEndpoint:
    """Test root endpoint"""
    
    def test_root_endpoint(self):
        """Test / endpoint returns API info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "api_name" in data["data"]
        assert "endpoints" in data["data"]
    
    def test_health_check(self):
        """Test /health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "status" in data


class TestTransactionCreation:
    """Test transaction creation endpoints"""
    
    def test_create_valid_expense(self):
        """Test creating a valid expense transaction"""
        response = client.post("/transactions", json=VALID_TRANSACTION)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["type"] == "expense"
        assert data["data"]["amount"] == "100.00"
    
    def test_create_valid_income(self):
        """Test creating a valid income transaction"""
        response = client.post("/transactions", json=VALID_INCOME)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["type"] == "income"
    
    def test_create_personal_expense_has_warning(self):
        """Test personal expense includes warning flag"""
        response = client.post("/transactions", json=PERSONAL_EXPENSE)
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "warning" in data["data"]
        assert data["data"]["warning"] is not None
        assert "personal" in data["data"]["warning"].lower()
    
    def test_create_invalid_amount(self):
        """Test creating transaction with invalid amount"""
        invalid_data = {**VALID_TRANSACTION, "amount": -100.00}
        response = client.post("/transactions", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_create_invalid_type(self):
        """Test creating transaction with invalid type"""
        invalid_data = {**VALID_TRANSACTION, "type": "transfer"}
        response = client.post("/transactions", json=invalid_data)
        assert response.status_code == 422
    
    def test_create_missing_required_field(self):
        """Test creating transaction with missing fields"""
        incomplete_data = {"description": "Missing amount"}
        response = client.post("/transactions", json=incomplete_data)
        assert response.status_code == 422


class TestTransactionRetrieval:
    """Test transaction retrieval endpoints"""
    
    def test_get_transactions_list(self):
        """Test getting transactions list"""
        response = client.get("/transactions")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "total_count" in data
        assert "page" in data
        assert "page_size" in data
    
    def test_get_transactions_with_pagination(self):
        """Test pagination parameters"""
        response = client.get("/transactions?page=1&page_size=5")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5
    
    def test_get_transactions_sorting(self):
        """Test sorting by different fields"""
        # Sort by date
        response = client.get("/transactions?sort_by=transaction_date&order=asc")
        assert response.status_code == 200
        
        # Sort by amount
        response = client.get("/transactions?sort_by=amount&order=desc")
        assert response.status_code == 200
    
    def test_get_transactions_with_search(self):
        """Test search functionality"""
        response = client.get("/transactions?search=test")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_transactions_with_filters(self):
        """Test filtering by category and type"""
        response = client.get("/transactions?category=Test&type=expense")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_single_transaction_not_found(self):
        """Test getting non-existent transaction"""
        response = client.get("/transactions/invalid-id")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False


class TestTransactionUpdate:
    """Test transaction update endpoints"""
    
    def test_update_non_existent_transaction(self):
        """Test updating non-existent transaction"""
        response = client.put(
            "/transactions/invalid-id",
            json={"amount": 150.00}
        )
        assert response.status_code == 404


class TestTransactionDeletion:
    """Test transaction deletion endpoints"""
    
    def test_delete_non_existent_transaction(self):
        """Test deleting non-existent transaction"""
        response = client.delete("/transactions/invalid-id")
        assert response.status_code == 404


class TestExportFunctionality:
    """Test export endpoints"""
    
    def test_export_csv_no_data(self):
        """Test CSV export with no matching data"""
        response = client.get("/transactions/export/csv?search=nonexistent_pattern_xyz")
        # Should return error when no data
        assert response.status_code in [200, 400]
    
    def test_export_pdf_no_data(self):
        """Test PDF export with no matching data"""
        response = client.get("/transactions/export/pdf?search=nonexistent_pattern_xyz")
        # Should return error when no data
        assert response.status_code in [200, 400]


class TestDataValidation:
    """Test Pydantic model validation"""
    
    def test_description_length_validation(self):
        """Test description length constraints"""
        # Too long description
        long_desc = "A" * 501
        invalid_data = {**VALID_TRANSACTION, "description": long_desc}
        response = client.post("/transactions", json=invalid_data)
        assert response.status_code == 422
    
    def test_category_length_validation(self):
        """Test category length constraints"""
        # Too long category
        long_category = "A" * 101
        invalid_data = {**VALID_TRANSACTION, "category": long_category}
        response = client.post("/transactions", json=invalid_data)
        assert response.status_code == 422
    
    def test_zero_amount_not_allowed(self):
        """Test that zero amount is rejected"""
        invalid_data = {**VALID_TRANSACTION, "amount": 0}
        response = client.post("/transactions", json=invalid_data)
        assert response.status_code == 422
    
    def test_negative_amount_not_allowed(self):
        """Test that negative amount is rejected"""
        invalid_data = {**VALID_TRANSACTION, "amount": -50.00}
        response = client.post("/transactions", json=invalid_data)
        assert response.status_code == 422


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
