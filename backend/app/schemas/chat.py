from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.models.chat import MessageSender

# Citation schema
class MessageCitationOut(BaseModel):
    file_id: int
    file_name: str
    page_number: Optional[int] = None
    snippet: Optional[str] = None

    class Config:
        from_attributes = True

# Message schema
class MessageBase(BaseModel):
    content: str
    sender: MessageSender

class MessageCreate(MessageBase):
    pass

class MessageOut(MessageBase):
    id: int
    conversation_id: int
    audio_url: Optional[str] = None
    created_at: datetime
    citations: List[MessageCitationOut] = []

    class Config:
        from_attributes = True

# Conversation schema
class ConversationBase(BaseModel):
    title: str
    subject_id: Optional[int] = None

class ConversationCreate(ConversationBase):
    pass

class ConversationOut(ConversationBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Chat completion request
class ChatQuery(BaseModel):
    message: str
    stream: bool = False
    use_web_search: bool = False
    restrict_to_materials: bool = True
    file_ids: Optional[List[int]] = None
