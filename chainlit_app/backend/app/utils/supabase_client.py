"""
Supabase client initialization and utilities.

This module handles the connection to Supabase PostgreSQL database
and provides utility functions for database operations.
"""

import os
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class SupabaseManager:
    """Manager for Supabase client initialization and connection."""
    
    _instance: Optional[Client] = None
    
    @classmethod
    def get_client(cls) -> Client:
        """
        Get or create Supabase client instance.
        
        Returns:
            Supabase Client instance
            
        Raises:
            ValueError: If SUPABASE_URL or SUPABASE_KEY not set
        """
        if cls._instance is None:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            
            if not supabase_url or not supabase_key:
                raise ValueError(
                    "SUPABASE_URL and SUPABASE_KEY environment variables must be set"
                )
            
            cls._instance = create_client(supabase_url, supabase_key)
        
        return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        """
        Reset the Supabase client instance.
        Useful for testing or reinitializing the connection.
        """
        cls._instance = None


def get_supabase_client() -> Client:
    """
    Dependency injection function for Supabase client.
    
    Returns:
        Supabase Client instance
        
    Example:
        Can be used as a FastAPI dependency:
        @app.get("/transactions")
        async def get_transactions(client: Client = Depends(get_supabase_client)):
            ...
    """
    return SupabaseManager.get_client()
