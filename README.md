# Personal Finance ML Backend v2.0

🚀 **Production-Ready AI-Powered Personal Finance Management System**

A comprehensive machine learning backend for personal finance management with advanced predictive analytics, goal planning intelligence, and real-time financial insights.

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.68+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 🌟 Key Features

### 🎯 Phase 2-4: Advanced AI Features (NEW!)

#### 💡 Advanced Expense Forecasting
- **Holt-Winters Model**: Seasonal pattern detection for 12+ months of data
- **ARIMA Model**: Trend-based forecasting for 6-11 months of data  
- **Auto Model Selection**: Automatically chooses the best model based on data availability
- **Confidence Intervals**: 95% prediction intervals for uncertainty quantification

#### 🏥 Financial Health Scoring (0-100)
- **Comprehensive Scoring**: 5-component algorithm with weighted scores
  - Savings Rate (30%): Track your savings habits
  - Expense Consistency (25%): Measure spending predictability
  - Emergency Fund (20%): Assess financial safety net
  - Debt-to-Income Ratio (15%): Monitor debt burden
  - Goal Progress (10%): Track financial goal achievement
- **Historical Tracking**: Month-over-month and quarter-over-quarter trends
- **Peer Benchmarking**: Anonymous comparison with similar age/income groups
- **Actionable Recommendations**: Personalized advice for improvement

#### 💰 Smart Budget Optimizer
- **50/30/20 Rule**: Automated budget allocation (Needs/Wants/Savings)
- **Goal-Adjusted Budgets**: Personalized based on active financial goals
- **Real-time Alerts**: Predictive overspending warnings
- **Category Recommendations**: Specific suggestions for each spending category
- **Leakage Detection**: Identify high-variance spending categories
- **Optimization Suggestions**: Reach target savings rates with actionable steps

#### 🤖 Personalized Recommendation Engine
- **Spending Habits Analysis**: Frequency analysis and pattern detection
- **Subscription Detection**: Automatically identify recurring charges (monthly, weekly, quarterly)
- **Savings Opportunities**: Find hidden fees, impulse purchases, and spending patterns
- **Behavior Nudges**: Positive reinforcement, warnings, and milestone celebrations
- **Smart Insights**: Weekend vs weekday spending, no-spend days, and more

### 💰 Goal Planning Intelligence
- **Timeline Calculator**: Calculate how long it takes to reach financial goals
- **Reverse Planning**: Determine required monthly savings for target dates
- **Milestone Tracking**: Automatic milestone generation (25%, 50%, 75%, 100%)
- **Feasibility Analysis**: AI-powered assessment of goal achievability
- **Alternative Scenarios**: Multiple saving strategy recommendations

### 📊 ML-Powered Predictions
- **Savings Forecasting**: Linear regression models with confidence intervals
- **Monthly Expense Prediction**: Time-series forecasting with 3-24 month history
- **Category-wise Analysis**: Multi-output prediction for spending categories
- **Trend Detection**: Identify spending patterns and anomalies

### 🏗️ Production-Ready Infrastructure
- **Structured Logging**: JSON-formatted logs with contextual information
- **Prometheus Metrics**: Built-in monitoring and performance tracking
- **Redis Caching**: High-performance caching layer for predictions
- **Rate Limiting**: Configurable API rate limiting per user/IP
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Authentication**: API key-based authentication middleware

### 🐳 Deployment Ready
- **Docker Support**: Multi-stage Dockerfile for optimized builds
- **Docker Compose**: Complete stack with PostgreSQL, Redis, and ML service
- **Health Checks**: Automated health monitoring for all services
- **Horizontal Scaling**: Load balancer ready architecture
- **Environment Configs**: Separate configs for dev/staging/production

---

## 📦 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/ahamed-hazeeb/personal_finance_ml_backend.git
cd personal_finance_ml_backend

# Create environment configuration
cp .env.example .env

