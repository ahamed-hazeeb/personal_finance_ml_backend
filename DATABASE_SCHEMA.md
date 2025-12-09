# Database Schema Documentation

This document describes the complete database schema for the Personal Finance ML Backend, aligned with the production PostgreSQL database structure.

## Overview

The database consists of 16 tables organized into three main categories:

1. **Core Tables**: User management, transactions, accounts, bills, and categories
2. **Financial Planning**: Budgets, goals, and reminders
3. **ML & Analytics**: Model parameters, predictions, benchmarks, and recommendations

## Core Tables

### users
Stores user account information and authentication details.

```sql
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    fcm_token TEXT,  -- Firebase Cloud Messaging token for notifications
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
```

**Row Level Security**: Enabled

### accounts
User financial accounts (checking, savings, credit cards, etc.).

```sql
CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    account_type TEXT NOT NULL,  -- 'checking', 'savings', 'credit', etc.
    balance NUMERIC NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_accounts_user_id ON accounts(user_id);
```

**Row Level Security**: Enabled

### categories
Transaction categories (user-specific or global).

```sql
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,  -- NULL for global categories
    name TEXT NOT NULL,
    type TEXT NOT NULL,  -- 'income', 'expense', 'savings'
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT categories_user_id_name_type_key UNIQUE (user_id, name, type)
);

CREATE INDEX idx_categories_user_id ON categories(user_id);
```

**Row Level Security**: Enabled

### payment_methods
User payment methods (cards, UPI, cash, etc.).

```sql
CREATE TABLE payment_methods (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    method_name TEXT NOT NULL,  -- 'credit_card', 'debit_card', 'upi', 'cash', etc.
    details JSONB,  -- Card last 4 digits, UPI ID, etc.
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_payment_methods_user_id ON payment_methods(user_id);
```

**Row Level Security**: Enabled

### bills
Bills and recurring payments tracking.

```sql
CREATE TABLE bills (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    bill_name TEXT NOT NULL,
    due_date DATE NOT NULL,
    amount NUMERIC NOT NULL,
    status TEXT DEFAULT 'unpaid',  -- 'unpaid', 'paid', 'overdue'
    reminder_sent INTEGER DEFAULT 0,
    payment_reference TEXT,
    payment_method_id INTEGER REFERENCES payment_methods(id) ON DELETE SET NULL,
    is_recurring BOOLEAN DEFAULT false,
    recurrence_frequency TEXT,  -- 'monthly', 'quarterly', 'yearly'
    reminder_enabled BOOLEAN DEFAULT false,
    reminder_days_before INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_bills_user_id ON bills(user_id);
```

**Row Level Security**: Enabled

### transactions
All financial transactions (income, expenses, savings).

```sql
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    account_id INTEGER REFERENCES accounts(id) ON DELETE SET NULL,
    amount NUMERIC NOT NULL,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    type TEXT NOT NULL,  -- 'expense', 'income', 'savings'
    date DATE NOT NULL,
    note TEXT DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    receiver_name TEXT,
    payment_method TEXT,
    bill_id INTEGER REFERENCES bills(id) ON DELETE SET NULL
);

CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_date ON transactions(date);
CREATE INDEX idx_transactions_bill_id ON transactions(bill_id);
```

**Row Level Security**: Enabled

## Financial Planning Tables

### budgets
Budget planning and tracking.

```sql
CREATE TABLE budgets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    amount NUMERIC NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status TEXT DEFAULT 'active',  -- 'active', 'completed', 'cancelled'
    model_parameters_id INTEGER REFERENCES model_parameters(id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_budgets_user_id ON budgets(user_id);
```

**Row Level Security**: Enabled

### future_plans
Future financial plans and goals (legacy table).

```sql
CREATE TABLE future_plans (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    goal_name TEXT NOT NULL,
    target_amount NUMERIC NOT NULL,
    current_savings NUMERIC NOT NULL DEFAULT 0.00,
    target_date DATE NOT NULL,
    monthly_savings NUMERIC NOT NULL,
    model_parameters_id INTEGER REFERENCES model_parameters(id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_future_plans_user_id ON future_plans(user_id);
```

**Row Level Security**: Enabled

**Note**: This is a legacy table. New features should use the `financial_goals` table.

### financial_goals
User financial goals (Phase 2-4 implementation).

```sql
CREATE TABLE financial_goals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    goal_name VARCHAR(200) NOT NULL,
    target_amount NUMERIC NOT NULL,
    current_amount NUMERIC NOT NULL DEFAULT 0,
    target_date DATE,
    monthly_contribution NUMERIC,
    status VARCHAR(20) NOT NULL DEFAULT 'active',  -- 'active', 'completed', 'abandoned'
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_status ON financial_goals(user_id, status);
```

### reminders
Reminders for bills and financial events.

```sql
CREATE TABLE reminders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    reminder_date DATE NOT NULL,
    reminder_time TIME,
    days_before INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',  -- 'pending', 'sent', 'dismissed'
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_reminders_user_id ON reminders(user_id);
```

**Row Level Security**: Enabled

## ML & Analytics Tables

### model_parameters
Trained ML model parameters and metadata.

