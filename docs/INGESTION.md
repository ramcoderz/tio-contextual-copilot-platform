# Crawler & Ingestion Pipeline Documentation

This document provides a technical breakdown of the TiO ingestion engine.

## 1. Overview
The TiO crawler is a recursive, BFS-based engine designed to discover and synthesize website content into a vector-searchable knowledge base.

## 2. Capabilities & Constraints

### Recursive BFS Traversal
- **Depth**: Defaults to a depth of **2** (homepage + 1 level of links). This prevents resource explosion while capturing the most relevant contextual pages.
- **Limit**: Capped at **20 pages** per chatbot by default to ensure fast ingestion and manage vector store costs.
- **Link Prioritization**: The crawler prioritizes internal links that appear to be informational (e.g., `/about`, `/services`, `/faq`) over transactional or noisy links (e.g., `/cart`, `/login`, `/tags`).

### JavaScript Support
- **Playwright Fallback**: TiO uses `httpx` for fast static parsing but automatically falls back to **Playwright** (headless Chromium) if it detects a JavaScript-heavy single-page application (SPA).

### Document Ingestion
- **Automatic Discovery**: The crawler scans for links ending in `.pdf`, `.docx`, `.txt`, and `.md`.
- **Parsing**: Discovered files are downloaded to a temporary buffer, parsed using specialized libraries (e.g., `PyPDF2`, `python-docx`), and chunked into the same vector space as the HTML content.

### Deduplication & Quality Filtering
- **URL Normalization**: URLs are normalized (removing fragments and query params) to prevent duplicate crawling of the same page.
- **Content Hashing**: A SHA-256 hash of the cleaned text is stored. If a new page's hash matches an existing one, it is skipped.
- **Noise Removal**: Boilerplate content (headers, footers, navbars) is stripped using `trafilatura` to ensure the vector store only contains high-signal information.

## 3. Site Intelligence Layer
During ingestion, the pipeline doesn't just store raw text. It performs a **Site Understanding Pass**:
1. **Domain Detection**: Classifies the site into a category (e.g., Tourism, Education).
2. **Entity Extraction**: Identifies key organizations, products, and locations.
3. **Relationship Mapping**: Detects connections between entities (e.g., "Museum X is located in City Y").
4. **Workflow Detection**: Identifies common user paths (e.g., "Booking a flight", "Applying for a visa").

## 4. Current Status

| Feature | Status |
| :--- | :--- |
| Recursive BFS (Depth 2) | ✅ Implemented |
| JavaScript Rendering | ✅ Implemented (Playwright) |
| PDF/DOCX Parsing | ✅ Implemented |
| External Link Discovery | ✅ Implemented (Selective) |
| Entity Extraction | ✅ Implemented |
| Relationship Mapping | ⚠️ Partial (Regex-based) |
| Workflow Detection | ⚠️ Partial (Heuristic-based) |
| Image/Video Parsing | ❌ Not Planned |

## 5. Improvement Roadmap
- **Entity Linking**: Moving from extraction to formal linking with Knowledge Bases (e.g., Wikidata).
- **Graph-Based Retrieval**: Moving from flat vector search to hybrid Graph+Vector retrieval for better relationship reasoning.
- **Visual Grounding**: Supporting OCR for images/diagrams within pages.
