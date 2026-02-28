"""
DEPLOYMENT GUIDE - AI Pocket CFO Transaction Management Module

Complete guide for deploying the application to production.
"""

# ============================================================

# 1. PRE-DEPLOYMENT CHECKLIST

# ============================================================

## Security

- [ ] Change DEBUG=False in .env
- [ ] Set strong SECRET_KEY in .env
- [ ] Restrict ALLOWED_ORIGINS to specific domains
- [ ] Implement actual JWT authentication (replace placeholder get_user_id)
- [ ] Use HTTPS only in production
- [ ] Validate and sanitize all user inputs
- [ ] Add rate limiting to prevent abuse
- [ ] Enable Row Level Security (RLS) in Supabase

## Database

- [ ] Run schema.sql in Supabase SQL Editor
- [ ] Verify all indexes are created
- [ ] Test Row Level Security policies
- [ ] Backup production database regularly
- [ ] Monitor database performance

## API

- [ ] Implement proper error logging
- [ ] Add request/response logging
- [ ] Set up monitoring and alerts
- [ ] Test all endpoints thoroughly
- [ ] Load test the API
- [ ] Verify pagination works correctly

## Testing

- [ ] Run unit tests: pytest test_transactions.py
- [ ] Test export functionality manually
- [ ] Test with various data volumes
- [ ] Verify CSV/PDF exports work
- [ ] Test with edge cases

# ============================================================

# 2. LOCAL DEVELOPMENT SETUP

# ============================================================

## Installation

1. Create virtual environment:
   python -m venv venv
   source venv/Scripts/activate # Windows

   # or

   source venv/bin/activate # macOS/Linux

2. Install dependencies:
   pip install -r requirements.txt

3. Create .env file:
   cp .env.example .env

4. Update .env with Supabase credentials:
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-anon-key
   SECRET_KEY=your-jwt-secret

5. Set up database:
   - Go to Supabase console
   - Run schema.sql in SQL Editor
   - Verify tables and indexes exist

6. Start development server:
   python -m uvicorn app.main:app --reload

7. Access API:
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

# ============================================================

# 3. DOCKER DEPLOYMENT

# ============================================================

## Using Docker Compose (Local or Server)

1. Ensure Docker and Docker Compose are installed

2. Create .env file with Supabase credentials

3. Build and run:
   docker-compose up -d

4. Access API:
   http://localhost:8000

5. View logs:
   docker-compose logs -f api

6. Stop services:
   docker-compose down

## Manual Docker Build

1. Build image:
   docker build -t ai-pocket-cfo:latest .

2. Run container:
   docker run -d \
    --name air-api \
    -p 8000:8000 \
    -e SUPABASE_URL=https://your-project.supabase.co \
    -e SUPABASE_KEY=your-key \
    -e SECRET_KEY=your-secret \
    ai-pocket-cfo:latest

3. Access API:
   http://localhost:8000

# ============================================================

# 4. CLOUD DEPLOYMENT

# ============================================================

## Heroku Deployment

1. Install Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli

2. Login to Heroku:
   heroku login

3. Create Heroku app:
   heroku create your-app-name

4. Add buildpack for Python:
   heroku buildpacks:add heroku/python

5. Set environment variables:
   heroku config:set SUPABASE_URL=https://your-project.supabase.co
   heroku config:set SUPABASE_KEY=your-key
   heroku config:set SECRET_KEY=your-secret

6. Create Procfile in project root:
   web: uvicorn app.main:app --host 0.0.0.0 --port $PORT

7. Deploy:
   git push heroku main

8. View logs:
   heroku logs --tail

## AWS EC2 Deployment

1. Launch EC2 instance (Ubuntu 20.04+ recommended)

2. SSH into instance:
   ssh -i your-key.pem ubuntu@your-instance-ip

3. Install dependencies:
   sudo apt update
   sudo apt install python3-pip python3-venv git curl
   git clone your-repo-url
   cd module\ 4

