from typing import List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.quiz import QuizDifficulty, QuizStatus, QuestionType

class QuizQuestionOut(BaseModel):
    id: int
    question_text: str
    question_type: QuestionType
    options: Optional[List[str]] = None

    class Config:
        from_attributes = True

class QuizOut(BaseModel):
    id: int
    title: str
    difficulty: QuizDifficulty
    score: int
    max_score: int
    time_taken: Optional[int] = None
    status: QuizStatus
    subject_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

class QuizDetailOut(QuizOut):
    questions: List[QuizQuestionOut] = []

    class Config:
        from_attributes = True

class UserAnswerSubmit(BaseModel):
    question_id: int
    user_answer: str

class QuizSubmit(BaseModel):
    time_taken: int  # in seconds
    answers: List[UserAnswerSubmit]

class QuizQuestionResultOut(BaseModel):
    id: int
    question_text: str
    question_type: QuestionType
    options: Optional[List[str]] = None
    correct_answer: str
    explanation: Optional[str] = None
    user_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    points_awarded: int
    feedback: Optional[str] = None

class QuizResultOut(QuizOut):
    results: List[QuizQuestionResultOut] = []
    
    class Config:
        from_attributes = True

class QuizGenerateRequest(BaseModel):
    title: str
    subject_id: Optional[int] = None
    file_ids: Optional[List[int]] = None
    difficulty: QuizDifficulty = QuizDifficulty.MEDIUM
    num_questions: int = Field(5, ge=1, le=20)
    question_types: List[QuestionType] = [QuestionType.MCQ]
