# Multi-Agent System using LangGraph

A production-ready, general-purpose multi-agent system using LangGraph for orchestration, Redis for state management, Celery for asynchronous tasks, and FastAPI for the backend.

![Architecture Overview](https://img.shields.io/badge/Architecture-Event%20Driven-blue) ![Python](https://img.shields.io/badge/Python-3.11+-green) ![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-teal)

## Overview

This system allows **collaborative AI agents** to work together to solve complex tasks. Unlike simple chatbots, this framework orchestrates specialized agents—a **Research Agent** that gathers information and a **Writing Agent** that synthesizes it—to produce high-quality, comprehensive outputs for **any** user request.

**Key Capabilities:**
- **Dynamic Research**: Automatically identifies research topics from your prompt (e.g., "Compare X vs Y", "How to install Z").
- **Adaptive Writing**: intelligent template selection for Comparisons, Tutorials, Analyses, and Summaries.
- **Human-in-the-Loop**: Inspect and approve drafts before they are finalized.
- **Production Architecture**: Scalable, async design with persistent state and real-time updates.

## Architecture

![System Architecture](assets/System%20Architecture.png)

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed diagrams and component breakdown.

## Quick Start

### Prerequisites
- Docker & Docker Compose
- API Key for Groq or OpenAI

### 1. Configure Environment
Copy the example file and add your API key:
```bash
cp .env.example .env
# Edit .env:
# LLM_API_KEY=your_key_here
```

### 2. Start Services
Launch the entire stack (API, DB, Redis, Worker):
```bash
docker-compose up -d
```

### 3. Create a Task
The system handles natural language prompts automatically:

**Comparison Task:**
```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Compare Redis vs PostgreSQL for caching"}'
```

**Tutorial Task:**
```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a beginner tutorial for Docker setup"}'
```

**Analysis Task:**
```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Analyze microservices vs monolithic architecture"}'
```

### 4. Monitor & Approve
Check task status and approve the draft:
```bash
# Get Status
curl http://localhost:8000/api/v1/tasks/{task_id}

# Approve
curl -X POST http://localhost:8000/api/v1/tasks/{task_id}/approve \
  -H "Content-Type: application/json" \
  -d '{"approved": true}'
```

## Technology Stack

| Component | Technology | Role |
|-----------|------------|------|
| **Orchestration** | **LangGraph** | Manages agent state and workflow structure |
| **API** | **FastAPI** | Async REST endpoints & WebSockets |
| **Queue** | **Celery** | Asynchronous task processing |
| **Database** | **PostgreSQL** | Persistent storage for tasks and results |
| **State/Cache** | **Redis** | High-speed agent workspace & broker |
| **LLM** | **LangChain** | LLM abstraction (OpenAI / Groq) |

## Testing

Run the end-to-end test suite to verify system health:

```bash
docker-compose exec api pytest tests/test_e2e.py -v
```

## License

MIT License.