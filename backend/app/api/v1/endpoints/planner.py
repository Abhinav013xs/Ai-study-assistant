import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User
from app.models.study_plan import StudyPlan, StudySession
from app.schemas.study_plan import StudyPlanCreate, StudyPlanOut, StudySessionCreate, StudySessionEnd, StudySessionOut
from app.services.planner import study_planner_service

router = APIRouter()

@router.post("", response_model=StudyPlanOut, status_code=status.HTTP_201_CREATED)
def create_study_plan(
    payload: StudyPlanCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Creates an adaptive day-by-day study schedule plan based on subjects, goals, and weaknesses.
    """
    try:
        plan = study_planner_service.generate_adaptive_plan(
            db=db,
            user_id=current_user.id,
            req=payload
        )
        return plan
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate planner schedule: {str(e)}"
        )

@router.get("", response_model=Optional[StudyPlanOut])
def get_active_study_plan(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Retrieves the most recently generated study plan for the authenticated user.
    """
    plan = (
        db.query(StudyPlan)
        .filter(StudyPlan.user_id == current_user.id)
        .order_by(StudyPlan.created_at.desc())
        .first()
    )
    return plan

@router.post("/sessions/start", response_model=StudySessionOut, status_code=status.HTTP_201_CREATED)
def start_study_session(
    payload: StudySessionCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Initiates a new study session clock timer for tracking metrics.
    """
    session = StudySession(
        user_id=current_user.id,
        subject_id=payload.subject_id,
        start_time=payload.start_time,
        notes=payload.notes,
        duration_seconds=0
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@router.post("/sessions/{session_id}/end", response_model=StudySessionOut)
def end_study_session(
    session_id: int,
    payload: StudySessionEnd,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Stops a study session clock, saves end time, calculates final duration in seconds,
    and updates session notes.
    """
    session = db.query(StudySession).filter(StudySession.id == session_id, StudySession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active study session not found."
        )

    session.end_time = payload.end_time
    
    # Calculate duration (removing timezone offsets to avoid TypeError on naive/aware subtraction)
    start_naive = session.start_time.replace(tzinfo=None) if session.start_time.tzinfo else session.start_time
    end_naive = payload.end_time.replace(tzinfo=None) if payload.end_time.tzinfo else payload.end_time
    duration = (end_naive - start_naive).total_seconds()
    session.duration_seconds = max(0, int(duration))
    
    if payload.notes:
        session.notes = (session.notes + f"\nEnd Notes: {payload.notes}") if session.notes else payload.notes

    db.commit()
    db.refresh(session)
    return session

@router.get("/sessions", response_model=List[StudySessionOut])
def list_study_sessions(
    subject_id: Optional[int] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Lists logged study sessions of the user, optionally filtered by subject.
    """
    query = db.query(StudySession).filter(StudySession.user_id == current_user.id)
    if subject_id is not None:
        query = query.filter(StudySession.subject_id == subject_id)
    return query.order_by(StudySession.start_time.desc()).all()
