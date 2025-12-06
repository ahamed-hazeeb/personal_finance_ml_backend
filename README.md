# Personal Finance ML Backend

AI-powered predictive analytics backend for personal finance management. This system provides modular, extensible machine learning models for expense forecasting, category-wise spending prediction, and savings trajectory analysis.

## Features

### 🎯 Core Predictive Analytics

1. **Monthly Expense Forecasting**
   - Predicts next month's total expense based on 3-12 months of historical data
   - Provides 95% confidence intervals for predictions
   - Uses time-series features and rolling statistics

2. **Category-wise Spending Prediction**
   - Forecasts upcoming expenses for each spending category (Food, Transport, Shopping, etc.)
   - Detects categories at risk of overspending (>20% above historical average)
   - Generates optimal budget recommendations based on income and spending patterns
   - Uses MultiOutputRegressor for cross-category pattern learning

3. **Savings Trajectory Forecasting**
   - Projects user's cumulative savings over 3, 6, and 12 months
   - Provides confidence intervals on growth trends
   - Calculates financial health metrics and savings rate
   - Offers personalized recommendations for improving savings

### 🔧 Technical Features

- **Modular Architecture**: Extensible design for future AI features (investment readiness, debt management, etc.)
- **Robust Feature Engineering**: Time-series features, lag features, rolling statistics, and growth indicators
- **Model Persistence**: Save and load trained models for production use
- **Time-Series Cross-Validation**: Proper evaluation respecting temporal ordering
- **Sample Data Generation**: Realistic dummy data for rapid development and testing
- **Comprehensive Evaluation**: MAE, RMSE, MAPE, R² metrics with cross-validation

## Installation

### Prerequisites
- Python 3.7+
- pip

### Setup

```bash
# Clone the repository
git clone https://github.com/ahamed-hazeeb/personal_finance_ml_backend.git
cd personal_finance_ml_backend

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### 1. Generate Sample Data

```bash
cd data
python sample_data_generator.py
```

This creates:
- `sample_transactions.csv`: Individual transaction records
- `sample_monthly_data.csv`: Aggregated monthly financial data

### 2. Train Models

Train all models (expense, category, savings):

```bash
python scripts/train_models.py --data ./data/sample_monthly_data.csv --models-dir ./models/saved
```

Train specific model:

```bash
# Train only expense forecaster
python scripts/train_models.py --model-type expense

# Train only category predictor
python scripts/train_models.py --model-type category

# Train only savings forecaster
python scripts/train_models.py --model-type savings
```

### 3. Make Predictions

```bash
python scripts/predict.py --data ./data/sample_monthly_data.csv --models-dir ./models/saved
```

## Project Structure

```
personal_finance_ml_backend/
├── data/
│   ├── sample_data_generator.py    # Generate dummy transaction data
│   ├── sample_transactions.csv     # Sample transaction records
│   └── sample_monthly_data.csv     # Sample monthly aggregated data
├── models/
│   ├── __init__.py
│   ├── base_predictor.py           # Base class for all predictors
│   ├── expense_forecaster.py       # Monthly expense forecasting
│   ├── category_predictor.py       # Category-wise spending prediction
│   ├── savings_forecaster.py       # Savings trajectory forecasting
│   └── saved/                      # Trained model files (.pkl)
├── utils/
│   ├── __init__.py
│   ├── preprocessing.py            # Feature engineering and data prep
│   └── metrics.py                  # Evaluation metrics and reporting
├── scripts/
│   ├── train_models.py             # Training pipeline
│   └── predict.py                  # Prediction/inference script
├── requirements.txt                # Python dependencies
├── .gitignore
└── README.md
```

## Usage Examples

### Python API

#### Expense Forecasting

```python
from models import ExpenseForecaster
import pandas as pd

# Load data
monthly_df = pd.read_csv('data/sample_monthly_data.csv')

# Initialize and train model
model = ExpenseForecaster(n_estimators=100, max_depth=10)
X, y = model.prepare_data(monthly_df, target_column='total_expense')
model.train(X[:-3], y[:-3])  # Train on all but last 3 months

# Make prediction for next month
forecast = model.forecast_next_month(monthly_df, confidence_level=0.95)
print(f"Predicted Expense: ${forecast['predicted_expense']:.2f}")
print(f"95% CI: {forecast['confidence_interval']}")

# Save model
model.save('models/saved/expense_model.pkl')
```

#### Category-wise Prediction

```python
from models import CategorySpendingPredictor

# Initialize and train
model = CategorySpendingPredictor(n_estimators=100)
X, y = model.prepare_data(monthly_df)
model.train(X[:-3], y[:-3])

# Predict next month's category expenses
forecasts = model.forecast_categories(monthly_df)
for category, info in forecasts.items():
    print(f"{category}: ${info['predicted']:.2f}")

# Detect overspending risks
risks = model.detect_overspending_risks(monthly_df, threshold=1.2)
at_risk = [cat for cat, info in risks.items() if info['at_risk']]
print(f"At risk categories: {at_risk}")

# Generate budget recommendations
total_income = monthly_df['total_income'].iloc[-1]
recommendations = model.generate_budget_recommendations(
    monthly_df, 
    total_budget=total_income,
    safety_margin=0.1
)
print(recommendations)
```

#### Savings Forecasting

```python
from models import SavingsForecaster

