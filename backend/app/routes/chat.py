"""Bilingual RAG Chat Assistant endpoints."""

from fastapi import APIRouter
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse
from app.rag.answer_generator import AnswerGenerator

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatMessageResponse)
async def chat_message(req: ChatMessageRequest):
    """
    Bilingual RAG Chatbot.
    Answers in Tamil or English grounded strictly in retrieved official scheme documents.
    """
    return await AnswerGenerator.generate_answer(req)

