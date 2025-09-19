# BrokeBuy - Docker Setup

This document explains how to run the BrokeBuy application using Docker for both development and production environments.

## 🏗️ Architecture

The application consists of 4 main services:
- **Backend**: FastAPI application (Python)
- **Scraper**: Node.js application for SRM Academia scraping
- **Frontend**: React application with Vite
- **Database**: MongoDB

## 🚀 Quick Start

### Development Mode (Recommended for local development)

```bash
# Start all services in development mode
./docker-dev.sh

# View logs
./docker-logs-dev.sh

# Stop services
./docker-stop-dev.sh
```

### Production Mode

```bash
# Start all services in production mode
./docker-start.sh

# View logs
./docker-logs.sh

# Stop services
./docker-stop.sh
```

## 📱 Service URLs

| Service | Development | Production |
|---------|-------------|------------|
| Backend API | http://localhost:8000 | http://localhost:8000 |
| API Documentation | http://localhost:8000/docs | http://localhost:8000/docs |
| Scraper | http://localhost:3001 | http://localhost:3001 |
| Frontend | http://localhost:5173 | http://localhost:80 |
| MongoDB | localhost:27017 | localhost:27017 |

## 🛠️ Manual Commands

### Development Mode

```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop services
docker-compose -f docker-compose.dev.yml down
```

### Production Mode

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🔧 Configuration

### Environment Variables

The application uses the following environment variables:

- `MONGO_URI`: MongoDB connection string
- `JWT_SECRET_KEY`: Secret key for JWT tokens
- `JWT_ALGORITHM`: JWT algorithm (default: HS256)
- `CLOUDINARY_CLOUD_NAME`: Cloudinary cloud name
- `CLOUDINARY_API_KEY`: Cloudinary API key
- `CLOUDINARY_API_SECRET`: Cloudinary API secret

### Database

MongoDB data is persisted in Docker volumes:
- Production: `brokebuy_mongodb_data`
- Development: `brokebuy_mongodb_dev_data`

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Check what's using the port
   lsof -i :8000
   
   # Kill the process
   kill -9 <PID>
   ```

2. **Docker not running**
   ```bash
   # Start Docker service
   sudo systemctl start docker
   ```

3. **Permission denied**
   ```bash
   # Make scripts executable
   chmod +x *.sh
   ```

4. **MongoDB connection issues**
   ```bash
   # Check MongoDB container logs
   docker-compose logs mongodb
   ```

### Reset Everything

```bash
# Stop all services
docker-compose down
docker-compose -f docker-compose.dev.yml down

# Remove all containers and volumes
docker-compose down -v
docker-compose -f docker-compose.dev.yml down -v

# Remove all images
docker-compose down --rmi all
docker-compose -f docker-compose.dev.yml down --rmi all
```

## 📦 Building Images

```bash
# Build all images
docker-compose build

# Build specific service
docker-compose build backend
```

## 🔍 Health Checks

All services include health checks:
- Backend: `http://localhost:8000/health`
- Scraper: `http://localhost:3001/health`
- Frontend: `http://localhost/` (or `http://localhost:5173` in dev)
- MongoDB: Internal ping command

## 📊 Monitoring

```bash
# View service status
docker-compose ps

# View resource usage
docker stats

# View specific service logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs scraper
docker-compose logs mongodb
```

## 🚀 Deployment

For production deployment on your college server:

1. Copy the entire project to the server
2. Update environment variables in `docker-compose.yml`
3. Run `./docker-start.sh`
4. Configure reverse proxy (nginx) if needed
5. Set up SSL certificates for HTTPS

## 📝 Notes

- Development mode includes hot reloading for all services
- Production mode uses optimized builds and nginx for the frontend
- All services are connected via a custom Docker network
- MongoDB data persists between container restarts
- Health checks ensure services are ready before dependent services start
