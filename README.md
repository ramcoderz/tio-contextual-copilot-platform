# TiO — Context-Aware Copilot Platform

**TiO** (Transformative Intelligence Orchestrator) is a professional-grade chatbot builder that transforms any website or set of documents into a context-aware AI copilot. Unlike basic RAG systems, TiO uses a **Contextual Synthesis Engine** to understand workflows, detect entities, and maintain conversation continuity.

![Platform Screenshot](https://raw.githubusercontent.com/ramcoderz/tio-contextual-copilot-platform/main/public/assets/dashboard_preview.png)

## 🚀 Key Features

- **Contextual Synthesis**: Moves beyond simple retrieval to synthesize raw data into facts, relationships, and workflows.
- **Workflow-Aware Retrieval**: Prioritizes information based on the user's active goal (e.g., booking, troubleshooting, planning).
- **Proactive Intelligence**: Detects user intent and suggests relevant next steps or domain-specific skills.
- **Hybrid Domain Routing**: Automatically classifies websites into domains (Tourism, Education, Medical, etc.) and applies specialized behavior profiles.
- **Premium UI/UX**: A sleek, dark-mode focused React dashboard and embeddable chat widget.
- **Strict Isolation**: Multi-tenant architecture ensuring session and chatbot data are never leaked.

## 🏗️ Architecture

TiO is built on a modern, scalable stack:

- **Frontend**: React 18, Vite, TailwindCSS, Framer Motion, Zustand.
- **Backend**: FastAPI (Python 3.10+), SQLAlchemy (Async), PostgreSQL/SQLite.
- **AI Intelligence**: Ollama (Llama 3/Mistral), Tavily Search (Fallback), Custom Site Intelligence Layer.
- **Vector Engine**: FAISS / ChromaDB with section-aware chunking.

## 🛠️ Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- [Ollama](https://ollama.ai/) (for local LLM inference)

### Backend Setup

1. Navigate to the `backend` directory.
2. Create a virtual environment: `python -m venv venv`
3. Install dependencies: `pip install -r requirements.txt`
4. Set up your `.env` file (see `.env.example`).
5. Run migrations: `python -m backend.db.migrate`
6. Start the server: `uvicorn backend.main:app --reload`

### Frontend Setup

1. Navigate to the `frontend` directory.
2. Install dependencies: `npm install`
3. Start the dev server: `npm run dev`
4. Access the dashboard at `http://localhost:5173`

## 📖 Documentation

- [Architecture Overview](docs/ARCHITECTURE.md)
- [Contextual Synthesis Engine](docs/CONTEXTUAL_SYNTHESIS.md)
- [Crawler & Ingestion Pipeline](docs/INGESTION.md)

## 🛡️ Security

TiO implements strict per-user and per-chatbot scoping. All retrieval queries are filtered by `chatbot_id` at the vector store level, and sessions are isolated using JWT-based authentication.

## 📄 License

MIT License. See `LICENSE` for details.

---

Built with ⚡ by [Ram](https://github.com/ramcoderz)