4. Create virtual environment:
   python3 -m venv venv
   source venv/bin/activate

5. Install requirements:
   pip install -r requirements.txt

6. Create .env file with Supabase credentials

7. Install and run with Gunicorn:
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:8000 app.main:app

8. Use systemd to run as service (create /etc/systemd/system/api.service):
   [Unit]
   Description=AI Pocket CFO API
   After=network.target

   [Service]
   Type=notify
   User=ubuntu
   WorkingDirectory=/home/ubuntu/module\ 4
   Environment="PATH=/home/ubuntu/module\ 4/venv/bin"
   EnvironmentFile=/home/ubuntu/module\ 4/.env
   ExecStart=/home/ubuntu/module\ 4/venv/bin/gunicorn -w 4 app.main:app
   Restart=always

   [Install]
   WantedBy=multi-user.target

9. Enable service:
   sudo systemctl enable api
   sudo systemctl start api
   sudo systemctl status api

## Azure App Service Deployment

1. Install Azure CLI: https://docs.microsoft.com/en-us/cli/azure/

2. Login to Azure:
   az login

3. Create resource group:
   az group create --name myResourceGroup --location eastus

4. Create App Service plan:
   az appservice plan create \
    --name myAppServicePlan \
    --resource-group myResourceGroup \
    --sku B1 --is-linux

5. Create web app:
   az webapp create \
    --resource-group myResourceGroup \
    --plan myAppServicePlan \
    --name my-pocket-cfo-api \
    --runtime "python|3.11"

6. Configure environment variables:
   az webapp config appsettings set \
    --resource-group myResourceGroup \
    --name my-pocket-cfo-api \
    --settings SUPABASE_URL=... SUPABASE_KEY=... SECRET_KEY=...

7. Deploy with git:
   az webapp deployment source config-local-git \
    --resource-group myResourceGroup \
    --name my-pocket-cfo-api

   git remote add azure <url from above>
   git push azure main

## Google Cloud Run Deployment

1. Install Google Cloud SDK: https://cloud.google.com/sdk/docs/install

2. Login to GCP:
   gcloud auth login

3. Create container image:
   gcloud builds submit --tag gcr.io/your-project/ai-pocket-cfo

4. Deploy to Cloud Run:
   gcloud run deploy ai-pocket-cfo \
    --image gcr.io/your-project/ai-pocket-cfo \
    --platform managed \
    --region us-central1 \
    --set-env-vars SUPABASE_URL=...,SUPABASE_KEY=...,SECRET_KEY=...

5. Access API:
   gcloud run services describe ai-pocket-cfo --platform managed

## DigitalOcean App Platform

1. Push code to GitHub

2. Create New App:
   - Connect GitHub repository
   - Select Python configuration
   - Set environment variables

3. Deploy

4. Access at provided URL

# ============================================================

# 5. PRODUCTION CONFIGURATION

# ============================================================

## Environment Variables

Set these in production:

SUPABASE_URL=<your-supabase-url>
SUPABASE_KEY=<your-supabase-key>
SECRET_KEY=<strong-random-key>
DEBUG=False
LOG_LEVEL=info
ALLOWED_ORIGINS=https://yourdomain.com,https://api.yourdomain.com

## Nginx Configuration (if using reverse proxy)

location /transactions/ {
proxy_pass http://localhost:8000/transactions/;
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;

    # Timeouts
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;

}

## SSL Configuration

Use Let's Encrypt with Certbot:

sudo certbot certonly --nginx -d your-domain.com
sudo systemctl enable certbot timer
sudo systemctl start certbot timer

# ============================================================

# 6. MONITORING & MAINTENANCE

# ============================================================

## Health Monitoring

Monitor endpoint:
curl https://your-api.com/health

Check statistics:
curl https://your-api.com/

## Logging

View logs in production:

