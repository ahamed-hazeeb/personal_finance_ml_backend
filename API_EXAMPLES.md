# API Examples

Comprehensive examples for using the Personal Finance ML Backend API.

## Base URL

```
Development: http://localhost:8000
Production: https://api.yoursite.com
```

## Authentication

Include API key in headers (when authentication is enabled):

```bash
X-API-Key: your-api-key-here
```

---

## Goal Planning Endpoints

### 1. Calculate Goal Timeline

Calculate how long it will take to reach a financial goal.

**Endpoint:** `POST /api/v1/goals/calculate-timeline`

**Request:**
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
  "target_amount": 50000.0,
  "current_savings": 10000.0,
  "amount_needed": 40000.0,
  "monthly_savings": 2000.0,
  "months_needed": 20,
  "target_date": "2026-08-06",
  "progress_percentage": 20.0,
  "feasibility_rating": "Good",
  "feasibility_message": "This goal is achievable with consistent savings",
  "milestones": [
    {
      "percentage": 25,
      "amount": 20000.0,
      "months_from_start": 5,
      "expected_date": "2025-05-06"
    },
    {
      "percentage": 50,
      "amount": 30000.0,
      "months_from_start": 10,
      "expected_date": "2025-10-06"
    },
    {
      "percentage": 75,
      "amount": 40000.0,
      "months_from_start": 15,
      "expected_date": "2026-03-06"
    },
    {
      "percentage": 100,
      "amount": 50000.0,
      "months_from_start": 20,
      "expected_date": "2026-08-06"
    }
  ]
}
```

### 2. Reverse Goal Planning

Calculate required monthly savings to reach a goal by a specific date.

**Endpoint:** `POST /api/v1/goals/reverse-plan`

**Request:**
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
  "target_amount": 50000.0,
  "current_savings": 10000.0,
  "amount_needed": 40000.0,
  "target_date": "2026-12-31",
  "months_available": 24,
  "required_monthly_savings": 1666.67,
  "feasibility_score": 70,
  "feasibility_rating": "Good",
  "feasibility_message": "This goal is achievable with consistent savings",
  "alternatives": [
    {
      "scenario": "Aggressive",
      "monthly_savings": 2500.0,
      "months_needed": 16,
      "target_date": "2026-04-06",
      "description": "Reach your goal faster with increased savings"
    },
    {
      "scenario": "Conservative",
      "monthly_savings": 1250.0,
      "months_needed": 32,
      "target_date": "2027-08-06",
      "description": "More flexible timeline with lower monthly commitment"
    }
  ],
  "milestones": [...]
}
```

---

## ML Training & Prediction Endpoints

### 3. Train Savings Model

Train a linear regression model for monthly savings prediction.

**Endpoint:** `POST /ml/train`

**Request:**
```bash
curl -X POST "http://localhost:8000/ml/train" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "start_date": "2023-01-01",
    "end_date": "2024-12-01"
  }'
```

**Response:**
```json
{
  "message": "Model trained successfully with 12 months of data",
  "model": {
    "id": 1,
    "user_id": 123,
    "model_type": "linear_regression",
    "target_table": "transactions_savings",
    "slope": 150.25,
    "intercept": 1000.0,
    "parameters": {
      "r2_score": 0.85,
      "trained_months": 12,
      "start_month": "2023-01"
    },
    "last_trained_date": "2024-12-06"
  }
}
```

### 4. Predict Monthly Savings

Generate savings predictions for future months.

**Endpoint:** `POST /ml/predict`

**Request:**
```bash
curl -X POST "http://localhost:8000/ml/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123,
    "months_ahead": 6
  }'
```

**Response:**
```json
{
  "user_id": 123,
  "model_type": "linear_regression",
  "predictions": [
    1801.0,
    1951.25,
    2101.5,
    2251.75,
    2402.0,
    2552.25
  ],
  "model_parameters": {
    "id": 1,
    "user_id": 123,
    "model_type": "linear_regression",
    "target_table": "transactions_savings",
    "slope": 150.25,
    "intercept": 1000.0,
    "parameters": {
      "r2_score": 0.85,
      "trained_months": 12,
      "start_month": "2023-01"
    },
    "last_trained_date": "2024-12-06"
  }
}
```

---

## System Endpoints

### 5. Health Check

Check system health and status.

**Endpoint:** `GET /health`

