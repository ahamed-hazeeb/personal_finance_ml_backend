# Deployment Guide

## Personal Finance ML Backend - Production Deployment

This guide covers deployment options for the Personal Finance ML Backend.

## Prerequisites

- Docker & Docker Compose installed
- PostgreSQL 15+ (if not using Docker)
- Redis 7+ (if not using Docker)
- Python 3.12+ (for local development)
- At least 2GB RAM
- 10GB disk space

## Deployment Options

### Option 1: Docker Compose (Recommended)

The easiest way to deploy the entire stack:

```bash
# Clone the repository
git clone https://github.com/ahamed-hazeeb/personal_finance_ml_backend.git
cd personal_finance_ml_backend

# Create environment file
cp .env.example .env

# Edit .env with your configuration
nano .env

# Start all services
docker-compose up -d

# Check service health
docker-compose ps
```

Services will be available at:
- ML Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### Option 2: Manual Deployment

#### Step 1: Setup PostgreSQL

```bash
# Install PostgreSQL
sudo apt-get install postgresql-15

# Create database and user
sudo -u postgres psql
CREATE DATABASE personal_finance;
CREATE USER pfms_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE personal_finance TO pfms_user;
\q
```

#### Step 2: Setup Redis

```bash
# Install Redis
sudo apt-get install redis-server

# Start Redis service
sudo systemctl start redis
sudo systemctl enable redis
```

#### Step 3: Deploy Application

```bash
# Clone repository
git clone https://github.com/ahamed-hazeeb/personal_finance_ml_backend.git
cd personal_finance_ml_backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
nano .env  # Edit configuration

# Run database migrations (if using Alembic)
# alembic upgrade head

# Start the application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Step 4: Setup as System Service

Create `/etc/systemd/system/pfms-backend.service`:

```ini
[Unit]
Description=Personal Finance ML Backend
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/personal_finance_ml_backend
Environment="PATH=/opt/personal_finance_ml_backend/venv/bin"
ExecStart=/opt/personal_finance_ml_backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable pfms-backend
sudo systemctl start pfms-backend
sudo systemctl status pfms-backend
```

### Option 3: Cloud Deployment

#### AWS Elastic Beanstalk

1. Install EB CLI: `pip install awsebcli`
2. Initialize: `eb init`
3. Create environment: `eb create production`
4. Deploy: `eb deploy`

#### Google Cloud Run

```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/pfms-backend

# Deploy
gcloud run deploy pfms-backend \
  --image gcr.io/PROJECT_ID/pfms-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### Azure Container Instances

```bash
# Create resource group
az group create --name pfms-rg --location eastus

# Deploy container
az container create \
  --resource-group pfms-rg \
  --name pfms-backend \
  --image yourregistry.azurecr.io/pfms-backend:latest \
  --cpu 2 --memory 4 \
  --ports 8000
```

## Environment Configuration

### Required Environment Variables

```env
# Database (Required)
DATABASE_URL=postgresql://user:password@host:5432/database

# Redis (Optional but recommended)
REDIS_HOST=localhost
REDIS_PORT=6379
CACHE_ENABLED=true

# Security (Required in production)
SECRET_KEY=your-secure-secret-key-here
ENVIRONMENT=production
DEBUG=false
```

### Optional but Recommended

```env
# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=3600

# Monitoring
ENABLE_METRICS=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/var/log/pfms/backend.log
```

## Database Setup

### Initial Schema

The application automatically creates tables on first run. For manual setup:

```sql
-- See app/db.py for complete schema
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    date DATE NOT NULL,
    amount NUMERIC NOT NULL,
    type VARCHAR NOT NULL,
    category VARCHAR,
    description VARCHAR
);

CREATE INDEX idx_transactions_user ON transactions(user_id);
CREATE INDEX idx_transactions_date ON transactions(date);

-- Additional tables: model_parameters, prediction_cache, etc.
```

### Database Migrations

Using Alembic for schema migrations:

```bash
# Initialize Alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Health Checks

Monitor service health:

```bash
# Application health
curl http://localhost:8000/health

# Metrics (Prometheus format)
curl http://localhost:8000/metrics

# API documentation
open http://localhost:8000/docs
```

## Performance Tuning

### Application

- **Workers**: Use `--workers 4` for uvicorn (1-2x CPU cores)
- **Timeouts**: Set appropriate timeouts for long-running predictions
- **Connection Pooling**: Configure DB pool size based on load

```python
# In .env
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

### Database

```sql
-- Add indexes for frequently queried columns
CREATE INDEX idx_transactions_user_date ON transactions(user_id, date);
CREATE INDEX idx_predictions_expires ON prediction_cache(expires_at);

-- Optimize PostgreSQL settings
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
```

### Redis

```conf
# redis.conf
maxmemory 512mb
maxmemory-policy allkeys-lru
```

## Monitoring

### Prometheus + Grafana

1. Setup Prometheus to scrape `/metrics`
2. Import Grafana dashboard
3. Configure alerts for:
   - High error rate (> 1%)
   - Slow response times (> 500ms p95)
   - Low cache hit rate (< 50%)

### Log Aggregation

Use ELK Stack or cloud logging:

```bash
# Filebeat configuration for logs
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/pfms/*.log
  json.keys_under_root: true
```

## Security Hardening

### SSL/TLS

Use a reverse proxy (Nginx/Caddy) for HTTPS:

```nginx
server {
    listen 443 ssl http2;
    server_name api.yoursite.com;

    ssl_certificate /etc/letsencrypt/live/api.yoursite.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yoursite.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Firewall

```bash
# UFW rules
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### API Key Management

Store API keys securely:

```bash
# Using environment variables
export SECRET_KEY=$(openssl rand -hex 32)

# Using secrets manager (AWS)
aws secretsmanager create-secret \
  --name pfms-backend-secret-key \
  --secret-string $(openssl rand -hex 32)
```

## Backup & Recovery

### Database Backup

```bash
# Automated daily backups
0 2 * * * pg_dump -U pfms_user personal_finance | gzip > /backups/pfms_$(date +\%Y\%m\%d).sql.gz

# Restore
gunzip -c /backups/pfms_20241206.sql.gz | psql -U pfms_user personal_finance
```

### Model Backup

```bash
# Backup trained models
tar -czf models_backup_$(date +%Y%m%d).tar.gz models/saved/

# Upload to S3
aws s3 cp models_backup_20241206.tar.gz s3://your-bucket/backups/
```

## Scaling

### Horizontal Scaling

- Use load balancer (AWS ALB, Nginx)
- Deploy multiple backend instances
- Use shared Redis for caching
- Use shared PostgreSQL (RDS, Cloud SQL)

### Vertical Scaling

- Increase worker processes
- Allocate more RAM
- Use faster storage (SSD)

## Troubleshooting

### Application won't start

```bash
# Check logs
docker-compose logs ml_backend

# Verify database connection
psql -h localhost -U pfms_user -d personal_finance

# Verify Redis connection
redis-cli ping
```

### High memory usage

- Check cache size: `redis-cli INFO memory`
- Reduce cache TTL
- Limit worker processes

### Slow predictions

- Enable caching
- Add database indexes
- Optimize model complexity
- Use connection pooling

## Support

For issues or questions:
- GitHub Issues: https://github.com/ahamed-hazeeb/personal_finance_ml_backend/issues
- Documentation: See README.md
- API Docs: http://localhost:8000/docs
