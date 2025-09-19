# 🔧 SRM BrokeBuy - Backend

Welcome to the **SRM BrokeBuy Backend**, the robust API service powering the SRM campus marketplace. Built with FastAPI and MongoDB, it handles user authentication, listings, transactions, messaging, and more — serving as the heart of the platform.

Link to the frontend repo: https://github.com/Abishek0411/BrokeBuy-Frontend
---

## 🚀 Tech Stack

| Layer              | Stack                                   |
|--------------------|-----------------------------------------|
| Framework          | [FastAPI](https://fastapi.tiangolo.com/) 🐍 |
| Language           | Python 3.10+                            |
| Database           | MongoDB (Local/Atlas)                   |
| Auth               | JWT (OAuth2PasswordBearer)              |
| Cloud Storage      | Cloudinary (image upload/optimization)  |
| Image Validation   | Pydantic + Byte-level size check        |
| Environment Config | Python-dotenv                           |
| Containerization   | Docker + Docker Compose                 |
| Hosting/Dev        | Localhost + Docker                      |

---

## ⚡ Quick Start

### 1. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit with your credentials
nano .env
```

### 2. Development Mode
```bash
# Start all services
./optimized-dev-start.sh

# Stop all services
./optimized-dev-stop.sh
```

### 3. Docker Mode
```bash
# Production
docker-compose up -d

# Development
docker-compose -f docker-compose.dev.yml up -d
```

📖 **Detailed Setup**: See [ENVIRONMENT-SETUP.md](ENVIRONMENT-SETUP.md) for complete environment configuration.

---

## 📂 Project Structure

```

app/
├── main.py             # FastAPI app entrypoint
├── models/             # Pydantic models
├── routes/             # API routers (auth, listings, users, wallet, etc.)
├── utils/              # Auth, image upload, helper logic
├── database.py         # MongoDB connection setup
└── constants.py        # App constants (e.g. image size limits)

````

---

## 🔐 Authentication

- **SRM SSO Integration** (via academia scraper microservice)
- User login is done through SRM portal; token is stored in DB
- **JWT-based access token** is generated after successful SRM login
- Used via `Authorization: Bearer <token>` headers in frontend

---

## 🛍️ Core Features

### 🔑 Auth Routes (`/auth`)
- `POST /auth/login` — Login with SRM credentials
- `POST /auth/logout` — Invalidate session and remove SRM token

### 🧑‍🎓 Users (`/users`)
- `GET /users/me` — Get current logged-in user details
- `GET /users/{user_id}` — Public info for messaging

### 📦 Listings (`/listings`)
- `GET /listings/` — Get all unsold listings
- `GET /listings/recent` — Recent items sorted by creation date
- `GET /listings/my-listings` — Get listings posted by logged-in user
- `GET /listings/{id}` — View full listing details
- `POST /listings/create` — Create a new listing with image upload
- `PUT /listings/{id}` — Edit metadata and image set
- `PATCH /listings/{id}/toggle-status` — Mark active/inactive
- `DELETE /listings/{id}` — Delete your listing
- `POST /upload-image` — Compress + upload image to Cloudinary

### 💰 Wallet (`/wallet`)
- [Planned] — Internal wallet logic, virtual credits
- Admin-controlled top-up and redemption system

### 💬 Messaging (`/messages`)
- 1-on-1 chat between buyer & seller
- Real-time optional via future WebSocket integration

---

## 🖼️ Image Handling

- **Upload** via multipart `UploadFile[]`
- **Size validation**: 5MB max per image
- **Cloudinary** is used to store images
- **Optimized URLs** are generated and returned

---

## 🧪 Running Locally

### 🔧 Requirements

- Python 3.10+
- MongoDB Atlas URL (or local)
- Cloudinary account
- `.env` file with:

```env
MONGODB_URI=mongodb+srv://<user>:<pass>@cluster.mongodb.net/brokebuy
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
CLOUDINARY_CLOUD_NAME=your-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-secret
````

### 🛠️ Setup

```bash
# 1. Clone repo
git clone https://github.com/yourusername/srm-brokebuy-backend.git
cd srm-brokebuy-backend

# 2. Create and activate virtual env
python -m venv myenv
source myenv/bin/activate  # or .\myenv\Scripts\activate on Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start server
uvicorn app.main:app --reload
```

---

## 📬 Testing via Postman

* Use `POST /auth/login` with:

```json
{
  "account": "your-srm-email",
  "password": "your-password"
}
```

* Save the `access_token` from response
* For all protected routes, add:

```
Authorization: Bearer <access_token>
```

* For image uploads (create/edit), use `form-data` body with:

  * Fields: title, description, price, category, condition, location
  * Files: image\_0, image\_1... (up to 5)

---

## ⚠️ Error Handling & Logs

* JWT decoding & expiration exceptions handled cleanly
* `traceback.print_exc()` prints full server error logs
* 401, 403, 413, and 500 errors are consistently structured

---

## 🧠 Future Enhancements

* [ ] WebSocket-based messaging
* [ ] Razorpay checkout flow (MVP phase)
* [ ] Admin dashboard for listings + users
* [ ] Pagination and filters for large marketplaces
* [ ] Analytics for listing views, interests

---

## 👨‍💻 Contributors

* 👨‍💻 [Abishek Rajaram](https://github.com/abishekr03) — DevOps + Backend Lead
* ⚙️ Academia Scraper Microservice — powers SRM SSO login
* ☁️ Cloudinary — image hosting
* 🧠 ChatGPT — code assistant

---

## 📃 License

MIT License. © SRM BrokeBuy Team — Empowering Campus Commerce.
