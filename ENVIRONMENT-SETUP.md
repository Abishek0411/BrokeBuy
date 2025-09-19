# 🔐 Environment Variables Setup Guide

This guide explains how to set up environment variables for the BrokeBuy project.

## 📁 Environment Files

### `.env.example`
- **Purpose**: Template file showing required environment variables
- **Git Status**: ✅ Committed to repository
- **Usage**: Copy this file to create your local `.env`

### `.env`
- **Purpose**: Local development environment variables
- **Git Status**: ❌ Ignored by Git (contains sensitive data)
- **Usage**: Your actual development credentials

### `.env.docker`
- **Purpose**: Docker Compose environment variables
- **Git Status**: ❌ Ignored by Git (contains sensitive data)
- **Usage**: Docker container environment

## 🚀 Quick Setup

### 1. For Local Development
```bash
# Copy the example file
cp .env.example .env

# Edit with your actual values
nano .env
```

### 2. For Docker Development
```bash
# Copy the example file
cp .env.example .env.docker

# Edit with your actual values
nano .env.docker
```

## 🔧 Required Environment Variables

### Database
```bash
MONGO_URI=mongodb://localhost:27017/brokebuy
```

### JWT Configuration
```bash
JWT_SECRET_KEY=your_very_secure_jwt_secret_key_here
JWT_ALGORITHM=HS256
```

### Cloudinary Configuration
```bash
CLOUDINARY_CLOUD_NAME=your_cloudinary_cloud_name
CLOUDINARY_API_KEY=your_cloudinary_api_key
CLOUDINARY_API_SECRET=your_cloudinary_api_secret
```

### Development Settings
```bash
DEV_MODE=true
```

## 🐳 Docker-Specific Notes

- For Docker Compose, use `mongodb://mongodb:27017/brokebuy` as the MONGO_URI
- The `.env.docker` file is used by Docker Compose
- Make sure to update both `.env` and `.env.docker` with your credentials

## 🔒 Security Best Practices

1. **Never commit `.env` or `.env.docker` files**
2. **Use strong, unique JWT secret keys**
3. **Rotate credentials regularly**
4. **Use different credentials for development and production**
5. **Consider using a secrets management service for production**

## 🚨 Important Notes

- The `.env.example` file contains placeholder values
- You must replace all placeholder values with your actual credentials
- Without proper environment variables, the application will not work
- Docker Compose will fail if `.env.docker` is missing

## 🆘 Troubleshooting

### "Environment variable not found" errors
- Check that your `.env` file exists and contains all required variables
- Verify there are no spaces around the `=` sign
- Make sure there are no quotes around the values unless needed

### Docker Compose fails to start
- Ensure `.env.docker` file exists
- Check that all required variables are set
- Verify the MONGO_URI points to the correct MongoDB container

### Database connection issues
- For local development: use `mongodb://localhost:27017/brokebuy`
- For Docker: use `mongodb://mongodb:27017/brokebuy`
- Ensure MongoDB is running before starting the backend
