"""
Prediction script for personal finance ML models.

This script loads trained models and makes predictions for future expenses,
category spending, and savings trajectory with comprehensive reporting.
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import ExpenseForecaster, CategorySpendingPredictor, SavingsForecaster
from utils.metrics import format_prediction_report


def load_data(data_path: str) -> pd.DataFrame:
    """
    Load monthly financial data from CSV.
    
    Args:
        data_path: Path to the CSV file
        
    Returns:
        DataFrame with monthly data
    """
    df = pd.read_csv(data_path)
    
    # Convert year_month to period if it's a string
    if 'year_month' in df.columns and df['year_month'].dtype == 'object':
        df['year_month'] = pd.to_datetime(df['year_month']).dt.to_period('M')
    
    return df


def predict_all(
    monthly_df: pd.DataFrame,
    models_dir: str = './models/saved'
) -> dict:
    """
    Make predictions using all trained models.
    
    Args:
        monthly_df: DataFrame with historical monthly data
        models_dir: Directory containing trained models
        
    Returns:
        Dictionary with all predictions
    """
    predictions = {}
    
    # Expense Forecaster
    expense_model_path = f"{models_dir}/expense_forecaster.pkl"
    if os.path.exists(expense_model_path):
        print("\n" + "="*60)
        print("MONTHLY EXPENSE FORECAST")
        print("="*60)
        
        expense_model = ExpenseForecaster()
        expense_model.load(expense_model_path)
        
        forecast = expense_model.forecast_next_month(monthly_df, confidence_level=0.95)
        
        predictions['monthly_expense'] = {
            'predicted': forecast['predicted_expense'],
            'confidence_interval': forecast['confidence_interval']
        }
        
        print(f"\nPredicted Total Expense for Next Month: ${forecast['predicted_expense']:,.2f}")
        print(f"95% Confidence Interval: [${forecast['confidence_interval'][0]:,.2f}, ${forecast['confidence_interval'][1]:,.2f}]")
        
        # Historical comparison
        avg_expense = monthly_df['total_expense'].mean()
        recent_avg = monthly_df['total_expense'].iloc[-3:].mean()
        print(f"\nHistorical Average: ${avg_expense:,.2f}")
        print(f"Recent 3-Month Average: ${recent_avg:,.2f}")
        print(f"Predicted vs Historical: {((forecast['predicted_expense'] / avg_expense) - 1) * 100:+.2f}%")
    
    # Category Predictor
    category_model_path = f"{models_dir}/category_predictor.pkl"
    if os.path.exists(category_model_path):
        print("\n" + "="*60)
        print("CATEGORY-WISE SPENDING PREDICTIONS")
        print("="*60)
        
        category_model = CategorySpendingPredictor()
        category_model.load(category_model_path)
        
        # Category forecasts
        category_forecasts = category_model.forecast_categories(monthly_df, confidence_level=0.95)
        
        predictions['category_expenses'] = {
            cat: info['predicted'] for cat, info in category_forecasts.items()
        }
        
        print("\nPredicted Spending by Category:")
        for category, info in category_forecasts.items():
            print(f"\n  {category}:")
            print(f"    Predicted: ${info['predicted']:,.2f}")
            print(f"    95% CI: [${info['confidence_interval'][0]:,.2f}, ${info['confidence_interval'][1]:,.2f}]")
            
            # Historical comparison
            if category in monthly_df.columns:
                hist_avg = monthly_df[category].mean()
                change = ((info['predicted'] / hist_avg) - 1) * 100
                print(f"    vs Historical Avg: {change:+.2f}%")
        
        # Overspending risk analysis
        print("\n" + "-"*60)
        print("OVERSPENDING RISK ANALYSIS")
        print("-"*60)
        
        risk_report = category_model.detect_overspending_risks(monthly_df, threshold=1.2)
        predictions['risk_analysis'] = risk_report
        
        at_risk_categories = [cat for cat, info in risk_report.items() if info['at_risk']]
        
        if at_risk_categories:
            print("\n⚠️  Categories at Risk of Overspending (>20% above avg):")
            for category in at_risk_categories:
                info = risk_report[category]
                print(f"\n  {category}:")
                print(f"    Predicted: ${info['predicted']:,.2f}")
                print(f"    Historical Avg: ${info['historical_avg']:,.2f}")
                print(f"    Over Budget: ${info['excess_amount']:,.2f}")
                print(f"    Ratio: {info['ratio']:.2f}x")
        else:
            print("\n✅ No categories at risk of overspending")
        
        # Budget recommendations
        print("\n" + "-"*60)
        print("BUDGET RECOMMENDATIONS")
        print("-"*60)
        
        total_income = monthly_df['total_income'].iloc[-1]
        budget_recs = category_model.generate_budget_recommendations(
            monthly_df,
            total_budget=total_income,
            safety_margin=0.1
        )
        
        predictions['budget_recommendations'] = budget_recs
        
        print(f"\nBased on income of ${total_income:,.2f}:")
        for category, amount in budget_recs.items():
            print(f"  {category}: ${amount:,.2f}")
    
    # Savings Forecaster
    savings_model_path = f"{models_dir}/savings_forecaster.pkl"
    if os.path.exists(savings_model_path):
        print("\n" + "="*60)
        print("SAVINGS TRAJECTORY FORECAST")
        print("="*60)
        
        savings_model = SavingsForecaster()
        savings_model.load(savings_model_path)
        
        trajectory = savings_model.forecast_trajectory(
            monthly_df,
            periods=[3, 6, 12],
            confidence_level=0.95
        )
        
        predictions['savings_trajectory'] = {
            period: info['projected_savings'] for period, info in trajectory.items() if period != 'current_savings'
        }
        
        print(f"\nCurrent Cumulative Savings: ${trajectory['current_savings']:,.2f}")
        print("\nProjected Savings:")
        
        for period in ['3_months', '6_months', '12_months']:
            if period in trajectory:
                info = trajectory[period]
                print(f"\n  {period.replace('_', ' ').title()}:")
                print(f"    Projected Total: ${info['projected_savings']:,.2f}")
                print(f"    Growth: +${info['growth_from_current']:,.2f}")
                print(f"    95% CI: [${info['confidence_interval'][0]:,.2f}, ${info['confidence_interval'][1]:,.2f}]")
                print(f"    Monthly Rate: ${info['monthly_savings_rate']:,.2f}/month")
        
        # Savings metrics
        print("\n" + "-"*60)
        print("SAVINGS ANALYSIS")
        print("-"*60)
        
        metrics = savings_model.calculate_savings_metrics(monthly_df)
        
        print(f"\nAverage Monthly Savings: ${metrics['avg_monthly_savings']:,.2f}")
        print(f"Savings Rate: {metrics['savings_rate']:.2f}%")
        print(f"Savings Volatility: ${metrics['savings_volatility']:,.2f}")
        print(f"Savings Trend: ${metrics.get('savings_trend', 0):,.2f}/month")
        print(f"Months with Positive Savings: {metrics['months_positive_savings']}")
        print(f"Months with Negative Savings: {metrics['months_negative_savings']}")
        
        # Financial health assessment
        print("\n" + "-"*60)
        print("FINANCIAL HEALTH ASSESSMENT")
        print("-"*60)
        
        assessment = savings_model.assess_financial_health(monthly_df)
        
        print(f"\nStatus: {assessment['status']}")
        print(f"Message: {assessment['message']}")
        
        if assessment['recommendations']:
            print("\nRecommendations:")
            for i, rec in enumerate(assessment['recommendations'], 1):
                print(f"  {i}. {rec}")
    
    return predictions


def main():
    """
    Main prediction execution.
    """
    parser = argparse.ArgumentParser(description='Make predictions using trained models')
    parser.add_argument(
        '--data',
        type=str,
        default='./data/sample_monthly_data.csv',
        help='Path to monthly data CSV file'
    )
    parser.add_argument(
        '--models-dir',
        type=str,
        default='./models/saved',
        help='Directory containing trained models'
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("PERSONAL FINANCE PREDICTIONS")
    print("="*60)
    print(f"Data path: {args.data}")
    print(f"Models directory: {args.models_dir}")
    
    # Check if models exist
    if not os.path.exists(args.models_dir):
        print(f"\n❌ Error: Models directory not found: {args.models_dir}")
        print("Please train models first using train_models.py")
        return
    
    # Load data
    print("\nLoading data...")
    monthly_df = load_data(args.data)
    print(f"Loaded {len(monthly_df)} months of data")
    print(f"Date range: {monthly_df['year_month'].min()} to {monthly_df['year_month'].max()}")
    
    # Make predictions
    predictions = predict_all(monthly_df, args.models_dir)
    
    print("\n" + "="*60)
    print("PREDICTIONS COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
