"""
Pydantic models for transaction request/response validation.

This module defines the data models used for serialization and validation
of transaction-related operations.
"""

from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field, validator


class TransactionBase(BaseModel):
    """Base model for transaction data."""
    
    description: str = Field(..., min_length=1, max_length=500)
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    type: str = Field(..., pattern="^(income|expense)$")
    category: str = Field(..., min_length=1, max_length=100)
    transaction_date: date
    is_personal: bool = False


class TransactionCreate(TransactionBase):
    """Model for creating a new transaction."""
    
    pass


class TransactionUpdate(BaseModel):
    """Model for updating an existing transaction."""
    
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    type: Optional[str] = Field(None, pattern="^(income|expense)$")
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    transaction_date: Optional[date] = None
    is_personal: Optional[bool] = None


class TransactionResponse(TransactionBase):
    """Model for transaction response."""
    
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    warning: Optional[str] = None
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
    
    @validator("warning", pre=True, always=True)
    def add_personal_expense_warning(cls, v, values):
        """
        Add warning flag for personal expenses.
        
        Args:
            v: Current warning value
            values: All field values
            
        Returns:
            Warning message if personal expense, else None
        """
        if values.get("type") == "expense" and (
            values.get("category") == "Personal" or values.get("is_personal")
        ):
            return "This expense is marked as personal and may affect business profit clarity."
        return None


class PaginatedTransactionResponse(BaseModel):
    """Model for paginated transaction response."""
    
    success: bool
    data: List[TransactionResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    message: str = ""


class TransactionDetailResponse(BaseModel):
    """Model for single transaction detail response."""
    
    success: bool
    data: TransactionResponse
    message: str = ""


# Alias for compatibility
SingleTransactionResponse = TransactionDetailResponse


class TransactionDeleteResponse(BaseModel):
    """Model for delete transaction response."""
    
    success: bool
    message: str = ""


# Alias for compatibility
DeleteTransactionResponse = TransactionDeleteResponse


class TransactionSummary(BaseModel):
    """Model for transaction summary (used in exports)."""
    
    total_income: Decimal
    total_expense: Decimal
    net_profit: Decimal


class ExportResponse(BaseModel):
    """Model for export operation response."""
    
    success: bool
    message: str
    file_name: str


class ErrorResponse(BaseModel):
    """Model for error responses."""
    
    success: bool
    message: str
    error_code: Optional[str] = None
