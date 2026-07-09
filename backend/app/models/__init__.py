from app.models.base import Base
from app.models.user import User, UserOTP, UserRole, OTPPurpose
from app.models.subject import Subject, File, FileStatus, OCRStatus
from app.models.document import DocumentMetadata, OcrResult, DocumentChunk
from app.models.chat import Conversation, Message, MessageCitation, MessageSender
from app.models.quiz import Quiz, QuizQuestion, QuizUserAnswer, QuizDifficulty, QuizStatus, QuestionType
from app.models.flashcard import Flashcard
from app.models.study_plan import StudyPlan, StudySession
from app.models.notification import Notification, Feedback

__all__ = [
    "Base",
    "User",
    "UserOTP",
    "UserRole",
    "OTPPurpose",
    "Subject",
    "File",
    "FileStatus",
    "OCRStatus",
    "DocumentMetadata",
    "OcrResult",
    "DocumentChunk",
    "Conversation",
    "Message",
    "MessageCitation",
    "MessageSender",
    "Quiz",
    "QuizQuestion",
    "QuizUserAnswer",
    "QuizDifficulty",
    "QuizStatus",
    "QuestionType",
    "Flashcard",
    "StudyPlan",
    "StudySession",
    "Notification",
    "Feedback",
]
