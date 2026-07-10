# LifePilot AI - Production Deployment & Operations Guide

This guide details the deployment options, environment configurations, CI/CD integrations, monitoring metrics, troubleshooting checklists, and rollback operations for both Backend and Frontend components of LifePilot AI.

---

## 1. Local Deployment (Bare Metal)

### Backend (FastAPI)
1. Navigate to the `backend` folder:
   ```bash
   cd backend
   ```
2. Install Python 3.12+ and Poetry, then build the virtual environment:
   ```bash
   poetry install
   ```
3. Set up a local database (PostgreSQL) and cache (Redis).
4. Create your local configuration file `.env` by copying `.env.example`:
   ```bash
   cp .env.example .env
   ```
5. Run database migrations:
   ```bash
   poetry run alembic upgrade head
   ```
6. Start the local development server:
   ```bash
   poetry run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

### Frontend (Next.js)
1. Navigate to the `frontend` folder:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Configure the backend connection URI in `.env.local`:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```
4. Start the local server:
   ```bash
   npm run dev
   ```
5. Access the user interface at `http://localhost:3000`.

---

## 2. Docker & Container Deployment

### Local Multi-Container Run (Docker Compose)
Docker Compose spins up Postgres, Redis, the backend web server, and the Next.js frontend with automated schema migration syncs and readiness health check loops.

1. Ensure Docker and Docker Compose are installed on your host.
2. Configure environment credentials in `.env` (copy from `.env.example`).
3. Run the orchestration:
   ```bash
   docker compose up --build -d
   ```
4. Verify the container status:
   ```bash
   docker compose ps
   ```
5. To stop and clean up containers:
   ```bash
   docker compose down -v
   ```

---

## 3. Render Deployment (Backend, Postgres, Redis)

Render is used for serverless cloud hosting of the FastAPI backend and databases. This repository includes a IaC `render.yaml` blueprint defining all resources.

### Automatic Blueprint Deployment
1. Connect your GitHub repository to Render (`https://dashboard.render.com`).
2. Select **Blueprints** from the top menu.
3. Click **New Blueprint Instance**.
4. Choose the repository and set the instance name. Render will automatically detect the `render.yaml` file and create:
   - **PostgreSQL Database** (`lifepilot-db`)
   - **Redis Cache** (`lifepilot-redis`)
   - **Web Service** (`lifepilot-backend`)
5. Provide a strong custom `SECRET_KEY` env var when prompted.
6. The blueprint automatically runs `alembic upgrade head` before Uvicorn starts to keep schemas synced with every commit!

---

## 4. Vercel Deployment (Frontend)

Vercel is optimized for static asset caching, edge networks, and serverless compilation of Next.js apps.

### Setup Instructions
1. Log into your Vercel Dashboard (`https://vercel.com`).
2. Click **Add New** -> **Project**.
3. Import your `lifepilot-ai` repository.
4. Set the **Root Directory** option to `frontend`.
5. Under **Framework Preset**, select **Next.js**.
6. Expand **Environment Variables** and define:
   - `NEXT_PUBLIC_API_URL`: Set this to your Render backend web service URL (e.g. `https://lifepilot-backend.onrender.com`).
7. Click **Deploy**. Vercel will build the standalone bundle and provide you with a production URL.

---

## 5. Security & Environment Validation

To prevent leaking credentials and verify configs, the following checks are implemented:
- **Production settings validation**: If `ENVIRONMENT` is set to `production`, starting the backend using weak default keys (e.g. `replace_me...`) or local connection addresses (`localhost`, `127.0.0.1`) will raise a validation crash on initialization.
- **Secret Masking**: Calling `settings.get_masked_settings()` filters passwords, keys, and connection strings into `********` to secure log files.
- **Strict CORS**: Wildcard origins (`*`) are disallowed in production mode.

---

## 6. Health & Monitoring

- **Health Check (`GET /health`)**: A lightweight endpoint that returns application version, overall status, and responsiveness checks of Postgres and Redis database sockets.
- **Readiness Check (`GET /ready`)**: Evaluates backend service initialization, including database state, redis state, local embedding model load, and vector database persistence connectivity.
- **Timing Middleware**: Every backend request is stamped with a unique `X-Request-ID` and outputs request logging with latency parameters (e.g., `5.34ms`) to logs.

---

## 7. Troubleshooting, Diagnostics & Rollback

### Common Diagnostic Commands
- **Check Docker Container Logs**:
  ```bash
  docker logs lifepilot-backend -f
  ```
- **Inspect Database Health Check Status**:
  ```bash
  docker inspect --format='{{json .State.Health}}' lifepilot-postgres
  ```
- **Connect directly to PostgreSQL inside Compose**:
  ```bash
  docker exec -it lifepilot-postgres psql -U lifepilot_user -d lifepilot_db
  ```

### Schema Rollbacks (Alembic)
If a database migration fails or needs to be reverted in production:
1. Revert to the last safe database version:
   ```bash
   poetry run alembic downgrade -1
   ```
2. Revert to a specific migration revision ID:
   ```bash
   poetry run alembic downgrade <revision_id>
   ```

### Application Deployment Rollbacks
- **Render**: Open the web service on Render dashboard, select **Events**, locate the last successful build, and select **Rollback to this deploy**.
- **Vercel**: Open the frontend project, navigate to **Deployments**, locate the last stable deployment, click the actions icon, and select **Promote to Production**.
