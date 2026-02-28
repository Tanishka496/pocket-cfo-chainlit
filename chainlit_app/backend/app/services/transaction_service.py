"""
Transaction service layer for database operations.

This module contains all business logic for transaction management,
including CRUD operations, filtering, sorting, and pagination.
"""

from typing import List, Optional, Tuple, Dict, Any
from datetime import date
from decimal import Decimal
from supabase import Client
from app.models.transaction_models import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse
)


class TransactionService:
    """
    Service class for transaction database operations.
    
    Handles all interactions with the Supabase database for transactions,
    including filtering, sorting, pagination, and CRUD operations.
    """
    
    TABLE_NAME = "transactions"
    
    def __init__(self, supabase_client: Client):
        """
        Initialize TransactionService.
        
        Args:
            supabase_client: Supabase client instance
        """
        self.db = supabase_client
    
    async def get_transactions(
        self,
        user_id: str,
        search: Optional[str] = None,
        category: Optional[str] = None,
        type_filter: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        sort_by: str = "transaction_date",
        order: str = "desc",
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List[TransactionResponse], int]:
        """
        Fetch paginated transactions with filters and sorting.
        
        Args:
            user_id: Current user ID
            search: Search keyword (searches description and category)
            category: Filter by category
            type_filter: Filter by type (income/expense)
            start_date: Filter by start date (inclusive)
            end_date: Filter by end date (inclusive)
            sort_by: Field to sort by (date, amount, category)
            order: Sort order (asc, desc)
            page: Page number (1-indexed)
            page_size: Number of records per page
            
        Returns:
            Tuple of (transactions list, total count)
            
        Raises:
            ValueError: If invalid sort_by or order parameters
        """
        # Validate parameters
        valid_sort_fields = ["transaction_date", "amount", "category"]
        valid_orders = ["asc", "desc"]
        
        if sort_by not in valid_sort_fields:
            sort_by = "transaction_date"
        if order.lower() not in valid_orders:
            order = "desc"
        
        try:
            # Start with base query filtered by user_id
            query = self.db.table(self.TABLE_NAME).select("*").eq("user_id", user_id)
            
            # Apply filters dynamically
            if search:
                # Search in description OR category (using OR logic)
                search_pattern = f"%{search}%"
                # Supabase doesn't support OR directly, so we fetch and filter
                # For production, consider using PostgreSQL full-text search
                query = query
            
            if category:
                query = query.ilike("category", f"%{category}%")
            
            if type_filter:
                query = query.eq("type", type_filter.lower())
            
            if start_date:
                query = query.gte("transaction_date", str(start_date))
            
            if end_date:
                query = query.lte("transaction_date", str(end_date))
            
            # Get total count for pagination
            count_response = self.db.table(self.TABLE_NAME).select("id", count="exact").eq("user_id", user_id)
            
            # Apply same filters to count
            if category:
                count_response = count_response.ilike("category", f"%{category}%")
            if type_filter:
                count_response = count_response.eq("type", type_filter.lower())
            if start_date:
                count_response = count_response.gte("transaction_date", str(start_date))
            if end_date:
                count_response = count_response.lte("transaction_date", str(end_date))
            
            count_data = count_response.execute()
            total_count = count_data.count if hasattr(count_data, 'count') else 0
            
            # Apply sorting
            query = query.order(sort_by, desc=(order.lower() == "desc"))
            
            # Apply pagination
            offset = (page - 1) * page_size
            query = query.range(offset, offset + page_size - 1)
            
            # Execute query
            response = query.execute()
            transactions_data = response.data
            
            # Apply search filter in memory (for OR logic on description and category)
            if search:
                search_lower = search.lower()
                transactions_data = [
                    t for t in transactions_data
                    if search_lower in t.get("description", "").lower() or
                       search_lower in t.get("category", "").lower()
                ]
                # Recalculate total_count after search filter
                total_count = len(transactions_data)
                # Re-apply pagination after filtering
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                transactions_data = transactions_data[start_idx:end_idx]
            
            # Convert to response models with warning flag
            transactions = [
                self._add_warning_flag(TransactionResponse(**t))
                for t in transactions_data
            ]
            
            return transactions, total_count
            
        except Exception as e:
            raise Exception(f"Error fetching transactions: {str(e)}")
    
    async def get_transaction_by_id(self, user_id: str, transaction_id: str) -> Optional[TransactionResponse]:
        """
        Fetch a single transaction by ID.
        
        Args:
            user_id: Current user ID (for authorization)
            transaction_id: Transaction ID to fetch
            
        Returns:
            TransactionResponse if found, None otherwise
        """
        try:
            response = (
                self.db.table(self.TABLE_NAME)
                .select("*")
                .eq("id", transaction_id)
                .eq("user_id", user_id)
                .single()
                .execute()
            )
            
            if response.data:
                transaction = TransactionResponse(**response.data)
                transaction = self._add_warning_flag(transaction)
                return transaction
            return None
            
        except Exception as e:
            raise Exception(f"Error fetching transaction: {str(e)}")
    
    async def create_transaction(
        self,
        user_id: str,
        transaction_data: TransactionCreate
    ) -> TransactionResponse:
        """
        Create a new transaction.
        
        Args:
            user_id: User ID for the transaction owner
            transaction_data: Transaction creation data
            
        Returns:
            Created TransactionResponse
            
        Raises:
            Exception: If database operation fails
        """
        try:
            insert_data = {
                "user_id": user_id,
                "description": transaction_data.description,
                "amount": str(transaction_data.amount),
                "type": transaction_data.type,
                "category": transaction_data.category,
                "transaction_date": str(transaction_data.transaction_date),
                "is_personal": transaction_data.is_personal,
            }
            
            response = (
                self.db.table(self.TABLE_NAME)
                .insert(insert_data)
                .execute()
            )
            
            if response.data:
                transaction = TransactionResponse(**response.data[0])
                transaction = self._add_warning_flag(transaction)
                return transaction
            
            raise Exception("Failed to create transaction")
            
        except Exception as e:
            raise Exception(f"Error creating transaction: {str(e)}")
    
    async def update_transaction(
        self,
        user_id: str,
        transaction_id: str,
        update_data: TransactionUpdate
    ) -> TransactionResponse:
        """
        Update an existing transaction.
        
        Args:
            user_id: Current user ID (for authorization)
            transaction_id: Transaction ID to update
            update_data: Partial transaction data to update
            
        Returns:
            Updated TransactionResponse
            
        Raises:
            Exception: If transaction not found or update fails
        """
        try:
            # Build update dictionary with only provided fields
            update_dict = {}
            
            if update_data.description is not None:
                update_dict["description"] = update_data.description
            if update_data.amount is not None:
                update_dict["amount"] = str(update_data.amount)
            if update_data.type is not None:
                update_dict["type"] = update_data.type
            if update_data.category is not None:
                update_dict["category"] = update_data.category
            if update_data.transaction_date is not None:
                update_dict["transaction_date"] = str(update_data.transaction_date)
            if update_data.is_personal is not None:
                update_dict["is_personal"] = update_data.is_personal
            
            if not update_dict:
                # If no fields to update, fetch and return current transaction
                return await self.get_transaction_by_id(user_id, transaction_id)
            
            response = (
                self.db.table(self.TABLE_NAME)
                .update(update_dict)
                .eq("id", transaction_id)
                .eq("user_id", user_id)
                .execute()
            )
            
            if response.data:
                transaction = TransactionResponse(**response.data[0])
                transaction = self._add_warning_flag(transaction)
                return transaction
            
            raise Exception("Transaction not found or not authorized")
            
        except Exception as e:
            raise Exception(f"Error updating transaction: {str(e)}")
    
    async def delete_transaction(self, user_id: str, transaction_id: str) -> bool:
        """
        Delete a transaction.
        
        Args:
            user_id: Current user ID (for authorization)
            transaction_id: Transaction ID to delete
            
        Returns:
            True if deletion successful
            
        Raises:
            Exception: If transaction not found or deletion fails
        """
        try:
            response = (
                self.db.table(self.TABLE_NAME)
                .delete()
                .eq("id", transaction_id)
                .eq("user_id", user_id)
                .execute()
            )
            
            # Supabase returns empty data on successful delete
            return True
            
        except Exception as e:
            raise Exception(f"Error deleting transaction: {str(e)}")
    
    async def get_transactions_for_export(
        self,
        user_id: str,
        search: Optional[str] = None,
        category: Optional[str] = None,
        type_filter: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch all matching transactions for export (no pagination).
        
        Args:
            user_id: Current user ID
            search: Search keyword
            category: Filter by category
            type_filter: Filter by type
            start_date: Filter by start date
            end_date: Filter by end date
            
        Returns:
            List of transaction dictionaries
        """
        try:
            query = self.db.table(self.TABLE_NAME).select("*").eq("user_id", user_id)
            
            if category:
                query = query.ilike("category", f"%{category}%")
            if type_filter:
                query = query.eq("type", type_filter.lower())
            if start_date:
                query = query.gte("transaction_date", str(start_date))
            if end_date:
                query = query.lte("transaction_date", str(end_date))
            
            # Order by date for export
            query = query.order("transaction_date", desc=True)
            
            response = query.execute()
            transactions_data = response.data
            
            # Apply search filter in memory
            if search:
                search_lower = search.lower()
                transactions_data = [
                    t for t in transactions_data
                    if search_lower in t.get("description", "").lower() or
                       search_lower in t.get("category", "").lower()
                ]
            
            return transactions_data
            
        except Exception as e:
            raise Exception(f"Error fetching transactions for export: {str(e)}")
    
    async def calculate_summary(
        self,
        user_id: str,
        search: Optional[str] = None,
        category: Optional[str] = None,
        type_filter: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Tuple[Decimal, Decimal]:
        """
        Calculate total income and expense for filtered transactions.
        
        Args:
            user_id: Current user ID
            search: Search keyword
            category: Filter by category
            type_filter: Filter by type
            start_date: Filter by start date
            end_date: Filter by end date
            
        Returns:
            Tuple of (total_income, total_expense)
        """
        transactions = await self.get_transactions_for_export(
            user_id=user_id,
            search=search,
            category=category,
            type_filter=type_filter,
            start_date=start_date,
            end_date=end_date
        )
        
        total_income = Decimal("0")
        total_expense = Decimal("0")
        
        for transaction in transactions:
            amount = Decimal(str(transaction.get("amount", 0)))
            if transaction.get("type") == "income":
                total_income += amount
            else:
                total_expense += amount
        
        return total_income, total_expense
    
    @staticmethod
    def _add_warning_flag(transaction: TransactionResponse) -> TransactionResponse:
        """
        Add personal expense warning flag if applicable.
        
        Args:
            transaction: TransactionResponse object
            
        Returns:
            Transaction with warning flag set if applicable
        """
        if (transaction.type == "expense" and 
            (transaction.category.lower() == "personal" or transaction.is_personal)):
            transaction.warning = "This expense is marked as personal and may affect business profit clarity."
        
        return transaction
