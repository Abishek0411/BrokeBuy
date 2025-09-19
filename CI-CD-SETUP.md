# CI/CD Setup for BrokeBuy

This guide explains how to set up Continuous Integration and Continuous Deployment (CI/CD) for your BrokeBuy project.

## 🚀 **Current Deployment Process**

### What the Script Does:
- ✅ **Copies all 3 folders** (backend, frontend, scraper)
- ✅ **Handles all dependencies** via Docker (no manual npm/pip installs)
- ✅ **Builds and starts all services** automatically
- ✅ **Verifies deployment** with health checks

### Dependencies Management:
- **Backend**: Python dependencies installed in Docker container
- **Frontend**: Node.js dependencies installed in Docker container  
- **Scraper**: Node.js dependencies installed in Docker container
- **Database**: MongoDB runs in separate container

## 🔄 **CI/CD Options**

### Option 1: GitHub Actions (Recommended)

**Setup Steps:**

1. **Add SSH Key to GitHub Secrets:**
   ```bash
   # Generate SSH key pair (if you don't have one)
   ssh-keygen -t rsa -b 4096 -C "your-email@example.com"
   
   # Copy public key to server
   ssh-copy-id srmadmin@172.16.0.60
   
   # Add private key to GitHub Secrets:
   # Go to: Settings → Secrets and variables → Actions
   # Add: SERVER_SSH_KEY (paste your private key)
   ```

2. **Push the workflow file:**
   ```bash
   git add .github/workflows/deploy.yml
   git commit -m "Add CI/CD workflow"
   git push origin main
   ```

3. **Automatic Deployment:**
   - Every push to `main` branch triggers deployment
   - Manual trigger available in GitHub Actions tab

### Option 2: Manual Update Script

**For quick updates without full redeployment:**

```bash
# Update all services
./update-deploy.sh

# Update only backend
./update-deploy.sh --backend-only

# Update only frontend  
./update-deploy.sh --frontend-only

# Update only scraper
./update-deploy.sh --scraper-only

# Fast update (no rebuild)
./update-deploy.sh --no-rebuild
```

### Option 3: Webhook-based Deployment

**For real-time updates:**

1. **Create webhook endpoint on server**
2. **Set up GitHub webhook** to trigger on push
3. **Automatically deploy** when code changes

## 📋 **Deployment Workflow**

### Initial Deployment:
```bash
# 1. Configure environment
cp env.prod.template .env.prod
nano .env.prod  # Edit with your values

# 2. Deploy everything
./deploy.sh
```

### Updates:
```bash
# Option A: Full redeployment
./deploy.sh

# Option B: Selective update
./update-deploy.sh --backend-only

# Option C: GitHub Actions (automatic)
git push origin main
```

## 🔧 **Environment Management**

### Production Environment Variables:
```bash
# Required in .env.prod
MONGO_ROOT_USERNAME=admin
MONGO_ROOT_PASSWORD=your_secure_password
JWT_SECRET_KEY=your_jwt_secret_key
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
ENVIRONMENT=production
```

### Security Best Practices:
- ✅ Never commit `.env` files
- ✅ Use strong, unique passwords
- ✅ Rotate secrets regularly
- ✅ Use environment-specific configurations

## 🚨 **Rollback Strategy**

### Quick Rollback:
```bash
# Stop current services
./server-management.sh stop

# Deploy previous version
git checkout <previous-commit>
./deploy.sh

# Or restore from backup
./server-management.sh restore backup_file.tar.gz
```

### Database Rollback:
```bash
# Restore database from backup
./server-management.sh restore backup_20241201_120000.tar.gz
```

## 📊 **Monitoring & Health Checks**

### Service Health:
```bash
# Check all services
./server-management.sh status

# View logs
./server-management.sh logs

# Monitor resources
./server-management.sh monitor
```

### Health Check Endpoints:
- Backend: `http://172.16.0.60:8000/health`
- Scraper: `http://172.16.0.60:3001/health`
- Frontend: `http://172.16.0.60/`

## 🔄 **Update Workflow Examples**

### Backend Code Change:
```bash
# 1. Make changes to backend code
# 2. Test locally
# 3. Update production
./update-deploy.sh --backend-only
```

### Frontend UI Change:
```bash
# 1. Make changes to frontend code
# 2. Test locally
# 3. Update production
./update-deploy.sh --frontend-only
```

### Full Application Update:
```bash
# 1. Make changes to any part
# 2. Test locally
# 3. Update production
./update-deploy.sh --all
```

### Emergency Hotfix:
```bash
# 1. Make critical fix
# 2. Quick update without rebuild
./update-deploy.sh --backend-only --no-rebuild
```

## 🛠 **Troubleshooting CI/CD**

### Common Issues:

1. **SSH Connection Failed:**
   ```bash
   # Test SSH connection
   ssh srmadmin@172.16.0.60
   
   # Check SSH key
   ssh-add -l
   ```

2. **Docker Build Failed:**
   ```bash
   # Check Docker logs
   ./server-management.sh logs backend
   
   # Rebuild manually
   ./update-deploy.sh --backend-only
   ```

3. **Service Unhealthy:**
   ```bash
   # Check service status
   ./server-management.sh status
   
   # View detailed logs
   ./server-management.sh logs
   ```

4. **Permission Denied:**
   ```bash
   # Fix file permissions
   chmod +x *.sh
   
   # Check Docker permissions
   sudo usermod -aG docker $USER
   ```

## 📈 **Advanced CI/CD Features**

### Automated Testing:
- Add tests to GitHub Actions workflow
- Run tests before deployment
- Deploy only if tests pass

### Staging Environment:
- Create separate staging server
- Test changes before production
- Blue-green deployment strategy

### Database Migrations:
- Automated database schema updates
- Rollback support for migrations
- Data integrity checks

### Monitoring Integration:
- Health check notifications
- Performance monitoring
- Error tracking and alerting

## 🎯 **Recommended Workflow**

1. **Development**: Work on feature branches
2. **Testing**: Test locally with Docker
3. **Pull Request**: Create PR to main branch
4. **Review**: Code review and approval
5. **Merge**: Merge to main branch
6. **Deploy**: Automatic deployment via GitHub Actions
7. **Monitor**: Check deployment status and logs
8. **Rollback**: If issues, rollback to previous version

This setup provides a robust, automated deployment pipeline that handles all your dependencies and ensures consistent deployments! 🚀
