# Usage Examples

This document provides practical examples of using the Personal Finance ML Backend.

## Quick Start

### 1. Generate Sample Data

```bash
cd data
python sample_data_generator.py
```

This creates:
- `sample_transactions.csv` - 12 months of transaction records
- `sample_monthly_data.csv` - Monthly aggregated financial data

### 2. Train Models

Train all three models (takes ~30 seconds):

```bash
python scripts/train_models.py
```

Output includes:
- Training and test metrics (MAE, RMSE, MAPE, R²)
- Cross-validation scores
- Feature importance rankings
- Saved models in `models/saved/`

### 3. Make Predictions

```bash
python scripts/predict.py
```

You'll see:
- Monthly expense forecast with 95% confidence interval
- Category-wise spending predictions
- Overspending risk analysis
- Budget recommendations
- Savings trajectory (3, 6, 12 months)
- Financial health assessment

## Python API Examples

### Example 1: Expense Forecasting

```python
from models import ExpenseForecaster
import pandas as pd

# Load your data
monthly_df = pd.read_csv('data/sample_monthly_data.csv')
monthly_df['year_month'] = pd.to_datetime(monthly_df['year_month']).dt.to_period('M')

# Train model
model = ExpenseForecaster(n_estimators=100, max_depth=10)
X, y = model.prepare_data(monthly_df)
model.train(X[:-3], y[:-3])

# Forecast next month
forecast = model.forecast_next_month(monthly_df)
print(f"Predicted: ${forecast['predicted_expense']:.2f}")
print(f"95% CI: ${forecast['confidence_interval'][0]:.2f} - ${forecast['confidence_interval'][1]:.2f}")

# Save model
model.save('my_expense_model.pkl')
```

### Example 2: Category-wise Prediction with Risk Analysis

```python
from models import CategorySpendingPredictor

# Initialize and train
model = CategorySpendingPredictor()
X, y = model.prepare_data(monthly_df)
model.train(X[:-3], y[:-3])

# Get predictions for all categories
forecasts = model.forecast_categories(monthly_df)
for category, info in forecasts.items():
    print(f"{category}: ${info['predicted']:.2f}")

# Detect overspending risks
risks = model.detect_overspending_risks(monthly_df, threshold=1.2)
at_risk = [cat for cat, info in risks.items() if info['at_risk']]
print(f"\nAt risk: {at_risk}")

# Generate budget recommendations
total_income = monthly_df['total_income'].iloc[-1]
budget = model.generate_budget_recommendations(
    monthly_df, 
    total_budget=total_income,
    safety_margin=0.1  # 10% emergency buffer
)
print(f"\nRecommended budgets:")
for category, amount in budget.items():
    print(f"  {category}: ${amount:.2f}")
```

### Example 3: Savings Trajectory Analysis

```python
from models import SavingsForecaster

# Train model
model = SavingsForecaster()
X, y = model.prepare_data(monthly_df)
model.train(X[:-3], y[:-3])

# Project savings trajectory
trajectory = model.forecast_trajectory(monthly_df, periods=[3, 6, 12])

print(f"Current: ${trajectory['current_savings']:,.2f}")
for period in ['3_months', '6_months', '12_months']:
    info = trajectory[period]
    print(f"\n{period}:")
    print(f"  Projected: ${info['projected_savings']:,.2f}")
    print(f"  Growth: +${info['growth_from_current']:,.2f}")
    print(f"  Monthly Rate: ${info['monthly_savings_rate']:.2f}/month")

# Financial health assessment
assessment = model.assess_financial_health(monthly_df)
print(f"\nFinancial Health: {assessment['status']}")
print(f"Message: {assessment['message']}")
if assessment['recommendations']:
    print("\nRecommendations:")
    for rec in assessment['recommendations']:
        print(f"  - {rec}")
```

### Example 4: Using Saved Models

```python
from models import ExpenseForecaster, CategorySpendingPredictor, SavingsForecaster

# Load pre-trained models
expense_model = ExpenseForecaster()
expense_model.load('models/saved/expense_forecaster.pkl')

category_model = CategorySpendingPredictor()
category_model.load('models/saved/category_predictor.pkl')

savings_model = SavingsForecaster()
savings_model.load('models/saved/savings_forecaster.pkl')

# Make predictions with loaded models
expense_forecast = expense_model.forecast_next_month(monthly_df)
category_forecasts = category_model.forecast_categories(monthly_df)
savings_trajectory = savings_model.forecast_trajectory(monthly_df)
```

