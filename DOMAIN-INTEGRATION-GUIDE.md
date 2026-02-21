# BrokeBuy Domain Integration Guide

## 🌐 **Overview**

This guide explains how to integrate a GoDaddy domain with your college server to make BrokeBuy accessible from anywhere on the internet, not just college WiFi.

## 🎯 **What We'll Achieve**

**Before:**
- Accessible only on college WiFi: `http://172.16.0.60`
- Internal IP address only
- Limited to college network

**After:**
- Accessible from anywhere: `https://yourdomain.com`
- Professional domain name
- Global internet access

## 🛒 **Step 1: Purchase Domain from GoDaddy**

### **Domain Selection:**
- Choose a relevant domain name (e.g., `srmbrokebuy.com`, `brokebuy-srm.com`)
- Consider `.com`, `.in`, or `.edu` extensions
- Check availability on GoDaddy

### **Recommended Domains:**
- `srmbrokebuy.com`
- `brokebuy-srm.com`
- `srmmarketplace.com`
- `srmbuyandsell.com`

## 🔧 **Step 2: Domain Configuration**

### **A. DNS Settings in GoDaddy:**

1. **Login to GoDaddy Account**
2. **Go to Domain Management**
3. **Click on "DNS" for your domain**
4. **Add/Modify DNS Records:**

```
Type    Name    Value                    TTL
A       @       172.16.0.60             600
A       www     172.16.0.60             600
CNAME   api     172.16.0.60             600
CNAME   admin   172.16.0.60             600
```

### **B. DNS Record Explanation:**

| Record Type | Name | Value | Purpose |
|-------------|------|-------|---------|
| **A** | `@` | `172.16.0.60` | Main domain points to server |
| **A** | `www` | `172.16.0.60` | www subdomain |
| **CNAME** | `api` | `172.16.0.60` | API subdomain |
| **CNAME** | `admin` | `172.16.0.60` | Admin panel |

## 🌍 **Step 3: Server Configuration**

### **A. Update Docker Compose for Domain:**

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  # Nginx Reverse Proxy with SSL
  nginx:
    image: nginx:alpine
    container_name: brokebuy-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - ./nginx/conf.d:/etc/nginx/conf.d
    depends_on:
      - frontend
      - backend
      - scraper
    networks:
      - brokebuy-network

  # Your existing services...
  backend:
    # ... existing config
    expose:
      - "8000"
  
  frontend:
    # ... existing config
    expose:
      - "80"
  
  scraper:
    # ... existing config
    expose:
      - "3001"
```

### **B. Nginx Configuration:**

```nginx
# nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }
    
    upstream frontend {
        server frontend:80;
    }
    
    upstream scraper {
        server scraper:3001;
    }

    # HTTP to HTTPS redirect
    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    # Main HTTPS server
    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;

        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Backend API
        location /api/ {
            proxy_pass http://backend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Scraper API
        location /scraper/ {
            proxy_pass http://scraper/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

## 🔒 **Step 4: SSL Certificate Setup**

### **Option A: Let's Encrypt (Free SSL)**

```bash
# Install Certbot
sudo apt-get update
sudo apt-get install certbot

# Get SSL certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Copy certificates to nginx directory
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./nginx/ssl/key.pem
```

### **Option B: GoDaddy SSL Certificate**

1. **Purchase SSL certificate from GoDaddy**
2. **Download certificate files**
3. **Place in `nginx/ssl/` directory**

## 🚀 **Step 5: Deployment with Domain**

### **A. Update Deployment Scripts:**

```bash
# Update deploy.sh to include domain setup
# Add domain configuration to environment variables
```

### **B. Environment Variables:**

```bash
# .env.prod
DOMAIN_NAME=yourdomain.com
SSL_EMAIL=your-email@example.com
```

## 📋 **Step 6: College Network Configuration**

### **A. Port Forwarding (If Possible):**
- Ask IT department to forward ports 80 and 443 to your server
- This allows external access to your domain

### **B. Alternative: Cloudflare Tunnel (Recommended)**

```bash
# Install Cloudflare Tunnel
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Create tunnel
cloudflared tunnel create brokebuy

# Configure tunnel
cloudflared tunnel route dns brokebuy yourdomain.com
```

## 🔧 **Step 7: Update Application Configuration**

### **A. Frontend Configuration:**

```typescript
// src/lib/axios.ts
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://yourdomain.com/api' 
  : 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
});
```

### **B. Backend Configuration:**

```python
# app/config.py
import os

DOMAIN_NAME = os.getenv("DOMAIN_NAME", "localhost")
CORS_ORIGINS = [
    f"https://{DOMAIN_NAME}",
    f"https://www.{DOMAIN_NAME}",
    "http://localhost:3000",  # For development
]
```

## 🌐 **Step 8: Final URLs**

After setup, your application will be accessible at:

- **Main Site**: `https://yourdomain.com`
- **API**: `https://yourdomain.com/api`
- **API Docs**: `https://yourdomain.com/api/docs`
- **Scraper**: `https://yourdomain.com/scraper`
- **Admin**: `https://admin.yourdomain.com`

## 🛠 **Deployment Commands**

### **Deploy with Domain:**

```bash
# 1. Configure domain in .env.prod
echo "DOMAIN_NAME=yourdomain.com" >> .env.prod

# 2. Deploy with domain configuration
./deploy-optimized.sh

# 3. Setup SSL certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# 4. Restart services
./server-management.sh restart
```

## 🔍 **Testing Domain Access**

### **A. DNS Propagation Check:**
```bash
# Check if domain points to your server
nslookup yourdomain.com
dig yourdomain.com
```

### **B. SSL Certificate Check:**
```bash
# Test SSL certificate
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com
```

### **C. Application Testing:**
```bash
# Test all endpoints
curl https://yourdomain.com
curl https://yourdomain.com/api/health
curl https://yourdomain.com/scraper/health
```

## 🚨 **Important Considerations**

### **A. College Network Policies:**
- Check if external access is allowed
- May need IT department approval
- Consider using Cloudflare Tunnel for bypassing restrictions

### **B. Security:**
- Always use HTTPS
- Implement proper CORS policies
- Use strong SSL certificates
- Regular security updates

### **C. Performance:**
- Consider CDN for static assets
- Implement caching strategies
- Monitor server resources

## 💰 **Cost Breakdown**

| Service | Cost | Purpose |
|---------|------|---------|
| **Domain** | $10-15/year | Professional domain name |
| **SSL Certificate** | Free (Let's Encrypt) | HTTPS security |
| **Cloudflare Tunnel** | Free | Bypass network restrictions |
| **Total** | **$10-15/year** | Complete domain setup |

## 🎉 **Benefits**

1. **Professional Appearance**: Custom domain looks more professional
2. **Global Access**: Accessible from anywhere in the world
3. **SEO Benefits**: Better search engine optimization
4. **Brand Recognition**: Easier to remember and share
5. **SSL Security**: Encrypted connections
6. **Scalability**: Easy to add subdomains and services

## 🚀 **Next Steps**

1. **Purchase domain from GoDaddy**
2. **Configure DNS settings**
3. **Update deployment scripts**
4. **Setup SSL certificate**
5. **Deploy with domain configuration**
6. **Test global access**

Your BrokeBuy application will then be accessible worldwide with a professional domain! 🌍
