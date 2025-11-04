# Podcast Generator Webapp - Deployment Guide

## Prerequisites

Before deploying, ensure you have:
- Docker and Docker Compose installed
- Google Gemini API key ([Get it here](https://makersuite.google.com/app/apikey))
- DeepSeek API key ([Get it here](https://platform.deepseek.com/api_keys))

---

## Quick Start (Local Deployment)

### 1. Clone and Setup

```bash
cd /home/user/podcastwebapp
```

### 2. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your preferred editor
```

Required variables in `.env`:
```bash
GOOGLE_API_KEY=your_actual_google_api_key
DEEPSEEK_KEY=your_actual_deepseek_key
FLASK_ENV=production
PORT=5000
LOG_LEVEL=INFO
```

### 3. Build and Run with Docker Compose

```bash
# Build the Docker image
docker-compose build

# Start the application
docker-compose up -d

# Check logs
docker-compose logs -f web
```

### 4. Verify Deployment

Open your browser and navigate to:
- **Web UI**: http://localhost:5000
- **Health Check**: http://localhost:5000/api/health

Expected health check response:
```json
{
  "status": "healthy",
  "pipeline_ready": true,
  "api_keys_configured": true
}
```

### 5. Stop the Application

```bash
docker-compose down
```

---

## Production Deployment Options

### Option 1: Deploy to Cloud VM (AWS EC2, DigitalOcean, etc.)

1. **Provision a VM**
   - Minimum specs: 2 CPU, 4GB RAM
   - OS: Ubuntu 20.04+ or similar
   - Open port 5000 (or configure reverse proxy)

2. **Install Docker**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   ```

3. **Clone Repository**
   ```bash
   git clone <your-repo-url>
   cd podcastwebapp
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   nano .env  # Add your API keys
   ```

5. **Deploy**
   ```bash
   docker-compose up -d
   ```

6. **Setup Nginx Reverse Proxy (Recommended)**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;

           # Important: Increase timeouts for long-running AI requests
           proxy_read_timeout 600s;
           proxy_connect_timeout 600s;
           proxy_send_timeout 600s;
       }
   }
   ```

7. **Setup SSL with Let's Encrypt**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

---

### Option 2: Deploy to Railway.app

1. **Create account** at [railway.app](https://railway.app)

2. **Create new project** from GitHub repository

3. **Add environment variables** in Railway dashboard:
   - `GOOGLE_API_KEY`
   - `DEEPSEEK_KEY`
   - `FLASK_ENV=production`
   - `PORT=5000`

4. **Deploy automatically** - Railway will detect Dockerfile and deploy

---

### Option 3: Deploy to Render.com

1. **Create account** at [render.com](https://render.com)

2. **Create new Web Service** from GitHub repository

3. **Configure service**:
   - Build Command: `docker build -t podcast-generator .`
   - Start Command: (uses Dockerfile CMD)
   - Environment Variables: Add your API keys

4. **Deploy** - Render will automatically build and deploy

---

### Option 4: Deploy to AWS ECS (Container Service)

1. **Push image to ECR**:
   ```bash
   aws ecr create-repository --repository-name podcast-generator
   docker build -t podcast-generator .
   docker tag podcast-generator:latest <ecr-url>/podcast-generator:latest
   docker push <ecr-url>/podcast-generator:latest
   ```

2. **Create ECS task definition** with:
   - Container port: 5000
   - Environment variables for API keys
   - Minimum 2GB memory

3. **Create ECS service** with Application Load Balancer

---

### Option 5: Deploy to Google Cloud Run

1. **Build and push to Google Container Registry**:
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT_ID/podcast-generator
   ```

2. **Deploy to Cloud Run**:
   ```bash
   gcloud run deploy podcast-generator \
     --image gcr.io/PROJECT_ID/podcast-generator \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars "GOOGLE_API_KEY=your_key,DEEPSEEK_KEY=your_key" \
     --memory 2Gi \
     --timeout 600s
   ```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_API_KEY` | ✅ Yes | - | Google Gemini API key for text analysis |
| `DEEPSEEK_KEY` | ✅ Yes | - | DeepSeek API key for script generation |
| `FLASK_ENV` | No | production | Flask environment (development/production) |
| `PORT` | No | 5000 | Application port |
| `LOG_LEVEL` | No | INFO | Logging level (DEBUG/INFO/WARNING/ERROR) |

---

## Health Checks & Monitoring

### Health Check Endpoint
```bash
curl http://localhost:5000/api/health
```

### Check Docker Container Status
```bash
docker-compose ps
```

### View Logs
```bash
# Docker Compose logs
docker-compose logs -f web

# Application logs (mounted volume)
tail -f logs/app_*.log
```

### Monitor Resource Usage
```bash
docker stats
```

---

## Persistence & Data

The application stores generated content in mounted volumes:

- **`./outputs/`** - Generated podcast scripts
  - `outputs/json/` - Analysis JSON files
  - `outputs/scripts/` - Generated script text files

- **`./logs/`** - Application logs

These directories are automatically created and persist across container restarts.

---

## Scaling Considerations

### Horizontal Scaling
To handle more concurrent requests, increase Gunicorn workers in `Dockerfile`:
```dockerfile
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "8", "--timeout", "300", "app:app"]
```

Recommended workers: `(2 × CPU cores) + 1`

### Vertical Scaling
- Minimum: 2 CPU, 4GB RAM
- Recommended: 4 CPU, 8GB RAM
- High traffic: 8 CPU, 16GB RAM

### Load Balancing
For multiple instances, use:
- AWS Application Load Balancer
- Nginx with upstream servers
- Cloud provider load balancers

---

## Security Best Practices

1. **Never commit `.env` files**
   - Already in `.gitignore`
   - Use secrets management (AWS Secrets Manager, etc.)

2. **Use HTTPS in production**
   - Configure SSL/TLS certificates
   - Use reverse proxy (Nginx, Caddy)

3. **Restrict access to health endpoint**
   - Use internal health checks only
   - Add authentication if exposed

4. **Regular updates**
   ```bash
   # Update base image
   docker-compose pull
   docker-compose up -d
   ```

5. **Rate limiting**
   - Implement at reverse proxy level
   - Use API gateway for cloud deployments

---

## Troubleshooting

### Issue: Container exits immediately
```bash
# Check logs
docker-compose logs web

# Common causes:
# - Missing API keys in .env
# - Port already in use
# - Syntax errors in code
```

### Issue: Health check failing
```bash
# Test health endpoint manually
docker-compose exec web curl http://localhost:5000/api/health

# Check if API keys are loaded
docker-compose exec web env | grep API_KEY
```

### Issue: Out of memory
```bash
# Increase Docker memory limit
# In docker-compose.yml, add to web service:
deploy:
  resources:
    limits:
      memory: 4G
```

### Issue: Slow response times
- Increase Gunicorn timeout: `--timeout 600`
- Check API rate limits for Gemini/DeepSeek
- Verify network connectivity to APIs

---

## CI/CD Pipeline Example (GitHub Actions)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: docker build -t podcast-generator .

      - name: Deploy to production
        run: |
          # Add your deployment script here
          # e.g., push to registry, update ECS service, etc.
```

---

## Cost Estimates

### API Costs (approximate)
- **Google Gemini**: ~$0.002 per request
- **DeepSeek**: ~$0.01-0.05 per generation
- **Per podcast script**: ~$0.05-0.10

### Infrastructure Costs
- **AWS EC2 (t3.medium)**: ~$30/month
- **DigitalOcean Droplet**: ~$24/month
- **Railway.app**: $5-20/month
- **Render.com**: Free tier available, then $7/month
- **Google Cloud Run**: Pay per request (~$10-50/month depending on usage)

---

## Next Steps

After deployment:

1. ✅ Test the web interface
2. ✅ Generate a sample podcast script
3. ✅ Monitor logs for errors
4. ✅ Setup monitoring/alerting
5. ✅ Configure backups for outputs directory
6. ✅ Setup custom domain (optional)
7. ✅ Implement rate limiting (for public access)

---

## Support & Documentation

- **Main README**: [README.md](README.md)
- **API Documentation**: See README.md#api-endpoints
- **Configuration**: [config/config.py](config/config.py)
- **Issues**: Report bugs via GitHub issues

---

## Quick Commands Reference

```bash
# Start application
docker-compose up -d

# Stop application
docker-compose down

# View logs
docker-compose logs -f web

# Rebuild after code changes
docker-compose up -d --build

# Check health
curl http://localhost:5000/api/health

# View running containers
docker-compose ps

# Access container shell
docker-compose exec web /bin/bash

# Clean up everything
docker-compose down -v
docker system prune -a
```
