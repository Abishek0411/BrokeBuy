# BrokeBuy Resource Optimization Guide

## 🎯 Problem Solved

**Before**: MongoDB and Docker were running automatically on startup, consuming ~233MB RAM constantly.

**After**: Services start only when needed, saving resources when not in use.

## 📊 Current Resource Usage

- **MongoDB**: ~157MB RAM, 0.4% CPU (when running)
- **Docker**: ~72MB RAM, 0.0% CPU (when running)
- **Total**: ~229MB RAM (only when actively using BrokeBuy)

## 🚀 Optimized Workflow

### For Development

```bash
# Start everything (services + applications)
./optimized-dev-start.sh

# Stop applications (keeps MongoDB/Docker running)
./optimized-dev-stop.sh

# Stop everything to save resources
./stop-services.sh
```

### For Production (Docker)

```bash
# Start system services first
./start-services.sh

# Start Docker applications
./docker-start.sh

# Stop Docker applications
./docker-stop.sh

# Stop system services to save resources
./stop-services.sh
```

## 🛠️ Available Scripts

### System Service Management
- `./start-services.sh` - Start MongoDB and Docker only
- `./stop-services.sh` - Stop MongoDB and Docker to save resources

### Development (Local)
- `./optimized-dev-start.sh` - Start everything for development
- `./optimized-dev-stop.sh` - Stop applications (asks about system services)
- `./dev-start.sh` - Original script (assumes services already running)
- `./dev-stop.sh` - Original stop script

### Production (Docker)
- `./docker-start.sh` - Start all Docker services
- `./docker-stop.sh` - Stop all Docker services
- `./docker-dev.sh` - Start Docker in development mode
- `./docker-stop-dev.sh` - Stop Docker development services

### Resource Management
- `./resource-monitor.sh` - Check current resource usage
- `./docker-cleanup.sh` - Clean up Docker resources

## 💡 Resource Saving Tips

### 1. **Stop Services When Not Needed**
```bash
# When you're done working on BrokeBuy
./stop-services.sh
```
This saves ~229MB RAM and stops CPU usage.

### 2. **Clean Up Docker Resources**
```bash
# Clean up unused Docker resources
./docker-cleanup.sh
```

### 3. **Monitor Resource Usage**
```bash
# Check what's using resources
./resource-monitor.sh
```

### 4. **Use Optimized Scripts**
Always use the `optimized-*` scripts for development as they:
- Start services only when needed
- Ask if you want to stop services to save resources
- Provide better resource management

## 🔄 Service States

### System Services (MongoDB + Docker)
- **Running**: Consumes ~229MB RAM
- **Stopped**: 0MB RAM, 0% CPU
- **Auto-start**: ❌ Disabled (saves resources on boot)

### Application Services (Backend + Scraper + Frontend)
- **Running**: Additional ~50-100MB RAM per service
- **Stopped**: 0MB RAM, 0% CPU
- **Dependencies**: Require MongoDB and Docker to be running

## 📈 Resource Usage Comparison

| Scenario | RAM Usage | CPU Usage | Notes |
|----------|-----------|-----------|-------|
| **System Idle** | ~4GB | ~26% | Normal system usage |
| **MongoDB + Docker Only** | ~4.2GB | ~26% | +229MB for services |
| **Full BrokeBuy Running** | ~4.3GB | ~27% | +100MB for applications |
| **Services Stopped** | ~4GB | ~26% | Back to normal |

## 🎯 Recommended Usage Patterns

### Daily Development
1. `./optimized-dev-start.sh` - Start working
2. Work on your project
3. `./optimized-dev-stop.sh` - Stop when done
4. Choose "Yes" to stop system services and save resources

### Occasional Use
1. `./start-services.sh` - Start services
2. `./docker-start.sh` - Start applications
3. Use the application
4. `./docker-stop.sh` - Stop applications
5. `./stop-services.sh` - Stop services

### Long-term Development
1. `./start-services.sh` - Start services once
2. Use `./dev-start.sh` and `./dev-stop.sh` for quick starts/stops
3. `./stop-services.sh` - Stop when done for the day

## 🔧 Troubleshooting

### Services Won't Start
```bash
# Check if services are running
./resource-monitor.sh

# Start services manually
sudo systemctl start mongod
sudo systemctl start docker
```

### High Resource Usage
```bash
# Check what's using resources
./resource-monitor.sh

# Clean up Docker
./docker-cleanup.sh

# Stop services
./stop-services.sh
```

### Port Conflicts
```bash
# Check what's using ports
lsof -i :8000
lsof -i :3001
lsof -i :5173

# Kill processes if needed
sudo kill -9 <PID>
```

## ✅ Benefits

1. **Resource Efficient**: Services only run when needed
2. **Faster Boot**: No auto-start services consuming resources
3. **Better Control**: Explicit control over when services run
4. **Monitoring**: Easy resource usage monitoring
5. **Cleanup**: Built-in Docker resource cleanup
6. **Flexible**: Choose between local development or Docker deployment

Your system will now boot faster and use fewer resources when you're not actively working on BrokeBuy! 🎉
