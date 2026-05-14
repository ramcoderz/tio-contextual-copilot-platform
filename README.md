# TiO: Contextual Copilot Platform

**TiO** is a production-oriented Context-Aware Chatbot Builder that transforms websites and uploaded documents into grounded conversational copilots. It leverages advanced contextual retrieval, hybrid search, and workflow-aware conversational synthesis to provide high-fidelity assistance.

## 🚀 Overview

Unlike generic RAG chatbots, TiO is designed to **understand** the context of a website. It builds a persistent "Website Understanding Layer" during ingestion, allowing it to reason across multiple pages, identify core workflows, and provide proactive guidance tailored to the specific domain (Tourism, Education, Developer, etc.).

## ✨ Key Features

- **Recursive Contextual Crawling**: Deep-depth BFS crawler with Playwright support for JavaScript-rendered pages and intelligent asset discovery.
- **Hybrid Retrieval (RRF)**: Combines dense semantic vector search (FAISS/ChromaDB) with sparse keyword-based search (BM25) for maximum precision.
- **Cross-Encoder Reranking**: Second-stage scoring using state-of-the-art cross-encoders to ensure only the most relevant context is synthesized.
- **Contextual Synthesis Engine**: A pre-generation aggregation layer that builds a structured `ContextSnapshot` (Facts, Entities, Workflows) from retrieved chunks.
- **Workflow-Aware Reasoning**: Tracks user goals and active workflows (e.g., Booking, Integration, Troubleshooting) to provide process-oriented guidance.
- **Entity Grounding**: Strict entity extraction and "No-Placeholder" policy ensures all claims are grounded in actual site content.
- **Reasoning Transparency**: Real-time "Thought Traces" expose the AI's goal, logical plan, and reasoning steps to the user.
- **Multi-Format Export**: Export grounded research and conversation histories to PDF, Markdown, or Word (Docx).

## 🏗️ Architecture

TiO follows a layered intelligence architecture:

1.  **Ingestion Layer**: Recursive crawler -> Section-aware chunking -> Entity Extraction -> Site Profile Generation.
2.  **Retrieval Layer**: Intent Detection -> Query Expansion -> Hybrid Search -> RRF Fusion -> Reranking.
3.  **Intelligence Layer**: Context Aggregation -> Response Planning -> Synthesized Generation.
4.  **Security Layer**: Strict session isolation, user-level scoping, and administrative data purge utilities.

For a detailed breakdown, see [Architecture Documentation](docs/architecture.md).

## 🛠️ Technology Stack

- **Backend**: Python (FastAPI), SQLAlchemy, Pydantic.
- **LLM / Inference**: Ollama (Local), Tavily (External Fallback).
- **Vector Stores**: FAISS, ChromaDB.
- **NLP**: spaCy, SentenceTransformers, Rank-BM25.
- **Frontend**: React, Vite, Framer Motion, Tailwind CSS.

## 🏁 Local Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- [Ollama](https://ollama.ai/) installed and running locally.

### Backend Setup
1.  Clone the repository and navigate to the project root.
2.  Create a virtual environment: `python -m venv venv`
3.  Activate venv: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
4.  Install dependencies: `pip install -r requirements.txt`
5.  Initialize the database: `python main.py --init-db`
6.  Start the server: `python main.py`

### Frontend Setup
1.  Navigate to `frontend/`
2.  Install dependencies: `npm install`
3.  Start the dev server: `npm run dev`

### Environment Variables
Create a `.env` file in the project root based on `.env.example`:
- `OLLAMA_BASE_URL`: Defaults to `http://localhost:11434`
- `OLLAMA_MODEL`: Defaults to `llama3`
- `TAVILY_API_KEY`: Required for external research fallback.
- `OPENROUTER_API_KEY`: (Optional) Cloud fallback if Ollama is offline.

## ⚠️ Known Limitations
- Initial ingestion for large websites (>500 pages) may take several minutes.
- Performance is heavily dependent on local hardware when using Ollama.
- Entity extraction is currently optimized for English-language content.

## 🗺️ Roadmap
- Integration with more vector store providers (Pinecone, Weaviate).
- Support for complex document formats (Excel, Powerpoint).
- Advanced multi-agent collaboration for multi-domain support.

---
*Built with precision for grounded intelligence.*