# Start all services (PostgreSQL, Redis, ML Backend)
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f ml_backend
```

**Services Available:**
- 🌐 API: http://localhost:8000
- 📚 Interactive Docs: http://localhost:8000/docs
- 🏥 Health Check: http://localhost:8000/health
- 📊 Metrics: http://localhost:8000/metrics
- 🗄️ PostgreSQL: localhost:5432
- 💾 Redis: localhost:6379

### Option 2: Local Development

```bash
# Clone repository
git clone https://github.com/ahamed-hazeeb/personal_finance_ml_backend.git
cd personal_finance_ml_backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your database and Redis URLs

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🚀 API Endpoints

### Goal Planning

#### Calculate Goal Timeline
Calculate how long it will take to reach a financial goal.

```bash
curl -X POST "http://localhost:8000/api/v1/goals/calculate-timeline" \
  -H "Content-Type: application/json" \
  -d '{
    "target_amount": 50000,
    "current_savings": 10000,
    "monthly_savings": 2000
  }'
```

**Response:**
```json
{
  "feasible": true,
  "months_needed": 20,
  "target_date": "2027-08-06",
  "feasibility_rating": "Good",
  "milestones": [
    {"percentage": 25, "amount": 20000, "expected_date": "2025-05-06"},
    {"percentage": 50, "amount": 30000, "expected_date": "2025-10-06"},
    {"percentage": 75, "amount": 40000, "expected_date": "2026-03-06"},
    {"percentage": 100, "amount": 50000, "expected_date": "2026-08-06"}
  ]
}
```

#### Reverse Goal Planning
Calculate required monthly savings to reach a goal by a specific date.

```bash
curl -X POST "http://localhost:8000/api/v1/goals/reverse-plan" \
  -H "Content-Type: application/json" \
  -d '{
    "target_amount": 50000,
    "current_savings": 10000,
    "target_date": "2026-12-31"
  }'
```

**Response:**
```json
{
  "feasible": true,
  "required_monthly_savings": 1666.67,
  "feasibility_score": 70,
  "alternatives": [
    {
      "scenario": "Aggressive",
      "monthly_savings": 2500,
      "months_needed": 16,
      "description": "Reach your goal faster with increased savings"
    },
    {
      "scenario": "Conservative",
      "monthly_savings": 1250,
      "months_needed": 32,
      "description": "More flexible timeline with lower monthly commitment"
    }
  ]
}
```

### ML Training & Prediction

#### Train Savings Model
```bash
curl -X POST "http://localhost:8000/ml/train" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "start_date": "2023-01-01",
    "end_date": "2024-12-01"
  }'
```

#### Predict Monthly Savings
```bash
curl -X POST "http://localhost:8000/ml/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "months_ahead": 6
  }'
```

### Phase 2 Features: Advanced AI & Analytics

#### Advanced Expense Forecasting
```bash
POST /api/v1/predictions/expense/advanced
```
Time-series forecasting using Holt-Winters (12+ months) or ARIMA (6-11 months).

#### Financial Health Score
```bash
POST /api/v1/insights/health-score
GET  /api/v1/insights/trends/{user_id}
GET  /api/v1/insights/benchmark/{user_id}
```
Comprehensive health scoring (0-100) with trends and peer benchmarking.

#### Smart Budget Management
```bash
POST /api/v1/budget/recommend
POST /api/v1/budget/alerts
POST /api/v1/budget/optimize
```
Personalized budgets using 50/30/20 rule with real-time alerts and optimization.

#### Personalized Recommendations
```bash
POST /api/v1/recommendations/habits
POST /api/v1/recommendations/subscriptions
POST /api/v1/recommendations/opportunities
POST /api/v1/recommendations/nudges
```
Habit analysis, subscription detection, savings opportunities, and behavior nudges.

### System Endpoints

- **Health Check**: `GET /health`
- **Prometheus Metrics**: `GET /metrics`
- **API Info**: `GET /`
- **Interactive Docs**: `GET /docs`
- **OpenAPI Schema**: `GET /openapi.json`