```sql
CREATE TABLE model_parameters (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    model_type TEXT NOT NULL,  -- 'linear_regression', 'expense_forecast', etc.
    slope NUMERIC,
    intercept NUMERIC,
    parameters JSONB,  -- Additional parameters as JSON
    last_trained_date DATE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    target_table TEXT
);

CREATE INDEX idx_model_parameters_user_id ON model_parameters(user_id);
```

**Row Level Security**: Enabled

### prediction_cache
Cache for ML prediction results.

```sql
CREATE TABLE prediction_cache (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    prediction_type VARCHAR(50) NOT NULL,
    input_hash VARCHAR(64) NOT NULL,  -- MD5 hash of input parameters
    result JSON NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_user_type_hash ON prediction_cache(user_id, prediction_type, input_hash);
CREATE INDEX idx_expires ON prediction_cache(expires_at);
```

### model_performance_metrics
Track ML model performance over time.

```sql
CREATE TABLE model_performance_metrics (
    id SERIAL PRIMARY KEY,
    model_id INTEGER NOT NULL REFERENCES model_parameters(id),
    actual_value NUMERIC,
    predicted_value NUMERIC,
    error_percentage NUMERIC,
    mae NUMERIC,  -- Mean Absolute Error
    rmse NUMERIC,  -- Root Mean Squared Error
    r2_score NUMERIC,  -- R² Score
    recorded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_model_recorded ON model_performance_metrics(model_id, recorded_at);
```

### user_benchmarks
Anonymized user benchmarks for peer comparison.

```sql
CREATE TABLE user_benchmarks (
    id SERIAL PRIMARY KEY,
    age_group VARCHAR(20) NOT NULL,  -- '20-30', '30-40', etc.
    income_bracket VARCHAR(20) NOT NULL,  -- '0-30k', '30-50k', etc.
    avg_savings_rate NUMERIC,
    avg_expense_ratio NUMERIC,
    avg_health_score NUMERIC,
    sample_size INTEGER,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_age_income ON user_benchmarks(age_group, income_bracket);
```

### recommendations_history
Track recommendations provided to users.

```sql
CREATE TABLE recommendations_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    recommendation_type VARCHAR(50) NOT NULL,  -- 'habit', 'opportunity', 'nudge', etc.
    category VARCHAR(50),
    recommendation TEXT NOT NULL,
    context JSON,
    accepted BOOLEAN,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_type ON recommendations_history(user_id, recommendation_type);
CREATE INDEX idx_created ON recommendations_history(created_at);
```

### financial_health_history
Financial health score tracking (Phase 2-4 feature).

```sql
CREATE TABLE financial_health_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    score INTEGER NOT NULL,  -- Overall score 0-100
    savings_rate_score NUMERIC,
    expense_consistency_score NUMERIC,
    emergency_fund_score NUMERIC,
    debt_ratio_score NUMERIC,
    goal_progress_score NUMERIC,
    grade VARCHAR(2),  -- A, B, C, D, F
    recommendations JSONB,
    calculated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_calculated ON financial_health_history(user_id, calculated_at);
```

## Entity Relationships

### User-Centric Relationships
- A **User** has many **Accounts**
- A **User** has many **Categories**
- A **User** has many **PaymentMethods**
- A **User** has many **Bills**
- A **User** has many **Transactions**
- A **User** has many **Budgets**
- A **User** has many **FinancialGoals**
- A **User** has many **Reminders**

### Transaction Relationships
- A **Transaction** belongs to a **User**
- A **Transaction** may belong to an **Account**
- A **Transaction** may belong to a **Category**
- A **Transaction** may be linked to a **Bill**

### ML & Analytics Relationships
- **ModelParameters** belong to a **User**
- **PredictionCache** entries belong to a **User**
- **ModelPerformanceMetrics** reference **ModelParameters**
- **RecommendationsHistory** entries belong to a **User**
- **FinancialHealthHistory** entries belong to a **User**

### Budget & Goal Relationships
- **Budgets** may reference **ModelParameters** for ML-generated budgets
- **FuturePlans** may reference **ModelParameters** for ML predictions

## Row Level Security (RLS)

All user-facing tables have Row Level Security enabled to ensure data isolation:
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

## Migration Notes

### From Legacy to New Schema

The system maintains backward compatibility:

1. **Transactions**: The `transactions` table now uses `category_id` (FK to categories) instead of a simple `category` string
2. **Goals**: New features should use `financial_goals` table instead of `future_plans`
3. **Authentication**: User management is now fully integrated with the `users` table

### Running Migrations

```bash
# Run the migration script
python scripts/migrate_database.py
```

This will:
1. Create all missing tables
2. Verify table structure
3. Report on newly created tables

## Usage in Code

### SQLAlchemy Models

All tables are defined as SQLAlchemy models in `app/db.py`:

```python
from app.db import User, Transaction, Bill, Category, Account
from app.db import FinancialHealthHistory, FinancialGoals
from app.db import get_db

# Use dependency injection in FastAPI
@router.post("/example")
async def example_endpoint(db: Session = Depends(get_db)):
    # Query database
    users = db.query(User).all()
    return users
```

## Best Practices

1. **Always use foreign keys** to maintain referential integrity
2. **Enable RLS** on new user-facing tables
3. **Add indexes** on frequently queried columns
4. **Use JSONB** for flexible metadata storage
5. **Include timestamps** (created_at, updated_at) on all tables
6. **Use CASCADE** on user deletions to clean up related data
7. **Use SET NULL** on optional foreign keys
