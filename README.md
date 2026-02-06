# Multi-Agent System Using LangGraph

[![CI/CD Pipeline](https://github.com/AkhileshMalthi/multi-agent-system-using-langgraph/actions/workflows/ci.yml/badge.svg)](https://github.com/AkhileshMalthi/multi-agent-system-using-langgraph/actions/workflows/ci.yml)

A scalable multi-agent orchestration system built with modern Python tools.

## 🚀 Tech Stack

- **Framework**: [LangGraph](https://github.com/langchain-ai/langgraph) - Agent orchestration with human-in-the-loop
- **API**: [FastAPI](https://fastapi.tiangolo.com/) - High-performance async web framework  
- **Task Queue**: [Celery](https://docs.celeryq.dev/) - Distributed task processing
- **Database**: PostgreSQL with SQLAlchemy & asyncpg
- **Cache/Broker**: Redis
- **LLM Providers**: Groq (default), OpenAI via LangChain
- **Package Manager**: [uv](https://github.com/astral-sh/uv) - Ultra-fast Python package installer

## 📁 Project Structure

```
.
├── src/
│   ├── api/          # FastAPI application
│   │   ├── main.py         # App entrypoint with WebSocket
│   │   ├── schemas.py      # Pydantic models
│   │   ├── websocket.py    # Real-time updates
│   │   └── routes/         # API endpoints
│   ├── agents/       # LangGraph workflow
│   │   ├── state.py        # Workflow state definition
│   │   ├── tools.py        # Search tools
│   │   ├── research_agent.py
│   │   ├── writing_agent.py
│   │   └── workflow.py     # LangGraph graph
│   ├── worker/       # Celery workers
│   │   └── celery_app.py   # Background tasks
│   ├── database/     # Database layer
│   │   ├── models.py       # SQLAlchemy models
│   │   ├── connection.py   # Async session
│   │   └── crud.py         # CRUD operations
│   └── shared/       # Shared utilities
│       ├── redis_client.py # Redis workspace
│       └── logger.py       # JSON structured logging
├── tests/            # Test suite
├── logs/             # Application logs
├── Dockerfile        # Multi-stage Docker build with uv
├── docker-compose.yml # Full stack orchestration
└── pyproject.toml    # Python dependencies and project metadata
```

## 🛠️ Development Setup

### Prerequisites
- Python 3.13+
- Docker & Docker Compose (for containerized setup)
- [uv](https://github.com/astral-sh/uv) package manager

### Local Development

```bash
# Install dependencies
uv sync --all-extras

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Run API server
uvicorn src.api.main:app --reload

# Run Celery worker (in another terminal)
celery -A src.worker.celery_app worker --loglevel=info
```

### Docker Setup

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

## 🔧 Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Key environment variables:
- `LLM_API_KEY` - Your OpenAI API key
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection for shared state
- `CELERY_BROKER_URL` - Redis URL for Celery

## 📚 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/tasks` | Create new task (202 Accepted) |
| GET | `/api/v1/tasks/{id}` | Get task status |
| POST | `/api/v1/tasks/{id}/approve` | Approve/reject task |
| WS | `/ws/tasks/{id}` | Real-time task updates |

Once running, visit:
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## 🔄 CI/CD Pipeline

The project uses GitHub Actions for continuous integration and deployment with 5 jobs:

1. **Lint** - Code quality checks with Ruff
2. **Unit Tests** - Fast unit/integration tests (excluding E2E)
3. **Docker Build** - Build and verify all services
4. **E2E Tests** - Full workflow tests with Docker
5. **Security Scan** - Dependency scanning with Safety and Bandit

**Setup CI secrets:**
- `GROQ_API_KEY` - Required for E2E tests

## 🧪 Testing

```bash
# Run unit tests only (fast, no Docker required)
uv run pytest -m "not e2e" -v

# Run with coverage
uv run pytest -m "not e2e" --cov=src

# Run E2E tests (requires Docker services running)
docker-compose up -d
uv run pytest tests/test_e2e.py -v

# Run all tests
uv run pytest tests/ -v
```

## 📝 License

See [LICENSE](LICENSE) file for details.