📖 **Full API Documentation**: See [API_EXAMPLES.md](API_EXAMPLES.md)

---

## 🏗️ Architecture

```
┌─────────────────┐
│  Load Balancer  │
└────────┬────────┘
         │
    ┌────┴─────┐
    │ FastAPI  │◄──────┐
    │  ML API  │       │
    └────┬─────┘       │
         │             │
    ┌────┴──────┐  ┌───┴────┐
    │PostgreSQL │  │ Redis  │
    │  Database │  │ Cache  │
    └───────────┘  └────────┘
```

### Tech Stack

- **Framework**: FastAPI (async Python web framework)
- **Database**: PostgreSQL (with SQLAlchemy ORM)
- **Cache**: Redis (for prediction caching)
- **ML Libraries**: scikit-learn, statsmodels, numpy, pandas
- **Monitoring**: Prometheus metrics
- **Logging**: Structured JSON logs
- **Authentication**: API key middleware
- **Rate Limiting**: slowapi with Redis backend
- **Deployment**: Docker & Docker Compose

### Project Structure

```
personal_finance_ml_backend/
├── app/
│   ├── api/                    # API versioning
│   ├── core/                   # Core configuration
│   │   ├── config.py          # Settings & environment
│   │   ├── logging.py         # Structured logging
│   │   └── monitoring.py      # Prometheus metrics
│   ├── middleware/            # Custom middleware
│   │   ├── auth.py           # Authentication
│   │   ├── error_handler.py  # Error handling
│   │   └── rate_limiter.py   # Rate limiting
│   ├── models/                # ML models
│   │   └── goal_planner.py   # Goal planning engine
│   ├── routers/               # API routes
│   │   ├── goals.py          # Goal endpoints
│   │   └── ml.py             # ML endpoints
│   ├── schemas/               # Pydantic schemas
│   ├── services/              # Business logic
│   │   └── cache_service.py  # Caching service
│   ├── utils/                 # Utilities
│   │   └── validators.py     # Input validation
│   ├── db.py                  # Database models
│   └── main.py                # FastAPI application
├── models/                    # Standalone ML models
├── scripts/                   # Utility scripts
├── .env.example              # Environment template
├── docker-compose.yml        # Docker Compose config
├── Dockerfile                # Docker build config
├── requirements.txt          # Python dependencies
├── API_EXAMPLES.md          # API usage examples
├── DEPLOYMENT.md            # Deployment guide
└── README.md                # This file
```

---

## 🔧 Configuration

All configuration is managed through environment variables. See [.env.example](.env.example) for all options.

### Key Configuration Options

```env
# Database
DATABASE_URL=postgresql://user:password@localhost/personal_finance

# Redis Cache
REDIS_HOST=localhost
CACHE_ENABLED=true

# Security
SECRET_KEY=your-secret-key-here
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100

# Features
ENABLE_GOAL_PLANNING=true
ENABLE_METRICS=true

# Environment
ENVIRONMENT=production  # development, staging, production
DEBUG=false
```

---

## 📊 Monitoring & Observability

### Health Check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "environment": "production",
  "cache": {
    "enabled": true,
    "hit_rate": 65.5
  }
}
```

### Prometheus Metrics

Access metrics at `http://localhost:8000/metrics`

**Available Metrics:**
- API request counts and latencies
- Model training/prediction metrics
- Cache hit/miss rates
- Database query performance
- Error rates by endpoint

### Structured Logging

All logs are emitted in JSON format for easy parsing:

```json
{
  "timestamp": "2024-12-06T18:19:22.744822Z",
  "level": "INFO",
  "logger": "app.main",
  "message": "Starting Personal Finance ML Backend v2.0.0",
  "module": "main",
  "function": "<module>",
  "line": 50
}
```

---

## 🧪 Testing

### Manual API Testing

```bash
# Test goal timeline
python -c "
import requests
response = requests.post(
    'http://localhost:8000/api/v1/goals/calculate-timeline',
    json={'target_amount': 50000, 'current_savings': 10000, 'monthly_savings': 2000}
)
print(response.json())
"
```

