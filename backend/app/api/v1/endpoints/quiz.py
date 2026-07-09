from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User
from app.models.quiz import Quiz, QuizStatus
from app.schemas.quiz import QuizOut, QuizDetailOut, QuizSubmit, QuizResultOut, QuizGenerateRequest
from app.services.quiz import quiz_service

router = APIRouter()

@router.post("", response_model=QuizDetailOut, status_code=status.HTTP_201_CREATED)
def generate_new_quiz(
    payload: QuizGenerateRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Generate a quiz dynamically using AI based on selected files or subject.
    """
    try:
        db_quiz = quiz_service.generate_quiz(
            db=db,
            user_id=current_user.id,
            req=payload
        )
        return db_quiz
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate quiz: {str(e)}"
        )

@router.get("", response_model=List[QuizOut])
def list_quizzes(
    subject_id: Optional[int] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Lists all generated quizzes, optionally filtered by subject.
    """
    query = db.query(Quiz).filter(Quiz.user_id == current_user.id)
    if subject_id is not None:
        query = query.filter(Quiz.subject_id == subject_id)
    return query.order_by(Quiz.created_at.desc()).all()

@router.get("/{quiz_id}", response_model=QuizDetailOut)
def get_quiz_details(
    quiz_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Fetches the details and questions of a specific quiz.
    """
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id, Quiz.user_id == current_user.id).first()
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found or unauthorized."
        )
    return quiz

@router.post("/{quiz_id}/submit", response_model=QuizResultOut)
def submit_quiz_answers(
    quiz_id: int,
    payload: QuizSubmit,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Grade answers, calculate score, record user answers, and return results.
    """
    try:
        graded_quiz = quiz_service.grade_quiz(
            db=db,
            quiz_id=quiz_id,
            submission=payload,
            user_id=current_user.id
        )
        
        # Format custom result payload manually or let ORM fetch it
        # Map questions and their answers together
        results = []
        answers_map = {ans.question_id: ans for ans in graded_quiz.user_answers}
        for q in graded_quiz.questions:
            ans_record = answers_map.get(q.id)
            results.append({
                "id": q.id,
                "question_text": q.question_text,
                "question_type": q.question_type,
                "options": q.options,
                "correct_answer": q.correct_answer,
                "explanation": q.explanation,
                "user_answer": ans_record.user_answer if ans_record else "",
                "is_correct": ans_record.is_correct if ans_record else False,
                "points_awarded": ans_record.points_awarded if ans_record else 0,
                "feedback": ans_record.feedback if ans_record else "No answer submitted."
            })
            
        return {
            "id": graded_quiz.id,
            "title": graded_quiz.title,
            "difficulty": graded_quiz.difficulty,
            "score": graded_quiz.score,
            "max_score": graded_quiz.max_score,
            "time_taken": graded_quiz.time_taken,
            "status": graded_quiz.status,
            "subject_id": graded_quiz.subject_id,
            "created_at": graded_quiz.created_at,
            "results": results
        }
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to grade quiz submission: {str(e)}"
        )