- AWS CloudWatch: Monitor EC2 CloudWatch Logs
- Heroku: heroku logs --tail
- Cloud Run: gcloud logging read
- Google Cloud: Cloud Logging console

## Database Backups

Supabase automatic backups:

- Go to Project Settings
- Backup settings are under "Backups"
- Enable automatic backups

Manual backup:

```sql
-- Export to CSV (in Supabase SQL Editor)
COPY transactions TO STDOUT WITH CSV HEADER;
```

## Performance Monitoring

Monitor API performance:

1. Track response times
2. Monitor error rates
3. Check database query performance
4. Set up alerts for issues

## Regular Maintenance

- [ ] Update dependencies monthly
- [ ] Review and optimize slow queries
- [ ] Check database storage usage
- [ ] Monitor API usage and costs
- [ ] Review and update security policies
- [ ] Test disaster recovery procedures

# ============================================================

# 7. TROUBLESHOOTING

# ============================================================

## Common Issues

### Supabase connection fails

Error: "SUPABASE_URL and SUPABASE_KEY must be set"
Solution: Verify .env file exists and has correct values

### 404 errors on database queries

Error: "Table not found"
Solution: Run schema.sql in Supabase to create tables

### JWT authentication fails

Error: "Invalid token"
Solution: Implement proper JWT extraction in get_user_id()

### CORS errors

Error: "Access to XMLHttpRequest blocked by CORS"
Solution: Update ALLOWED_ORIGINS in .env or app configuration

### Large file uploads fail

Error: "Request entity too large"
Solution: Increase max upload size in Nginx/reverse proxy

### Database is slow

Solution:

1. Check query performance: SELECT \* FROM pg_stat_statements
2. Verify indexes exist: SELECT \* FROM pg_indexes
3. Analyze table: ANALYZE transactions;
4. Update statistics: VACUUM ANALYZE transactions;

## Debug Mode

Enable debug logging:

1. Set DEBUG=True in .env
2. Set LOG_LEVEL=debug
3. Restart application
4. Check logs for detailed information

## Testing Endpoints

Use curl or Postman:

# Health check

curl https://your-api.com/health

# Get transactions

curl https://your-api.com/transactions

# Create transaction

curl -X POST https://your-api.com/transactions \
 -H "Content-Type: application/json" \
 -d '{"description":"Test","amount":100,"type":"expense","category":"Test","transaction_date":"2024-02-27"}'

# ============================================================

# 8. SCALING FOR PRODUCTION

# ============================================================

## Horizontal Scaling

1. Load Balancing
   - Use NGINX or cloud load balancer
   - Distribute requests across multiple API instances

2. Database
   - Upgrade Supabase plan for more connections
   - Implement read replicas if needed
   - Use connection pooling (PgBouncer)

3. Caching
   - Add Redis for caching frequent queries
   - Cache export reports
   - Implement client-side caching headers

## Vertical Scaling

1. Increase server resources (CPU, RAM)
2. Upgrade database plan
3. Increase API container resources

## Cost Optimization

1. Monitor Supabase usage
2. Implement caching to reduce queries
3. Use database replicas wisely
4. Optimize API response times
5. Consider reserved capacity if using major clouds

# ============================================================

# 9. COMPLIANCE & SECURITY

# ============================================================

## GDPR Compliance

- [ ] Implement user data export feature
- [ ] Implement user data deletion
- [ ] Keep data retention policies
- [ ] Consent management

## Data Encryption

- [ ] Use HTTPS/TLS for all communications
- [ ] Use Supabase encrypted connections
- [ ] Encrypt sensitive data at rest
- [ ] Use secure key management

## Access Control

- [ ] Implement proper authentication
- [ ] Use Row Level Security in database
- [ ] Implement audit logging
- [ ] Regular access reviews

## Backup & Disaster Recovery

- [ ] Enable automatic backups
- [ ] Test backup restoration
- [ ] Document recovery procedures
- [ ] Maintain off-site backups