### Integration Testing

```bash
# Run with pytest (when tests are implemented)
pytest tests/ -v
```

---

## 🚢 Deployment

### Docker Deployment

```bash
# Build image
docker build -t pfms-backend:latest .

# Run container
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host/db \
  -e REDIS_HOST=redis \
  pfms-backend:latest
```

### Production Deployment

For production deployment with load balancing, SSL, and monitoring:

📖 **Complete Guide**: See [DEPLOYMENT.md](DEPLOYMENT.md)

Key topics covered:
- AWS/GCP/Azure deployment
- Nginx reverse proxy setup
- SSL/TLS configuration
- Database migrations
- Backup strategies
- Performance tuning
- Security hardening

---

## 🔐 Security

### Features

- **API Key Authentication**: Protect endpoints with API keys
- **Rate Limiting**: Prevent abuse with configurable rate limits
- **Input Validation**: Comprehensive validation using Pydantic
- **SQL Injection Protection**: SQLAlchemy ORM with parameterized queries
- **CORS Configuration**: Configurable CORS policies
- **Error Sanitization**: Hide sensitive info in production errors

### Best Practices

```python
# Always use environment variables for secrets
SECRET_KEY=your-secret-key-here  # Never commit this!

# Enable rate limiting in production
RATE_LIMIT_ENABLED=true

# Use HTTPS in production
# Configure via reverse proxy (Nginx/Caddy)

# Restrict CORS origins
CORS_ORIGINS=["https://yourapp.com"]
```

---

## 🔄 Integration Examples

### JavaScript/Node.js

```javascript
const axios = require('axios');

const API_URL = 'http://localhost:8000';

async function calculateGoal() {
  const response = await axios.post(
    `${API_URL}/api/v1/goals/calculate-timeline`,
    {
      target_amount: 50000,
      current_savings: 10000,
      monthly_savings: 2000
    }
  );
  return response.data;
}
```

### Python

```python
import requests

response = requests.post(
    'http://localhost:8000/api/v1/goals/calculate-timeline',
    json={
        'target_amount': 50000,
        'current_savings': 10000,
        'monthly_savings': 2000
    }
)
result = response.json()
```

📖 **More Examples**: See [API_EXAMPLES.md](API_EXAMPLES.md)

---

## 🛠️ Development

### Setup Development Environment

```bash
# Clone and setup
git clone https://github.com/ahamed-hazeeb/personal_finance_ml_backend.git
cd personal_finance_ml_backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set environment to development
export ENVIRONMENT=development
export DEBUG=true

# Run with auto-reload
uvicorn app.main:app --reload
```

### Code Style

- **PEP 8**: Follow Python style guidelines
- **Type Hints**: Use type hints for all functions
- **Docstrings**: Document all public methods
- **Validation**: Validate all inputs using Pydantic

---

## 📈 Roadmap

### ✅ Completed (v2.0)
- Core infrastructure (logging, monitoring, caching)
- Goal planning intelligence
- Enhanced database schema
- Docker deployment
- Comprehensive documentation

### 🚧 In Progress
- Advanced expense forecasting (Holt-Winters, ARIMA)
- Budget optimizer with 50/30/20 rule
- Financial health score calculator
- Recommendations engine

### 🔮 Planned (v2.1+)
- Cash flow predictor
- Debt management optimizer
- Investment readiness analyzer
- Mobile app integration
- Real-time notifications
- Multi-currency support

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📧 Support

- **Documentation**: [API Examples](API_EXAMPLES.md) | [Deployment Guide](DEPLOYMENT.md)
- **Issues**: [GitHub Issues](https://github.com/ahamed-hazeeb/personal_finance_ml_backend/issues)
- **Interactive API Docs**: http://localhost:8000/docs

---

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- scikit-learn for ML capabilities
- The open-source community

---

**Built with ❤️ by Ahamed Hazeeb**

**Version**: 2.0.0  
**Last Updated**: December 2024
