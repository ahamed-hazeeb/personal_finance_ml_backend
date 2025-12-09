# Database Setup and Initialization Guide

## Quick Start

If you encounter the error `relation "financial_health_history" does not exist` or similar database errors, you need to initialize the database tables.

### Option 1: Using the API (Recommended for Development)

1. **Check database status:**
   ```bash
   curl http://localhost:8000/api/v1/admin/db/status
   ```

   This will show you:
   - Existing tables
   - Missing tables
   - Connection status

2. **Initialize missing tables:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/admin/db/init
   ```

   This will create all missing tables without affecting existing ones.

### Option 2: Using the Migration Script

Run the migration script directly:

```bash
cd /path/to/personal_finance_ml_backend
python scripts/migrate_database.py
```

This will:
- Check existing tables
- Create all missing tables
- Verify the migration was successful

### Option 3: Using Python Directly

```python
from app.db import create_tables

# Create all tables (skips existing ones)
create_tables()
```

## Expected Tables

The system requires these 16 tables:

### Core Tables
1. **users** - User authentication and management
2. **accounts** - Financial accounts (checking, savings, etc.)
3. **categories** - Transaction categories
4. **payment_methods** - Payment method tracking
5. **bills** - Bill management
6. **transactions** - All financial transactions
7. **budgets** - Budget planning
8. **future_plans** - Legacy goals table
9. **reminders** - Bill and event reminders

### ML & Analytics Tables
10. **model_parameters** - ML model metadata
11. **prediction_cache** - Cached predictions
12. **model_performance_metrics** - Model performance tracking
13. **user_benchmarks** - Anonymized benchmarks
14. **recommendations_history** - Recommendation tracking
15. **financial_goals** - User financial goals
16. **financial_health_history** - Health score tracking

## Troubleshooting

### Error: `relation "financial_health_history" does not exist`

**Solution:**
1. Check if the table exists:
   ```bash
   curl http://localhost:8000/api/v1/admin/db/status
   ```

2. If missing, initialize the database:
   ```bash
   curl -X POST http://localhost:8000/api/v1/admin/db/init
   ```

3. Verify the table was created:
   ```bash
   curl http://localhost:8000/api/v1/admin/db/status
   ```

### Error: Database connection failed

**Solution:**
1. Verify PostgreSQL is running
2. Check your `.env` file has correct `DATABASE_URL`
3. Test connection:
   ```bash
   psql $DATABASE_URL -c "SELECT version();"
   ```

### Error: Permission denied

**Solution:**
Ensure your database user has CREATE TABLE permissions:
```sql
GRANT CREATE ON DATABASE your_db TO your_user;
```

## Production Deployment

For production environments:

1. **Manual Migration (Recommended):**
   ```bash
   # On production server
   python scripts/migrate_database.py
   ```

2. **Docker Deployment:**
   ```bash
   # Run migration after container starts
   docker exec -it ml_backend python scripts/migrate_database.py
   ```

3. **Kubernetes:**
   ```yaml
   # Add as init container
   initContainers:
   - name: db-migration
     image: your-app:latest
     command: ["python", "scripts/migrate_database.py"]
   ```

## Schema Changes

When updating the schema:

1. Update models in `app/db.py`
2. Run migration: `python scripts/migrate_database.py`
3. Verify: `curl http://localhost:8000/api/v1/admin/db/status`

## Foreign Key Relationships

All tables now have proper foreign key constraints:

- `ON DELETE CASCADE` - Automatically deletes related records when user is deleted
- `ON DELETE SET NULL` - Sets FK to NULL when referenced record is deleted

Example:
```sql
-- When a user is deleted, all their transactions are automatically deleted
transactions.user_id -> users.user_id (ON DELETE CASCADE)

-- When a bill is deleted, transaction's bill_id is set to NULL
transactions.bill_id -> bills.id (ON DELETE SET NULL)
```

## Row Level Security (RLS)

The following tables have RLS enabled in production:
- users
- accounts
- categories
- payment_methods
- bills
- transactions
- budgets
- future_plans
- reminders
- model_parameters

Ensure RLS policies are configured in your PostgreSQL database.

## API Endpoints for Database Management

### GET /api/v1/admin/db/status
Check database connection and table status.

**Response:**
```json
{
  "status": "connected",
  "tables_count": 16,
  "existing_tables": ["users", "transactions", ...],
  "missing_tables": [],
  "all_tables_present": true
}
```

### POST /api/v1/admin/db/init
Initialize database by creating missing tables.

**Response:**
```json
{
  "status": "success",
  "message": "Database initialized successfully",
  "tables_before": 10,
  "tables_after": 16,
  "newly_created": ["financial_health_history", ...],
  "newly_created_count": 6
}
```

### GET /api/v1/admin/db/tables
List all tables with column information.

**Response:**
```json
{
  "status": "success",
  "table_count": 16,
  "tables": {
    "users": {
      "column_count": 7,
      "columns": [...]
    }
  }
}
```

## Best Practices

1. **Always backup** before running migrations in production
2. **Test migrations** in staging environment first
3. **Check status** before and after migration
4. **Monitor logs** during migration
5. **Use transactions** for complex schema changes

## Support

For issues or questions:
- Check `/docs` endpoint for API documentation
- Review `DATABASE_SCHEMA.md` for detailed schema documentation
- Check application logs for detailed error messages
