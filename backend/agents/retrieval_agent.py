from backend.vectorstore.service import async_retrieve

async def retrieve_context(query: str, chatbot_id: int):
    return await async_retrieve(query, top_k=5, chatbot_id=chatbot_id)