### Example 5: Model Evaluation

```python
from models import ExpenseForecaster
from utils.preprocessing import prepare_train_test_split

# Prepare data
model = ExpenseForecaster()
X, y = model.prepare_data(monthly_df)

# Split into train/test
X_train, X_test, y_train, y_test = prepare_train_test_split(
    pd.concat([X, y], axis=1),
    test_size=3,
    feature_columns=list(X.columns),
    target_columns=[y.name]
)

# Train and evaluate
model.train(X_train, y_train)
test_metrics = model.evaluate(X_test, y_test)

print("Test Performance:")
for metric, value in test_metrics.items():
    print(f"  {metric}: {value:.4f}")

# Cross-validation
cv_scores = model.cross_validate(X, y, n_splits=3)
print("\nCross-Validation:")
for metric, scores in cv_scores.items():
    print(f"  {metric}: {np.mean(scores):.4f} ± {np.std(scores):.4f}")

# Feature importance
importance = model.get_feature_importance()
print("\nTop 5 Features:")
print(importance.head(5))
```

### Example 6: Custom Data Integration

```python
import pandas as pd
from datetime import datetime, timedelta

# Create your own monthly data
data = {
    'year_month': pd.period_range('2023-01', periods=12, freq='M'),
    'total_income': [5000] * 12,
    'Food': [400, 420, 380, 450, 430, 410, 440, 420, 400, 450, 460, 470],
    'Transport': [200, 180, 220, 210, 200, 190, 210, 220, 200, 210, 220, 230],
    'Shopping': [300, 280, 350, 320, 300, 290, 330, 310, 300, 350, 340, 360],
    # ... add other categories
}
monthly_df = pd.DataFrame(data)

# Calculate totals
category_cols = ['Food', 'Transport', 'Shopping']  # Add all your categories
monthly_df['total_expense'] = monthly_df[category_cols].sum(axis=1)
monthly_df['savings'] = monthly_df['total_income'] - monthly_df['total_expense']

# Now use with models
from models import ExpenseForecaster
model = ExpenseForecaster()
X, y = model.prepare_data(monthly_df)
model.train(X, y)
```

## Command-Line Options

### Training Script

```bash
# Train specific model
python scripts/train_models.py --model-type expense
python scripts/train_models.py --model-type category
python scripts/train_models.py --model-type savings

# Custom data path
python scripts/train_models.py --data /path/to/data.csv

# Custom model save location
python scripts/train_models.py --models-dir /path/to/models

# Adjust test size
python scripts/train_models.py --test-size 6
```

### Prediction Script

```bash
# Custom data and model paths
python scripts/predict.py --data /path/to/data.csv --models-dir /path/to/models
```

## Expected Output Format

### Monthly Expense Forecast
```
Predicted Total Expense: $1,850.00
95% Confidence Interval: [$1,600.00, $2,100.00]
Historical Average: $1,800.00
Predicted vs Historical: +2.78%
```

### Category Predictions
```
Food: $450.00 (95% CI: [$400.00, $500.00])
Transport: $220.00 (95% CI: [$180.00, $260.00])
Shopping: $350.00 (95% CI: [$300.00, $400.00])
```

### Overspending Risk
```
⚠️  Categories at Risk:
  Shopping: $350.00 (Historical: $280.00, 25% over budget)
```

### Savings Projection
```
Current: $35,000.00
3 months: $38,500.00 (+$3,500.00)
6 months: $42,000.00 (+$7,000.00)
12 months: $49,000.00 (+$14,000.00)
```

## Tips

1. **Minimum Data**: Need at least 6 months of data for reliable predictions
2. **Best Results**: 12+ months of consistent data recommended
3. **Regular Retraining**: Retrain models monthly with new data
4. **Feature Customization**: Modify `utils/preprocessing.py` to add custom features
5. **Model Tuning**: Adjust `n_estimators` and `max_depth` for better performance

## Troubleshooting

### Issue: Poor prediction accuracy
- **Solution**: Ensure you have at least 12 months of data
- **Solution**: Check for data quality issues (missing values, outliers)
- **Solution**: Increase `n_estimators` parameter

### Issue: Import errors
- **Solution**: Run from project root directory
- **Solution**: Ensure all dependencies installed: `pip install -r requirements.txt`

### Issue: Model file not found
- **Solution**: Train models first: `python scripts/train_models.py`
- **Solution**: Check `--models-dir` path is correct
