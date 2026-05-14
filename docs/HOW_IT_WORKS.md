# How It Works: The RAG Pipeline

This document provides a deep dive into the RAG (Retrieval-Augmented Generation) pipeline of TiO.

## 1. Search Logic (Intent Detection)
When a user sends a message, the system first determines the **Intent**:
- **General Chat**: Informal conversation.
- **Search**: In-depth retrieval from the website content.
- **Admin**: Bot management tasks.

## 2. Hybrid Retrieval
TiO doesn't just look for keywords; it looks for **meaning**.
1.  **Vector Search**: Finds chunks that are semantically similar to the query.
2.  **BM25 Search**: Finds chunks with exact keyword matches.
3.  **RRF Fusion**: Combines both to get the "Best of both worlds."

## 3. The Understanding Layer
During ingestion, the bot doesn't just save text; it **builds a profile** of the site:
- What is this site about?
- What are the key services?
- What workflows exist (e.g., "How to apply")?

## 4. Conversational Synthesis
Instead of just quoting a chunk of text, the assistant **synthesizes** an answer:
- It looks at all retrieved chunks.
- It identifies common facts.
- It plans a response based on the detected user goal.
- It generates a natural, conversational response that is strictly grounded in the source material.

---
*Built for grounded, intelligent site awareness.*
