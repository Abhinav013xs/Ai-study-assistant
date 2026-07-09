import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User
from app.models.flashcard import Flashcard
from app.schemas.flashcard import FlashcardCreate, FlashcardOut, FlashcardReview
from app.services.study_tools import study_tools_service

router = APIRouter()

@router.post("/notes", status_code=status.HTTP_200_OK)
def generate_study_notes(
    file_ids: List[int],
    note_type: str = "detailed",
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Generates study notes of a given format (detailed, bullet, mindmap, formula, definitions)
    from a list of uploaded materials. Returns structured markdown text.
    """
    if not file_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide at least one file ID for note generation."
        )
    
    # Generate notes using LLM
    try:
        notes_markdown = study_tools_service.generate_smart_notes(
            db=db,
            user_id=current_user.id,
            file_ids=file_ids,
            note_type=note_type
        )
        return {"notes": notes_markdown, "format": "markdown"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate study notes: {str(e)}"
        )

@router.post("/flashcards/generate", response_model=List[FlashcardOut], status_code=status.HTTP_201_CREATED)
def generate_flashcards(
    file_id: int,
    num_cards: int = Query(5, ge=1, le=15),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Automatically creates flashcards (Q/A pairs) from the content of an uploaded material.
    """
    try:
        cards = study_tools_service.generate_flashcards(
            db=db,
            user_id=current_user.id,
            file_id=file_id,
            num_cards=num_cards
        )
        return cards
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate flashcards: {str(e)}"
        )

@router.get("/flashcards", response_model=List[FlashcardOut])
def list_flashcards(
    subject_id: Optional[int] = None,
    due_only: bool = False,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Lists flashcards. Supports filtering by subject and retrieving 'due_only' cards
    which require review according to the SM-2 spaced repetition schedule.
    """
    query = db.query(Flashcard).filter(Flashcard.user_id == current_user.id)
    if subject_id is not None:
        query = query.filter(Flashcard.subject_id == subject_id)
    if due_only:
        query = query.filter(Flashcard.next_review <= datetime.datetime.utcnow())
    return query.all()

@router.post("/flashcards/{flashcard_id}/review", response_model=FlashcardOut)
def review_flashcard(
    flashcard_id: int,
    payload: FlashcardReview,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Submits a review grade (0 to 5) for a flashcard.
    Applies the SuperMemo-2 algorithm to compute the next review session interval.
    """
    try:
        updated_card = study_tools_service.review_flashcard_sm2(
            db=db,
            flashcard_id=flashcard_id,
            rating=payload.rating,
            user_id=current_user.id
        )
        return updated_card
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process review: {str(e)}"
        )

@router.delete("/flashcards", status_code=status.HTTP_200_OK)
def clear_flashcards(
    subject_id: Optional[int] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Clears all flashcards or flashcards for a specific subject.
    """
    query = db.query(Flashcard).filter(Flashcard.user_id == current_user.id)
    if subject_id is not None:
        query = query.filter(Flashcard.subject_id == subject_id)
    
    deleted_count = query.delete(synchronize_session=False)
    db.commit()
    return {"status": "success", "message": f"Successfully deleted {deleted_count} flashcards."}

@router.delete("/flashcards/{flashcard_id}", status_code=status.HTTP_200_OK)
def delete_flashcard(
    flashcard_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Deletes a flashcard from the user's database.
    """
    card = db.query(Flashcard).filter(Flashcard.id == flashcard_id, Flashcard.user_id == current_user.id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flashcard not found or access denied."
        )
    db.delete(card)
    db.commit()
    return {"status": "success", "message": "Flashcard deleted successfully."}