# Initialize and train
model = SavingsForecaster(n_estimators=100)
X, y = model.prepare_data(monthly_df, target_column='savings')
model.train(X[:-3], y[:-3])

# Forecast savings trajectory
trajectory = model.forecast_trajectory(monthly_df, periods=[3, 6, 12])
print(f"Current Savings: ${trajectory['current_savings']:.2f}")
print(f"Projected (3 months): ${trajectory['3_months']['projected_savings']:.2f}")

# Assess financial health
assessment = model.assess_financial_health(monthly_df)
print(f"Status: {assessment['status']}")
print(f"Message: {assessment['message']}")
print(f"Recommendations: {assessment['recommendations']}")
```

## Model Architecture

### Base Predictor
All models inherit from `BaseFinancePredictor`, which provides:
- RandomForestRegressor with configurable parameters
- Train/predict/evaluate methods
- Confidence interval calculation
- Model persistence (save/load)
- Feature importance analysis
- Time-series cross-validation

### Feature Engineering
The preprocessing pipeline creates:
- **Time features**: Month, quarter, year, cyclical encoding (sin/cos)
- **Lag features**: Previous 1, 2, 3 months' values
- **Rolling features**: 3-month and 6-month rolling mean, std, trend
- **Growth features**: Month-over-month and year-over-year growth rates

### Model Types

1. **ExpenseForecaster**: Single-output RandomForestRegressor
   - Target: Total monthly expense
   - Features: Time features, expense lags, income lags, rolling statistics

2. **CategorySpendingPredictor**: MultiOutputRegressor
   - Targets: Multiple category expenses simultaneously
   - Features: Category-specific lags, rolling stats, time features
   - Enables cross-category pattern learning

3. **SavingsForecaster**: Single-output RandomForestRegressor
   - Target: Monthly savings (income - expenses)
   - Features: Savings lags, income/expense patterns, time features

## API Integration Notes

### RESTful API Structure (Future Implementation)

```python
# Suggested API endpoints for integration:

POST /api/train
- Train models with user's historical data
- Input: Historical transaction data
- Output: Model IDs, training metrics

POST /api/predict/expense
- Get monthly expense forecast
- Input: User ID or historical data
- Output: Prediction with confidence interval

POST /api/predict/categories
- Get category-wise predictions
- Input: User ID or historical data
- Output: Category forecasts, risk analysis, budget recommendations

POST /api/predict/savings
- Get savings trajectory
- Input: User ID or historical data
- Output: 3/6/12-month projections, financial health assessment

GET /api/models/{model_id}
- Get model information and performance metrics
```

### Integration with FastAPI (Example)

```python
from fastapi import FastAPI
from models import ExpenseForecaster, CategorySpendingPredictor, SavingsForecaster

app = FastAPI()

@app.post("/api/predict/expense")
async def predict_expense(user_data: dict):
    model = ExpenseForecaster()
    model.load('models/saved/expense_forecaster.pkl')
    
    monthly_df = pd.DataFrame(user_data['monthly_data'])
    forecast = model.forecast_next_month(monthly_df)
    
    return {
        "predicted_expense": forecast['predicted_expense'],
        "confidence_interval": forecast['confidence_interval'],
        "confidence_level": forecast['confidence_level']
    }
```

## Extensibility

The codebase is designed for easy extension to additional AI features:

### Adding New Features

1. **Investment Readiness Score**
   - Create `InvestmentReadinessPredictor` inheriting from `BaseFinancePredictor`
   - Use savings rate, income stability, and expense patterns as features
   - Classify users into investment readiness categories

2. **Debt Management Advisor**
   - Create `DebtManagementAdvisor` model
   - Predict optimal debt payoff strategies
   - Recommend allocation between debt payment and savings

3. **Anomaly Detection**
   - Add `AnomalyDetector` for unusual spending patterns
   - Use Isolation Forest or One-Class SVM
   - Alert users to suspicious transactions

### Custom Data Sources

```python
# Extend sample_data_generator.py for custom data
def generate_custom_categories(categories: dict):
    """Add custom spending categories"""
    pass

def load_from_bank_api(api_credentials: dict):
    """Load real transaction data from bank API"""
    pass
```

## Performance Metrics

Models are evaluated using:
- **MAE** (Mean Absolute Error): Average prediction error in dollars
- **RMSE** (Root Mean Squared Error): Penalizes larger errors more
- **MAPE** (Mean Absolute Percentage Error): Error as percentage
- **R²** (R-squared): Proportion of variance explained (0-1, higher is better)

Typical performance on sample data:
- Expense Forecaster: MAPE ~5-10%
- Category Predictor: MAPE ~10-15% (varies by category)
- Savings Forecaster: MAPE ~8-12%

## Contributing

Contributions are welcome! Areas for improvement:
- Deep learning models (LSTM, Transformer) for time-series
- More sophisticated feature engineering
- Hyperparameter optimization
- Real-time model updates
- Multi-user support and personalization
- Integration with financial APIs (Plaid, Yodlee)

## License

MIT License - feel free to use in your projects

## Support

For questions or issues, please open an issue on GitHub.

---

**Built with**: Python, scikit-learn, pandas, numpy

**Author**: Ahamed Hazeeb

**Version**: 1.0.0