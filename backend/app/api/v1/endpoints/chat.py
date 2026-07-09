import json
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User
from app.models.chat import Conversation, Message, MessageCitation, MessageSender
from app.schemas.chat import ConversationCreate, ConversationOut, MessageOut, ChatQuery
from app.services.rag import rag_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/conversations", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: ConversationCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Creates a new conversation thread, optionally tied to a specific subject.
    """
    db_conversation = Conversation(
        title=payload.title,
        subject_id=payload.subject_id,
        user_id=current_user.id
    )
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation

@router.get("/conversations", response_model=List[ConversationOut])
def list_conversations(
    subject_id: Optional[int] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Lists all conversations of the user, optionally filtered by subject.
    """
    query = db.query(Conversation).filter(Conversation.user_id == current_user.id)
    if subject_id is not None:
        query = query.filter(Conversation.subject_id == subject_id)
    return query.order_by(Conversation.updated_at.desc()).all()

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageOut])
def get_message_history(
    conversation_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Fetches all message history and citations within a conversation.
    """
    conv = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id).first()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation thread not found or access denied."
        )
    return conv.messages

@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_200_OK)
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Deletes a conversation thread and all its message history.
    """
    conv = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id).first()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation thread not found or access denied."
        )
    db.delete(conv)
    db.commit()
    return {"status": "success", "message": "Conversation deleted successfully."}

@router.post("/conversations/{conversation_id}/query", response_model=MessageOut)
def query_rag_chat(
    conversation_id: int,
    payload: ChatQuery,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Submit a chat query. Runs RAG retrieval, invokes LLM, commits user/assistant responses,
    links citations, and returns the response message.
    """
    conv = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id).first()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation thread not found."
        )

    # 1. Fetch history
    history = []
    for msg in conv.messages[-10:]:  # Last 10 messages for context
        history.append({
            "role": "user" if msg.sender == MessageSender.USER else "assistant",
            "content": msg.content
        })

    # 2. Execute RAG pipeline
    answer, citations = rag_service.answer_query(
        db=db,
        query=payload.message,
        user_id=current_user.id,
        conversation_history=history,
        subject_id=conv.subject_id,
        file_ids=payload.file_ids,
        restrict_to_materials=payload.restrict_to_materials
    )

    # 3. Save User message to DB
    user_msg = Message(
        conversation_id=conversation_id,
        sender=MessageSender.USER,
        content=payload.message
    )
    db.add(user_msg)

    # 4. Save Assistant message to DB
    assistant_msg = Message(
        conversation_id=conversation_id,
        sender=MessageSender.ASSISTANT,
        content=answer
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    # 5. Save citations linked to Assistant message
    for cit in citations:
        db_cit = MessageCitation(
            message_id=assistant_msg.id,
            file_id=cit["file_id"],
            page_number=cit["page_number"],
            snippet=cit["snippet"]
        )
        db.add(db_cit)
    db.commit()
    db.refresh(assistant_msg)

    return assistant_msg

@router.get("/conversations/{conversation_id}/query/stream")
def stream_rag_chat(
    conversation_id: int,
    message: str,
    restrict_to_materials: bool = True,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Streams the RAG response via Server-Sent Events (SSE).
    """
    conv = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id).first()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation thread not found."
        )

    # Fetch context history
    history = []
    for msg in conv.messages[-6:]:
        history.append({
            "role": "user" if msg.sender == MessageSender.USER else "assistant",
            "content": msg.content
        })

    def sse_generator():
        # Get stream generator and citations
        stream, citations = rag_service.stream_answer_query(
            db=db,
            query=message,
            user_id=current_user.id,
            conversation_history=history,
            subject_id=conv.subject_id,
            restrict_to_materials=restrict_to_materials
        )

        full_response = []
        
        # 1. Stream the citations first
        citations_payload = {"type": "citations", "citations": citations}
        yield f"data: {json.dumps(citations_payload)}\n\n"

        # 2. Stream response content
        for chunk in stream:
            full_response.append(chunk)
            chunk_payload = {"type": "content", "content": chunk}
            yield f"data: {json.dumps(chunk_payload)}\n\n"

        # 3. Save conversation updates to database once streaming completes
        db_session = deps.SessionLocal()
        try:
            # Re-fetch records inside generator thread
            user_msg = Message(
                conversation_id=conversation_id,
                sender=MessageSender.USER,
                content=message
            )
            db_session.add(user_msg)

            assistant_msg = Message(
                conversation_id=conversation_id,
                sender=MessageSender.ASSISTANT,
                content="".join(full_response)
            )
            db_session.add(assistant_msg)
            db_session.commit()

            for cit in citations:
                db_cit = MessageCitation(
                    message_id=assistant_msg.id,
                    file_id=cit["file_id"],
                    page_number=cit["page_number"],
                    snippet=cit["snippet"]
                )
                db_session.add(db_cit)
            db_session.commit()
        except Exception as e:
            logger.error(f"Failed to save streaming conversation messages: {str(e)}")
            db_session.rollback()
        finally:
            db_session.close()

        yield "data: [DONE]\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")
