# Contextual Synthesis Engine

The Contextual Synthesis Engine is the core differentiator of TiO. It moves the platform from a "Retrieval" system to a "Synthesis" system.

## 1. What is Contextual Synthesis?
Traditional RAG (Retrieval-Augmented Generation) systems often suffer from "Chunk Blindness" — they retrieve isolated snippets of text that lack the broader context of the website's structure or the user's intent.

**Synthesis** is the process of:
1. **Aggregating** raw chunks from multiple sources (HTML, PDF, External Search).
2. **Analyzing** those chunks for atomic facts, relationships, and workflows.
3. **Structuring** that analysis into a `ContextSnapshot`.
4. **Projecting** that snapshot through the lens of the user's active goal.

## 2. The Synthesis Pipeline

### Step 1: Multi-Pass Retrieval
- **Pass 1**: Semantic search based on the user's query.
- **Pass 2**: Workflow-boosted search. If a "Booking" goal is detected, retrieval is biased toward "Booking" tagged chunks.
- **Pass 3**: External search (via Tavily) if internal confidence is low.

### Step 2: Atomic Fact Extraction
The `Context Aggregator` processes the raw text to extract:
- **Facts**: "The ticket price is $50."
- **Workflows**: "1. Select date → 2. Add to cart → 3. Checkout."
- **Entities**: "Lourdes Museum", "Summer Pass".

### Step 3: Response Planning
Before generating the final answer, the Orchestrator creates a **Response Plan**:
- **Goal**: What is the user trying to do? (e.g., "Estimate trip cost").
- **Workflow**: Which site workflow applies? (e.g., "Pricing").
- **Reasoning**: "I will first find the base price, then add the peak season surcharge."

### Step 4: Proactive Projection
The final generation is not just an answer; it's a projection of the site's intelligence. It includes:
- **Direct Answer**: Grounded in the plan and facts.
- **Workflow Guidance**: "Since you're planning a trip, would you like to see the opening hours?"
- **Citations**: Linking directly to the source documents.

## 3. Why it Matters
Contextual Synthesis solves several common AI chatbot failures:
- **Hallucination Prevention**: By forcing a "Planning" turn, the LLM is less likely to guess.
- **Workflow Continuity**: The system remembers that you are in the "Admission" flow even if your next question is generic.
- **Non-Robotic Interaction**: By understanding the domain (e.g., Tourism), TiO can adopt a professional, domain-specific tone rather than a generic assistant persona.

## 4. Technical Implementation
- **Logic**: Located in `backend/utils/context_intelligence.py` and `backend/agents/orchestrator_agent.py`.
- **State**: Persisted in the `ConversationGoal` model (`backend/models/entities.py`).
- **Memory**: Compressed using the `Rolling Summary` service (`backend/memory/service.py`).
