# Technical Architecture

This document outlines the internal architecture of the TiO Contextual Copilot Platform.

## 1. Data Ingestion Pipeline

The ingestion pipeline transforms raw website data and documents into a searchable, structured "Understanding Layer."

### A. Recursive Crawling
- **Engines**: Uses `Trafilatura` for high-speed extraction and `Playwright` for complex JavaScript-rendered pages.
- **Traversal**: BFS (Breadth-First Search) with configurable depth and page limits.
- **Asset Discovery**: Automatically identifies linked PDFs, Docx, and Txt files for ingestion.

### B. Processing & Understanding
- **Chunking**: Implements section-aware chunking to preserve semantic headers and context.
- **Entity Extraction**: Uses `spaCy` NER to extract people, organizations, locations, and products.
- **Site Profiling**: Generates a persistent site summary and maps out core workflows using LLM-assisted analysis of the aggregated content.

---

## 2. Retrieval & Ranking Strategy

TiO uses a multi-stage retrieval process to ensure responses are grounded in the most relevant context.

### A. Intent & Expansion
- **Intent Detection**: Lightweight keyword and semantic analysis to categorize the query (e.g., General Chat, Search, Admin).
- **Query Expansion**: Uses LLMs to generate variations of the user query to bridge vocabulary gaps (e.g., "how to join" -> "admission process").

### B. Hybrid Search (RRF)
- **Dense Search**: Semantic similarity using `BAAI/bge-small-en-v1.5` embeddings stored in FAISS or ChromaDB.
- **Sparse Search**: Keyword matching using BM25 algorithms.
- **Fusion**: Reciprocal Rank Fusion (RRF) combines these scores to identify candidates that appear in both search results.

### C. Cross-Encoder Reranking
- Candidate chunks are re-scored using a Cross-Encoder model (`ms-marco-MiniLM-L-6-v2`) which evaluates the direct relevance of the chunk to the original query.

---

## 3. Intelligence & Synthesis Layer

The synthesis layer is what separates TiO from standard RAG systems.

### A. Context Aggregation
Before generation, the system synthesizes a **Context Snapshot**:
- **Facts**: A deduplicated list of atomic facts extracted from all retrieved chunks.
- **Workflows**: Identification of specific "how-to" processes mentioned.
- **Relationships**: A map of connections (e.g., "The API belongs to the Enterprise SDK").

### B. Response Planning
The Orchestrator agent performs a planning turn:
- **Goal**: What is the user specifically asking for?
- **Workflow**: Which site process is being engaged?
- **Plan**: A step-by-step logical outline for the response.

### C. Grounded Generation
- The final response is generated using the Planning and Snapshot context.
- **Strict Hallucination Control**: A post-processing layer checks for bracketed placeholders or robotic filler phrases and strips them before the user sees the output.

---

## 4. Security & Multi-Tenancy

- **Isolation**: All data is scoped by `chatbot_id` and `user_id` at the database and vector store levels.
- **Session Persistence**: User goals and workflow stages are persisted in the database to maintain continuity across sessions.
- **Data Governance**: Centralized utilities for purging all chatbot-related data (Files, DB, Vectors) upon deletion.

---
*Architecture version: 2.1.0 (Production-Ready)*
