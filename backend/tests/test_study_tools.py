import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.models.user import User, UserRole
from app.models.flashcard import Flashcard
from app.services.study_tools import study_tools_service

# Setup mock database session for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def mock_user(db_session):
    user = User(
        email="test_student@academy.com",
        hashed_password="hashed_pass_placeholder",
        full_name="Test Student",
        role=UserRole.STUDENT,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def mock_flashcard(db_session, mock_user):
    card = Flashcard(
        front="What is the time complexity of binary search?",
        back="O(log n) because the search space is halved at each step.",
        difficulty="easy",
        topic="Algorithms",
        user_id=mock_user.id
    )
    db_session.add(card)
    db_session.commit()
    db_session.refresh(card)
    return card

def test_sm2_spaced_repetition_success(db_session, mock_user, mock_flashcard):
    """
    Test SM-2 spaced repetition when the user remembers the card (rating = 5).
    Expects repetitions to increment and ease factor to increase.
    """
    initial_ef = mock_flashcard.ease_factor
    initial_reps = mock_flashcard.repetitions

    # Submit a perfect review (rating 5)
    updated_card = study_tools_service.review_flashcard_sm2(
        db=db_session,
        flashcard_id=mock_flashcard.id,
        rating=5,
        user_id=mock_user.id
    )

    assert updated_card.repetitions == initial_reps + 1
    assert updated_card.interval == 1
    assert updated_card.ease_factor > initial_ef
    assert updated_card.next_review > datetime.datetime.utcnow()

def test_sm2_spaced_repetition_forgot(db_session, mock_user, mock_flashcard):
    """
    Test SM-2 spaced repetition when the user forgets the card (rating = 1).
    Expects repetitions to reset to 0 and interval to go to 1 day.
    """
    # Simulate a card that was previously reviewed
    mock_flashcard.repetitions = 3
    mock_flashcard.interval = 12
    db_session.commit()

    # Submit a failed review (rating 1)
    updated_card = study_tools_service.review_flashcard_sm2(
        db=db_session,
        flashcard_id=mock_flashcard.id,
        rating=1,
        user_id=mock_user.id
    )

    assert updated_card.repetitions == 0
    assert updated_card.interval == 1
    assert updated_card.next_review > datetime.datetime.utcnow()