**Request:**
```bash
curl "http://localhost:8000/health"
```

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "environment": "development",
  "cache": {
    "enabled": true,
    "hit_rate": 65.5
  }
}
```

### 6. Metrics (Prometheus)

Get Prometheus metrics for monitoring.

**Endpoint:** `GET /metrics`

**Request:**
```bash
curl "http://localhost:8000/metrics"
```

**Response:**
```
# HELP api_requests_total Total number of API requests
# TYPE api_requests_total counter
api_requests_total{method="POST",endpoint="/api/v1/goals/calculate-timeline",status_code="200"} 42.0
...
```

### 7. API Information

Get API information and available endpoints.

**Endpoint:** `GET /`

**Request:**
```bash
curl "http://localhost:8000/"
```

**Response:**
```json
{
  "name": "Personal Finance ML Backend",
  "version": "2.0.0",
  "environment": "development",
  "endpoints": {
    "ml_train": "POST /ml/train - Train a linear regression model for monthly savings",
    "ml_predict": "POST /ml/predict - Predict monthly savings for future months",
    "goals_calculate_timeline": "POST /api/v1/goals/calculate-timeline - Calculate goal timeline",
    "goals_reverse_plan": "POST /api/v1/goals/reverse-plan - Calculate required savings for goal",
    "health": "GET /health - Health check endpoint",
    "metrics": "GET /metrics - Prometheus metrics (if enabled)",
    "docs": "GET /docs - Interactive API documentation"
  }
}
```

---

## Integration Examples

### JavaScript/Node.js

```javascript
const axios = require('axios');

const API_URL = 'http://localhost:8000';

// Calculate goal timeline
async function calculateGoalTimeline() {
  try {
    const response = await axios.post(
      `${API_URL}/api/v1/goals/calculate-timeline`,
      {
        target_amount: 50000,
        current_savings: 10000,
        monthly_savings: 2000
      }
    );
    console.log('Goal Timeline:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error:', error.response.data);
  }
}

// Train model
async function trainModel(userId) {
  try {
    const response = await axios.post(
      `${API_URL}/ml/train`,
      {
        user_id: userId,
        start_date: '2023-01-01',
        end_date: '2024-12-01'
      }
    );
    console.log('Model trained:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error:', error.response.data);
  }
}

// Predict savings
async function predictSavings(userId, monthsAhead) {
  try {
    const response = await axios.post(
      `${API_URL}/ml/predict`,
      {
        user_id: userId,
        months_ahead: monthsAhead
      }
    );
    console.log('Predictions:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error:', error.response.data);
  }
}

// Usage
(async () => {
  await calculateGoalTimeline();
  await trainModel(123);
  await predictSavings(123, 6);
})();
```

### Python

```python
import requests

API_URL = "http://localhost:8000"

# Calculate goal timeline
def calculate_goal_timeline():
    response = requests.post(
        f"{API_URL}/api/v1/goals/calculate-timeline",
        json={
            "target_amount": 50000,
            "current_savings": 10000,
            "monthly_savings": 2000
        }
    )
    return response.json()

# Train model
def train_model(user_id):
    response = requests.post(
        f"{API_URL}/ml/train",
        json={
            "user_id": user_id,
            "start_date": "2023-01-01",
            "end_date": "2024-12-01"
        }
    )
    return response.json()

# Predict savings
def predict_savings(user_id, months_ahead):
    response = requests.post(
        f"{API_URL}/ml/predict",
        json={
            "user_id": user_id,
            "months_ahead": months_ahead
        }
    )
    return response.json()

# Usage
if __name__ == "__main__":
    timeline = calculate_goal_timeline()
    print("Goal Timeline:", timeline)
    
    model = train_model(123)
    print("Model trained:", model)
    
    predictions = predict_savings(123, 6)
    print("Predictions:", predictions)
```

---

## Error Handling

### Common Error Responses

**400 Bad Request:**
```json
{
  "error": {
    "type": "ValidationError",
    "message": "Invalid input data",
    "status_code": 400,
    "details": [
      {
        "field": "target_amount",
        "message": "field required",
        "type": "value_error.missing"
      }
    ]
  }
}
```

**404 Not Found:**
```json
{
  "error": {
    "type": "NotFoundError",
    "message": "No trained model found for user 123",
    "status_code": 404
  }
}
```

**500 Internal Server Error:**
```json
{
  "error": {
    "type": "InternalServerError",
    "message": "An unexpected error occurred",
    "status_code": 500
  }
}
```

**429 Too Many Requests:**
```json
{
  "error": "Too many requests. Please try again later."
}
```

---

## Best Practices

1. **Always handle errors**: Check response status codes and handle errors gracefully
2. **Use appropriate timeouts**: Set reasonable timeouts for API requests (e.g., 30 seconds)
3. **Implement retry logic**: Use exponential backoff for failed requests
4. **Cache responses**: Cache frequently accessed data on the client side
5. **Validate inputs**: Validate data before sending to the API
6. **Monitor usage**: Track API usage and monitor for errors
7. **Keep API key secure**: Never expose API keys in client-side code

---

## Rate Limiting

Default limits (configurable):
- **100 requests per hour** per IP address
- Rate limit info in response headers:
  ```
  X-RateLimit-Limit: 100
  X-RateLimit-Remaining: 95
  X-RateLimit-Reset: 1638360000
  ```

---

## Support

- **Interactive Documentation**: http://localhost:8000/docs
- **GitHub Issues**: https://github.com/ahamed-hazeeb/personal_finance_ml_backend/issues
- **README**: See README.md for more information
