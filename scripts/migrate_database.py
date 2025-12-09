"""
Database migration script for Phase 2-4 features.

This script creates new tables for:
- Financial health history tracking
- User benchmarks (already in db.py)
- Model performance metrics (already in db.py)
- Recommendations history (already in db.py)
- Financial goals (already in db.py)
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import create_tables, Base, engine
from sqlalchemy import inspect


def check_table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def run_migration():
    """Run database migration."""
    print("🚀 Starting database migration for Phase 2-4 features...")
    print()
    
    # Check existing tables
    existing_tables = inspect(engine).get_table_names()
    print(f"📊 Found {len(existing_tables)} existing tables:")
    for table in existing_tables:
        print(f"  ✓ {table}")
    print()
    
    # New tables to create
    new_tables = [
        'financial_health_history',
        'user_benchmarks',
        'model_performance_metrics',
        'recommendations_history',
        'financial_goals'
    ]
    
    print("🔨 Creating new tables...")
    
    # Create all tables (will skip existing ones)
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Table creation completed")
        print()
    except Exception as e:
        print(f"❌ Error creating tables: {str(e)}")
        return False
    
    # Verify new tables
    updated_tables = inspect(engine).get_table_names()
    newly_created = set(updated_tables) - set(existing_tables)
    
    if newly_created:
        print(f"✨ Created {len(newly_created)} new tables:")
        for table in newly_created:
            print(f"  ✓ {table}")
    else:
        print("ℹ️  All tables already exist (no new tables created)")
    
    print()
    print("✅ Migration completed successfully!")
    print()
    print("📋 Summary:")
    print(f"  Total tables: {len(updated_tables)}")
    print(f"  Newly created: {len(newly_created)}")
    print()
    
    return True


def verify_migration():
    """Verify that all required tables exist."""
    print("🔍 Verifying migration...")
    print()
    
    required_tables = [
        'transactions',
        'model_parameters',
        'prediction_cache',
        'financial_health_history',
        'user_benchmarks',
        'model_performance_metrics',
        'recommendations_history',
        'financial_goals'
    ]
    
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    all_exist = True
    for table in required_tables:
        exists = table in existing_tables
        status = "✅" if exists else "❌"
        print(f"  {status} {table}")
        if not exists:
            all_exist = False
    
    print()
    if all_exist:
        print("✅ All required tables exist!")
    else:
        print("❌ Some required tables are missing!")
    
    return all_exist


if __name__ == "__main__":
    print("=" * 60)
    print("Database Migration - Phase 2-4 Features")
    print("=" * 60)
    print()
    
    try:
        # Run migration
        success = run_migration()
        
        if success:
            # Verify migration
            verify_migration()
            print()
            print("=" * 60)
            print("✅ Migration completed successfully!")
            print("=" * 60)
        else:
            print()
            print("=" * 60)
            print("❌ Migration failed!")
            print("=" * 60)
            sys.exit(1)
    
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Migration failed with error: {str(e)}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        sys.exit(1)
