# LifePilot AI - SaaS Monorepo Foundation

LifePilot AI is an AI-powered personal life operating system designed to unify task management, habits, expenses, analytics, and semantic knowledge retrieval (RAG) into a single, cohesive dashboard governed by personal intelligence.

This repository contains the **Phase 1: Project Foundation**, establishing a production-ready monorepo with high-quality Next.js (frontend) and FastAPI (backend) layers, linting tools, and containerized configurations.

---

## Architecture Overview

The LifePilot AI codebase is structured as a decoupled monorepo, keeping client-side logic and core API systems strictly isolated:

```
                  ┌───────────────────────┐
                  │   Next.js Frontend    │ (TypeScript, Tailwind, shadcn/ui)
                  │   (Port: 3000)        │
                  └──────────┬────────────┘
                             │ (REST API)
                             ▼
                  ┌───────────────────────┐
                  │   FastAPI Backend     │ (Python 3.12+, Uvicorn)
                  │   (Port: 8000)        │
                  └──────┬──────────┬─────┘
                         │          │
            ┌────────────▼───┐  ┌───▼────────────┐
            │   PostgreSQL   │  │     Redis      │ (Data & Cache Isolation)
            │   (Port: 5432) │  │  (Port: 6379)  │
            └────────────────┘  └────────────────┘
```

---

## Directory Structure

```
lifepilot-ai/
├── .github/                  # CI configuration
│   └── workflows/
│       └── lint.yml          # GitHub Actions check (linter & formatters)
├── backend/                  # Python API Service
│   ├── app/
│   │   ├── api/              # API router and controllers
│   │   ├── core/             # Base security, auth, database, exceptions
│   │   ├── config/           # Pydantic Settings management
│   │   ├── models/           # SQLAlchemy DB models (future)
│   │   ├── schemas/          # Pydantic validation schemas
│   │   ├── repositories/     # Database access pattern (future)
│   │   ├── services/         # Business logic layer (future)
│   │   ├── middleware/       # CORS, logs, custom middleware
│   │   ├── utils/            # Shared helper functions
│   │   └── main.py           # FastAPI entry point
│   ├── tests/                # Pytest suite
│   ├── Dockerfile            # Multi-stage Python runner
│   └── pyproject.toml        # Poetry packaging and tools (Black, Ruff, isort)
├── frontend/                 # Next.js Application
│   ├── src/
│   │   ├── app/              # Next.js App Router (pages & layout)
│   │   ├── components/       # Shared presentation UI components
│   │   │   └── ui/           # shadcn/ui components (button, etc.)
│   │   ├── features/         # Feature-based logic scopes (tasks, habits, etc.)
│   │   ├── hooks/            # Custom React hooks
│   │   ├── lib/              # Utility instances (axios, utils, shadcn helper)
│   │   ├── services/         # API abstraction layers
│   │   ├── store/            # Client state store (Zustand)
│   │   ├── types/            # TypeScript schemas and types
│   │   └── styles/           # Global styles and Tailwind imports
│   ├── Dockerfile            # Multi-stage standalone Node runner
│   ├── eslint.config.mjs     # ESLint rules configuration
│   ├── tsconfig.json         # TypeScript configuration
│   ├── next.config.ts        # Next.js config (standalone enabled)
│   └── package.json          # Node scripts and dependencies
├── docs/                     # Architectural documents & guides
├── scripts/                  # Automation scripts
├── .editorconfig             # IDE spacing rules
├── .env.example              # Environment template
├── .gitignore                # Global git ignoring configs
├── docker-compose.yml        # Multi-container conductor
├── LICENSE                   # MIT License
└── README.md                 # This file
```

---

## Getting Started

### Prerequisites
Make sure you have the following installed on your machine:
- **Node.js** v20+ and **npm** v10+
- **Python** v3.12+
- **Docker** and **Docker Compose**

### Setup Environment
1. Copy the `.env.example` file to create your local environment:
   ```bash
   cp .env.example .env
   ```
2. Adjust the variables inside `.env` as needed (defaults are preconfigured for local dev).

---

## Docker Commands (Easiest Method)

To launch the entire stack (Next.js, FastAPI, PostgreSQL, Redis) with health checks in isolated containers:

```bash
# Build and start all containers in background
docker compose up -d --build

# Verify container statuses and health
docker compose ps

# View execution logs of all containers
docker compose logs -f

# Stop and tear down containers
docker compose down
```

Once running:
- **Frontend App**: [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://localhost:8000](http://localhost:8000) (Docs at `/docs`)

---

## Development Commands (Local Execution)

If running services directly on your host machine for development:

### Backend Development
Navigate to the `backend` directory:
```bash
cd backend

# Install dependencies (requires Poetry)
poetry install

# Run backend test suite
poetry run pytest

# Run linters and formatters
poetry run black . --check
poetry run isort . --check
poetry run ruff check .

# Start the development server (reload enabled)
poetry run uvicorn app.main:app --reload --port 8000
```

### Frontend Development
Navigate to the `frontend` directory:
```bash
cd frontend

# Install dependencies
npm install

# Run linters and Prettier rules
npm run lint

# Start the local development server
npm run dev -- -p 3000
```

---

## Future Roadmap

- **Phase 2 (Database & Cache)**: Establish SQLAlchemy 2.0 ORM with PostgreSQL and configure Redis for background task caching.
- **Phase 3 (Authentication & Core Logic)**: Implement JWT authentication, user registration, and schema validations.
- **Phase 4 (Feature Implementations)**: Implement CRUD endpoints for Task management, Habits tracking, and Finances logs.
- **Phase 5 (AI Integration & RAG)**: Integrate LangChain/LlamaIndex, OpenAI/Gemini APIs, and vector databases for personal context chat.
