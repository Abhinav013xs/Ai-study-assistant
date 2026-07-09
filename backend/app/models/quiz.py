import enum
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum, Boolean, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin

class QuizDifficulty(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class QuizStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"

class QuestionType(str, enum.Enum):
    MCQ = "mcq"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"
    SHORT_ANSWER = "short_answer"
    LONG_ANSWER = "long_answer"

class Quiz(Base, TimestampMixin):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True)
    difficulty = Column(Enum(QuizDifficulty), default=QuizDifficulty.MEDIUM, nullable=False)
    score = Column(Integer, default=0, nullable=False)
    max_score = Column(Integer, default=0, nullable=False)
    time_taken = Column(Integer, nullable=True)  # in seconds
    status = Column(Enum(QuizStatus), default=QuizStatus.PENDING, nullable=False)

    # Relationships
    user = relationship("User", back_populates="quizzes")
    subject = relationship("Subject", back_populates="quizzes")
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")
    user_answers = relationship("QuizUserAnswer", back_populates="quiz", cascade="all, delete-orphan")

class QuizQuestion(Base, TimestampMixin):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(Enum(QuestionType), nullable=False)
    options = Column(JSON, nullable=True)  # List of strings for MCQs, None otherwise
    correct_answer = Column(Text, nullable=False)  # Exact answer, e.g. "A", "True", etc.
    explanation = Column(Text, nullable=True)

    # Relationships
    quiz = relationship("Quiz", back_populates="questions")
    user_answers = relationship("QuizUserAnswer", back_populates="question", cascade="all, delete-orphan")

class QuizUserAnswer(Base, TimestampMixin):
    __tablename__ = "quiz_user_answers"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False)
    user_answer = Column(Text, nullable=False)
    is_correct = Column(Boolean, nullable=True)  # Can be null if needs manual grading (long answer)
    points_awarded = Column(Integer, default=0, nullable=False)
    feedback = Column(Text, nullable=True)

    # Relationships
    quiz = relationship("Quiz", back_populates="user_answers")
    question = relationship("QuizQuestion", back_populates="user_answers")
