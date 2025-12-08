"""
Pydantic schemas for transaction data.
"""
from typing import List, Optional
from datetime import date as date_type
from pydantic import BaseModel, Field


class TransactionSchema(BaseModel):
    """Schema for individual transaction."""
    id: Optional[int] = Field(None, description="Transaction ID")
    user_id: Optional[int] = Field(None, description="User ID")
    amount: float = Field(..., description="Transaction amount")
    category: str = Field(..., description="Transaction category")
    category_id: Optional[int] = Field(None, description="Category ID")
    type: str = Field(..., description="Transaction type: income, expense, savings")
    date: str = Field(..., description="Transaction date in YYYY-MM-DD format")
    note: Optional[str] = Field(None, description="Transaction note")


class TransactionListRequest(BaseModel):
    """Request schema for endpoints accepting transaction lists."""
    user_id: int = Field(..., description="User ID")
    transactions: List[TransactionSchema] = Field(..., description="List of transactions")
