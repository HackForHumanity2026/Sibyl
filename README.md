# Sibyl

A multi-agent AI orchestration system for sustainability report verification and IFRS S1/S2 compliance analysis.

## Overview

Sibyl ingests sustainability report PDFs, extracts verifiable claims, dispatches specialized investigation agents to gather evidence from diverse real-world sources, and produces a paragraph-level IFRS S1/S2 compliance mapping.

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy 2.1, PostgreSQL 17 + pgvector, Redis, LangGraph
- **Frontend:** React + Vite + TypeScript, shadcn/ui, TailwindCSS v4
- **AI:** OpenRouter (Claude, Gemini, DeepSeek), LangChain

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- OpenRouter API key

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd sibyl
   ```

2. Copy the environment file and add your API key:
   ```bash
   cp .env.example .env
   # Edit .env and set OPENROUTER_API_KEY
   ```

3. Start all services:
   ```bash
   docker-compose up
   ```

### Service URLs

| Service   | URL                          |
|-----------|------------------------------|
| Frontend  | http://localhost:5174        |
| Backend   | http://localhost:8000        |
| API Docs  | http://localhost:8000/docs   |
| PostgreSQL| localhost:5434               |
| Redis     | localhost:6379               |

> Note: PostgreSQL uses port 5434 and frontend uses port 5174 to avoid conflicts with local services.

## Project Structure

```
sibyl/
├── backend/           # FastAPI application
│   ├── app/
│   │   ├── agents/    # LangGraph agent implementations
│   │   ├── api/       # REST API routes
│   │   ├── core/      # Configuration and database
│   │   ├── models/    # SQLAlchemy ORM models
│   │   ├── schemas/   # Pydantic request/response schemas
│   │   └── services/  # Business logic services
│   ├── alembic/       # Database migrations
│   └── data/          # IFRS/SASB standard texts
├── frontend/          # React application
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── services/
│       └── types/
├── docker-compose.yml
└── .env.example
```

## Development

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## License

This project was created for Hack for Humanity 2026.
