# LifePilot AI - Architecture Guide

This document outlines the high-level architecture decisions for **LifePilot AI** personal operating system.

## Clean Architecture Principles

The backend utilizes **Clean Architecture** patterns:

1. **Entities (Models)**: Core enterprise business objects (e.g., Task, Habit, Budget) located in `app/models/`. These are independent of external libraries.
2. **Use Cases (Services)**: Application-specific business rules in `app/services/`.
3. **Interface Adapters**:
   - **Routers**: Map endpoints (e.g., `/api/v1/tasks/`) to service methods, found in `app/api/`.
   - **Repositories**: Access and mutate database rows, insulating the core from SQL engines.
4. **Frameworks & Drivers**: FastAPI framework, SQLAlchemy ORM, Uvicorn server, Postgres Database, Redis Cache.

## Frontend Modular Design

The frontend implements a **Feature-based modular structure**:

- Components in `src/features/` are grouped by domain (e.g., `tasks`, `habits`, `analytics`).
- Each feature directory encapsulates:
  - Components specific to that feature (e.g., `TaskCard.tsx`).
  - Logic hooks (`useTaskMutation.ts`).
  - Types (`task.types.ts`).
  - Service functions (`taskService.ts`).
- Global widgets (e.g., Navbars, general buttons) reside in `src/components/` and `src/components/ui/`.
- Client-side states (via Zustand) reside in `src/store/`.
