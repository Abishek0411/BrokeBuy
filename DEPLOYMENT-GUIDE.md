# BrokeBuy Production Deployment Guide

This guide provides step-by-step instructions for deploying the BrokeBuy application to your college server.

## Prerequisites

- SSH access to the server (`srmadmin@172.16.0.60`)
- Docker and Docker Compose installed on the server
- All project files ready for deployment

## Quick Deployment (Minimal Steps)

### 1. Configure Environment Variables

```bash
# Copy the environment template
cp env.prod.template .env.prod

# Edit the environment file with your actual values
nano .env.prod
```

**Required Configuration:**
- `MONGO_ROOT_PASSWORD`: Set a strong password for MongoDB
- `JWT_SECRET_KEY`: Generate a long, random secret key
- `CLOUDINARY_*`: Your Cloudinary credentials for image uploads

### 2. Deploy to Server

```bash
# Run the deployment script
./deploy.sh
```

The script will:
- Copy all project files to the server
- Install Docker and Docker Compose (if needed)
- Build and start all services
- Verify the deployment

### 3. Access Your Application

After successful deployment, your application will be available at:
- **Frontend**: http://172.16.0.60
- **Backend API**: http://172.16.0.60:8000
- **API Documentation**: http://172.16.0.60:8000/docs
- **Scraper Service**: http://172.16.0.60:3001

## Server Management

Use the management script for common operations:

```bash
# Check service status
./server-management.sh status

# View logs
./server-management.sh logs

# Restart services
./server-management.sh restart

# Stop services
./server-management.sh stop

# Start services
./server-management.sh start

# Update services
./server-management.sh update

# Backup database
./server-management.sh backup

# Monitor resources
./server-management.sh monitor

# Open shell on server
./server-management.sh shell
```

## Manual Deployment (Alternative)

If you prefer manual deployment:

### 1. Connect to Server
```bash
ssh srmadmin@172.16.0.60
```

### 2. Create Project Directory
```bash
mkdir -p /home/srmadmin/brokebuy
cd /home/srmadmin/brokebuy
```

### 3. Copy Project Files
```bash
# From your local machine
scp -r /home/abishek/Downloads/proj_BrokeBuy_backend/* srmadmin@172.16.0.60:/home/srmadmin/brokebuy/
scp -r /home/abishek/Downloads/proj_BrokeBuy_frontend srmadmin@172.16.0.60:/home/srmadmin/
scp -r /home/abishek/Downloads/SRM-Academia-Scraper-node-main srmadmin@172.16.0.60:/home/srmadmin/
```

### 4. Install Docker (if not installed)
```bash
# On the server
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER
rm get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 5. Configure Environment
```bash
# On the server
cd /home/srmadmin/brokebuy
cp env.prod.template .env.prod
nano .env.prod  # Edit with your values
```

### 6. Start Services
```bash
# Build and start all services
docker-compose -f docker-compose.prod.yml up -d --build

# Check status
docker-compose -f docker-compose.prod.yml ps
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   sudo netstat -tulpn | grep :80
   
   # Stop conflicting services
   sudo systemctl stop apache2  # or nginx
   ```

2. **Permission Denied**
   ```bash
   # Add user to docker group
   sudo usermod -aG docker $USER
   # Log out and back in
   ```

3. **Services Not Starting**
   ```bash
   # Check logs
   docker-compose -f docker-compose.prod.yml logs
   
   # Check individual service logs
   docker-compose -f docker-compose.prod.yml logs backend
   ```

4. **Database Connection Issues**
   ```bash
   # Check MongoDB logs
   docker-compose -f docker-compose.prod.yml logs mongodb
   
   # Verify environment variables
   docker-compose -f docker-compose.prod.yml config
   ```

### Health Checks

```bash
# Check if services are responding
curl http://172.16.0.60/health
curl http://172.16.0.60:8000/health
curl http://172.16.0.60:3001/health
```

## Security Considerations

1. **Change Default Passwords**: Update MongoDB root password
2. **Use Strong JWT Secret**: Generate a long, random JWT secret key
3. **Firewall Configuration**: Ensure only necessary ports are open
4. **SSL/HTTPS**: Consider setting up SSL certificates for production
5. **Regular Updates**: Keep Docker images and dependencies updated

## Backup and Recovery

### Database Backup
```bash
# Create backup
./server-management.sh backup

# Restore from backup
./server-management.sh restore backup_filename.tar.gz
```

### Full System Backup
```bash
# Backup entire application directory
tar -czf brokebuy_full_backup_$(date +%Y%m%d).tar.gz /home/srmadmin/brokebuy/
```

## Monitoring

### Resource Monitoring
```bash
# Check resource usage
./server-management.sh monitor

# View real-time logs
./server-management.sh logs
```

### Log Files
- Application logs: `docker-compose -f docker-compose.prod.yml logs`
- System logs: `/var/log/syslog`
- Docker logs: `journalctl -u docker.service`

## Updates and Maintenance

### Updating the Application
```bash
# Pull latest changes and rebuild
./server-management.sh update
```

### Regular Maintenance
```bash
# Clean up old Docker images
docker image prune -f

# Clean up unused volumes
docker volume prune -f

# Check disk space
df -h
```

## Support

If you encounter issues:
1. Check the logs: `./server-management.sh logs`
2. Verify service status: `./server-management.sh status`
3. Check resource usage: `./server-management.sh monitor`
4. Review this guide for troubleshooting steps

For additional help, refer to the Docker Compose documentation or contact your system administrator.
