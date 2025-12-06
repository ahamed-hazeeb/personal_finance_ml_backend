"""
Sample data generator for personal finance ML models.

This module generates realistic dummy transaction data for development and testing.
It creates historical expense and income data with multiple spending categories.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import random


# Expense categories with typical spending ranges (monthly)
EXPENSE_CATEGORIES = {
    'Food': (200, 600),
    'Transport': (100, 300),
    'Shopping': (150, 500),
    'Entertainment': (50, 200),
    'Utilities': (100, 250),
    'Healthcare': (50, 300),
    'Education': (0, 400),
    'Other': (50, 200)
}


def generate_transaction_data(
    num_months: int = 12,
    start_date: str = None,
    base_income: float = 5000.0,
    income_growth_rate: float = 0.02,
    expense_volatility: float = 0.15,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generate synthetic transaction data for personal finance analysis.
    
    Args:
        num_months: Number of months of historical data to generate
        start_date: Starting date (YYYY-MM-DD format). If None, starts from current date - num_months
        base_income: Base monthly income
        income_growth_rate: Monthly income growth rate (default 2%)
        expense_volatility: Volatility factor for expenses (default 15%)
        seed: Random seed for reproducibility
        
    Returns:
        DataFrame with columns: date, category, amount, type (income/expense)
    """
    random.seed(seed)
    np.random.seed(seed)
    
    if start_date is None:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=num_months * 30)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = start_date + timedelta(days=num_months * 30)
    
    transactions = []
    
    # Generate monthly data
    current_date = start_date
    for month_idx in range(num_months):
        # Generate income for the month
        monthly_income = base_income * (1 + income_growth_rate) ** month_idx
        monthly_income += np.random.normal(0, monthly_income * 0.05)  # Small variance
        
        transactions.append({
            'date': current_date,
            'category': 'Income',
            'amount': round(monthly_income, 2),
            'type': 'income'
        })
        
        # Generate expenses for each category
        for category, (min_amount, max_amount) in EXPENSE_CATEGORIES.items():
            # Base amount with some monthly variation
            base_amount = (min_amount + max_amount) / 2
            
            # Add trend (slight increase over time)
            trend = base_amount * 0.01 * month_idx
            
            # Add seasonal effect (higher in certain months)
            seasonal_factor = 1.0
            month_of_year = (current_date.month - 1) % 12
            if category == 'Shopping' and month_of_year in [10, 11]:  # Holiday season
                seasonal_factor = 1.3
            elif category == 'Entertainment' and month_of_year in [5, 6, 7]:  # Summer
                seasonal_factor = 1.2
            elif category == 'Utilities' and month_of_year in [0, 1, 11]:  # Winter
                seasonal_factor = 1.15
            
            # Calculate final amount with volatility
            amount = (base_amount + trend) * seasonal_factor
            amount += np.random.normal(0, amount * expense_volatility)
            amount = max(0, amount)  # Ensure non-negative
            
            # Generate multiple transactions per category (1-5 transactions)
            num_transactions = random.randint(1, 5)
            transaction_amounts = np.random.dirichlet(np.ones(num_transactions)) * amount
            
            for trans_idx, trans_amount in enumerate(transaction_amounts):
                trans_date = current_date + timedelta(days=random.randint(0, 28))
                transactions.append({
                    'date': trans_date,
                    'category': category,
                    'amount': round(trans_amount, 2),
                    'type': 'expense'
                })
        
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    # Create DataFrame
    df = pd.DataFrame(transactions)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    return df


def aggregate_monthly_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate transaction data to monthly summary with category-wise breakdown.
    
    Args:
        df: Transaction DataFrame from generate_transaction_data()
        
    Returns:
        DataFrame with monthly aggregated data including:
        - year_month: YYYY-MM format
        - total_income: Total monthly income
        - total_expense: Total monthly expense
        - savings: Income - Expense
        - Category columns: Expense per category
    """
    df = df.copy()
    df['year_month'] = df['date'].dt.to_period('M')
    
    # Aggregate income
    income_df = df[df['type'] == 'income'].groupby('year_month')['amount'].sum().reset_index()
    income_df.columns = ['year_month', 'total_income']
    
    # Aggregate expenses by category
    expense_df = df[df['type'] == 'expense'].pivot_table(
        index='year_month',
        columns='category',
        values='amount',
        aggfunc='sum',
        fill_value=0
    ).reset_index()
    
    # Merge income and expense data
    monthly_df = income_df.merge(expense_df, on='year_month', how='left')
    
    # Calculate totals
    category_columns = [col for col in monthly_df.columns if col not in ['year_month', 'total_income']]
    monthly_df['total_expense'] = monthly_df[category_columns].sum(axis=1)
    monthly_df['savings'] = monthly_df['total_income'] - monthly_df['total_expense']
    
    return monthly_df


def generate_sample_dataset(
    output_path: str = None,
    num_months: int = 12
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate and save sample datasets for development and testing.
    
    Args:
        output_path: Path to save the CSV files. If None, doesn't save to disk.
        num_months: Number of months of data to generate
        
    Returns:
        Tuple of (transaction_df, monthly_df)
    """
    print(f"Generating {num_months} months of sample transaction data...")
    transaction_df = generate_transaction_data(num_months=num_months)
    
    print("Aggregating to monthly data...")
    monthly_df = aggregate_monthly_data(transaction_df)
    
    if output_path:
        trans_path = f"{output_path}/sample_transactions.csv"
        monthly_path = f"{output_path}/sample_monthly_data.csv"
        
        transaction_df.to_csv(trans_path, index=False)
        print(f"Transaction data saved to: {trans_path}")
        
        # Convert period to string for CSV export
        monthly_export = monthly_df.copy()
        monthly_export['year_month'] = monthly_export['year_month'].astype(str)
        monthly_export.to_csv(monthly_path, index=False)
        print(f"Monthly data saved to: {monthly_path}")
    
    print(f"\nSummary:")
    print(f"  Total transactions: {len(transaction_df)}")
    print(f"  Date range: {transaction_df['date'].min()} to {transaction_df['date'].max()}")
    print(f"  Total income: ${transaction_df[transaction_df['type']=='income']['amount'].sum():,.2f}")
    print(f"  Total expenses: ${transaction_df[transaction_df['type']=='expense']['amount'].sum():,.2f}")
    
    return transaction_df, monthly_df


if __name__ == "__main__":
    # Generate sample data
    transaction_df, monthly_df = generate_sample_dataset(
        output_path="./data",
        num_months=12
    )
    
    print("\nFirst few transactions:")
    print(transaction_df.head(10))
    
    print("\nMonthly summary:")
    print(monthly_df)
