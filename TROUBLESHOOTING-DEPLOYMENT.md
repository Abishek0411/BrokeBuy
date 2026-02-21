# BrokeBuy Deployment Troubleshooting Guide

## 🔍 **Quick Diagnostics**

If you can't access your website, run these checks to diagnose the issue:

### **1. Check Local Services (Development)**
```bash
# Check if services are running locally
curl http://localhost:8000/health  # Backend
curl http://localhost:5173/        # Frontend
curl http://localhost:3001/health  # Scraper

# If not running, start them:
./optimized-dev-start.sh
```

### **2. Check Server Deployment (Production)**

#### **Option A: Using Management Script**
```bash
# Check service status
./server-management.sh status

# View logs
./server-management.sh logs

# Check specific service
./server-management.sh logs backend
```

#### **Option B: Direct SSH Check**
```bash
# Connect to server
ssh srmadmin@172.16.0.60

# Check running containers
docker ps

# Check service logs
cd /home/srmadmin/BrokeBuy/backend
docker-compose -f docker-compose.prod.yml logs

# Check specific service
docker-compose -f docker-compose.prod.yml logs backend
```

### **3. Port Checking**

Your deployment uses these ports:
- **Frontend**: Port 8081 (mapped from 80 inside container)
- **Backend**: Port 8001 (mapped from 8000 inside container)
- **Scraper**: Port 3001
- **MongoDB**: Port 27017

**Access URLs:**
- Local (college WiFi): `http://172.16.0.60:8081` (Frontend)
- Local API: `http://172.16.0.60:8001` (Backend)
- Global (if tunnel set up): `https://brokebuy-srm.trycloudflare.com`

## 🚨 **Common Issues**

### **Issue 1: Server Not Reachable**
**Symptom**: `Connection timed out` when accessing server

**Solutions:**
1. **Check if you're on college WiFi**
   - Server IP `172.16.0.60` is only accessible from college network

2. **Check if services are running**
   ```bash
   ./server-management.sh status
   ```

3. **Deploy/Re-deploy services**
   ```bash
   ./deploy-optimized.sh
   ```

### **Issue 2: Services Not Starting**
**Symptom**: Containers start but immediately stop

**Diagnosis:**
```bash
# Check logs
./server-management.sh logs

# Check specific service
docker-compose -f docker-compose.prod.yml logs backend
```

**Common Causes:**
1. **Missing environment variables**
   - Check `.env.prod` file on server
   - Ensure all required variables are set

2. **Port conflicts**
   - Check if ports 8081, 8001, 3001 are already in use
   ```bash
   # On server
   sudo netstat -tulpn | grep -E "8081|8001|3001"
   ```

3. **Build failures**
   - Check Docker build logs
   ```bash
   docker-compose -f docker-compose.prod.yml build --no-cache
   ```

### **Issue 3: Can Access Backend but Not Frontend**
**Symptom**: API works but website doesn't load

**Check:**
1. **Frontend container status**
   ```bash
   docker ps | grep frontend
   ```

2. **Frontend logs**
   ```bash
   docker-compose -f docker-compose.prod.yml logs frontend
   ```

3. **Rebuild frontend**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d --build frontend
   ```

### **Issue 4: Database Connection Errors**
**Symptom**: Backend can't connect to MongoDB

**Check:**
1. **MongoDB container status**
   ```bash
   docker ps | grep mongodb
   ```

2. **Check MongoDB logs**
   ```bash
   docker-compose -f docker-compose.prod.yml logs mongodb
   ```

3. **Verify environment variables**
   ```bash
   # On server
   cd /home/srmadmin/BrokeBuy/backend
   cat .env.prod | grep MONGO
   ```

4. **Restart MongoDB**
   ```bash
   docker-compose -f docker-compose.prod.yml restart mongodb
   ```

### **Issue 5: Wrong Port Numbers**
**Symptom**: Connection refused or wrong service

**Current Port Mapping:**
- Frontend: `172.16.0.60:8081` (NOT port 80)
- Backend: `172.16.0.60:8001` (NOT port 8000)
- Scraper: `172.16.0.60:3001`
- MongoDB: `172.16.0.60:27017`

**Why different ports?**
- Port 80 and 8000 might be used by other services on college server
- Using 8081 and 8001 avoids conflicts

## 🛠️ **Fix Common Issues**

### **Quick Re-deployment**
```bash
# Stop everything
./server-management.sh stop

# Deploy again
./deploy-optimized.sh

# Check status
./server-management.sh status
```

### **Restart Specific Service**
```bash
# Restart backend only
./server-management.sh logs backend
# Then manually restart if needed

# On server:
cd /home/srmadmin/BrokeBuy/backend
docker-compose -f docker-compose.prod.yml restart backend
```

### **Full Clean Rebuild**
```bash
# On server
ssh srmadmin@172.16.0.60
cd /home/srmadmin/BrokeBuy/backend

# Stop and remove everything
docker-compose -f docker-compose.prod.yml down -v

# Rebuild from scratch
docker-compose -f docker-compose.prod.yml up -d --build

# Check status
docker-compose -f docker-compose.prod.yml ps
```

## 📊 **Health Check Endpoints**

Test these endpoints to verify services:
```bash
# Backend health
curl http://172.16.0.60:8001/health

# Scraper health
curl http://172.16.0.60:3001/health

# Frontend
curl http://172.16.0.60:8081
```

## 🆘 **Still Having Issues?**

### **Collect Diagnostics:**
```bash
# Create diagnostics file
cat > diagnostics.txt << 'EOF'
# Server Info
cat /etc/os-release

# Docker Info
docker --version
docker-compose --version

# Running Containers
docker ps -a

# Container Logs
docker-compose -f docker-compose.prod.yml logs --tail=100

# Disk Space
df -h

# Memory
free -h
EOF

# Run diagnostics
ssh srmadmin@172.16.0.60 < diagnostics.txt > server-diagnostics.log
```

### **Common Commands Reference:**
```bash
# View all logs
./server-management.sh logs

# View specific service
./server-management.sh logs backend
./server-management.sh logs frontend
./server-management.sh logs scraper

# Restart services
./server-management.sh restart

# Stop services
./server-management.sh stop

# Start services
./server-management.sh start

# Check status
./server-management.sh status

# Monitor resources
./server-management.sh monitor
```

## 🎯 **Quick Actions**

### **If Website Not Loading:**
1. Check `http://172.16.0.60:8081` (correct port!)
2. Run `./server-management.sh status`
3. Check logs: `./server-management.sh logs frontend`
4. Rebuild if needed: `docker-compose -f docker-compose.prod.yml up -d --build`

### **If API Not Working:**
1. Check `http://172.16.0.60:8001/health`
2. Check logs: `./server-management.sh logs backend`
3. Verify `.env.prod` on server
4. Check MongoDB: `docker-compose logs mongodb`

### **If Can't Connect to Server:**
1. Verify you're on college WiFi
2. Try: `ping 172.16.0.60`
3. Check SSH: `ssh srmadmin@172.16.0.60`
4. May need to deploy from college network
