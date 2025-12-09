"""
Database initialization and health check endpoint.

Provides endpoints to check database status and create missing tables.
"""
from fastapi import APIRouter, HTTPException
from sqlalchemy import inspect, text
from typing import Dict, List

from app.db import engine, Base, create_tables
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["Database Admin"])


@router.get("/db/status")
async def get_database_status():
    """
    Check database connection and table status.
    
    Returns:
        Dictionary with database status and existing tables
    
    Raises:
        HTTPException 500: If database connection fails
    """
    try:
        # Check connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        # Get existing tables
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        # Expected tables
        expected_tables = [
            'users', 'accounts', 'categories', 'payment_methods', 'bills',
            'transactions', 'budgets', 'future_plans', 'reminders',
            'model_parameters', 'prediction_cache', 'model_performance_metrics',
            'user_benchmarks', 'recommendations_history', 'financial_goals',
            'financial_health_history'
        ]
        
        # Find missing tables
        missing_tables = [t for t in expected_tables if t not in existing_tables]
        
        return {
            'status': 'connected',
            'tables_count': len(existing_tables),
            'existing_tables': sorted(existing_tables),
            'expected_tables': expected_tables,
            'missing_tables': missing_tables,
            'all_tables_present': len(missing_tables) == 0
        }
        
    except Exception as e:
        logger.error(f"Database status check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {str(e)}"
        )


@router.post("/db/init")
async def initialize_database():
    """
    Initialize database by creating all missing tables.
    
    **Warning**: This will create all tables defined in the schema.
    Use with caution in production environments.
    
    Returns:
        Dictionary with initialization results
    
    Raises:
        HTTPException 500: If table creation fails
    """
    try:
        logger.info("Starting database initialization...")
        
        # Get existing tables before
        inspector = inspect(engine)
        existing_before = set(inspector.get_table_names())
        
        # Create all tables (will skip existing ones)
        create_tables()
        
        # Get existing tables after
        inspector = inspect(engine)
        existing_after = set(inspector.get_table_names())
        
        # Find newly created tables
        newly_created = existing_after - existing_before
        
        logger.info(f"Database initialization complete. Created {len(newly_created)} new tables.")
        
        return {
            'status': 'success',
            'message': 'Database initialized successfully',
            'tables_before': len(existing_before),
            'tables_after': len(existing_after),
            'newly_created': sorted(list(newly_created)),
            'newly_created_count': len(newly_created)
        }
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Database initialization failed: {str(e)}"
        )


@router.get("/db/tables")
async def list_database_tables():
    """
    List all tables in the database with their column information.
    
    Returns:
        Dictionary with table names and column details
    
    Raises:
        HTTPException 500: If query fails
    """
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        table_info = {}
        for table_name in tables:
            columns = inspector.get_columns(table_name)
            table_info[table_name] = {
                'column_count': len(columns),
                'columns': [
                    {
                        'name': col['name'],
                        'type': str(col['type']),
                        'nullable': col['nullable']
                    }
                    for col in columns
                ]
            }
        
        return {
            'status': 'success',
            'table_count': len(tables),
            'tables': table_info
        }
        
    except Exception as e:
        logger.error(f"Failed to list tables: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list tables: {str(e)}"
        )
