import datetime
from fastapi import APIRouter, Depends, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User
from app.models.subject import File
from app.models.chat import Conversation
from app.models.quiz import Quiz, QuizStatus
from app.models.flashcard import Flashcard
from app.models.study_plan import StudySession

router = APIRouter()

def calculate_streak(sessions: list) -> int:
    """
    Calculate consecutive daily study streak.
    """
    if not sessions:
        return 0

    # Get unique study dates sorted descending
    study_dates = sorted(
        list({s.start_time.date() for s in sessions}),
        reverse=True
    )

    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)

    if study_dates[0] not in (today, yesterday):
        return 0

    streak = 1
    for idx in range(len(study_dates) - 1):
        diff = study_dates[idx] - study_dates[idx + 1]
        if diff.days == 1:
            streak += 1
        elif diff.days > 1:
            break  # Streak broken
    return streak

@router.get("", status_code=status.HTTP_200_OK)
def get_user_dashboard_analytics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Computes and aggregates analytics data for the student dashboard.
    """
    user_id = current_user.id

    # 1. Total Files Uploaded
    total_files = db.query(File).filter(File.user_id == user_id).count()

    # 2. Total AI Conversations
    total_convs = db.query(Conversation).filter(Conversation.user_id == user_id).count()

    # 3. Total Time Studied (seconds)
    total_study_seconds = (
        db.query(func.sum(StudySession.duration_seconds))
        .filter(StudySession.user_id == user_id)
        .scalar()
    ) or 0

    # 4. Streak Calculation
    all_sessions = (
        db.query(StudySession)
        .filter(StudySession.user_id == user_id)
        .order_by(StudySession.start_time.desc())
        .all()
    )
    streak = calculate_streak(all_sessions)

    # 5. Quiz Stats
    completed_quizzes = (
        db.query(Quiz)
        .filter(Quiz.user_id == user_id, Quiz.status == QuizStatus.COMPLETED)
        .all()
    )
    total_quizzes = len(completed_quizzes)
    average_quiz_score = 0.0
    if total_quizzes > 0:
        total_pct = sum([(q.score / q.max_score) * 100 if q.max_score > 0 else 0 for q in completed_quizzes])
        average_quiz_score = round(total_pct / total_quizzes, 1)

    # 6. Flashcards mastered (Ease factor >= 2.5 and repetitions >= 3)
    mastered_cards = (
        db.query(Flashcard)
        .filter(
            Flashcard.user_id == user_id,
            Flashcard.ease_factor >= 2.5,
            Flashcard.repetitions >= 3
        )
        .count()
    )
    total_cards = db.query(Flashcard).filter(Flashcard.user_id == user_id).count()

    # 7. Chart Progress Data (Daily, Weekly, Monthly)
    
    # 7a. Weekly Progress Chart Data (Last 7 days duration in minutes)
    weekly_chart = []
    today = datetime.date.today()
    for i in range(6, -1, -1):
        target_date = today - datetime.timedelta(days=i)
        day_seconds = (
            db.query(func.sum(StudySession.duration_seconds))
            .filter(
                StudySession.user_id == user_id,
                func.date(StudySession.start_time) == target_date
            )
            .scalar()
        ) or 0
        weekly_chart.append({
            "day": target_date.strftime("%a"),
            "date": target_date.strftime("%Y-%m-%d"),
            "minutes": round(day_seconds / 60.0, 1)
        })

    # 7b. Daily Progress Chart Data (Last 24 hours, grouped into 8 blocks of 3 hours)
    daily_chart = []
    now = datetime.datetime.utcnow()
    for i in range(7, -1, -1):
        block_start = now - datetime.timedelta(hours=(i+1)*3)
        block_end = now - datetime.timedelta(hours=i*3)
        block_seconds = (
            db.query(func.sum(StudySession.duration_seconds))
            .filter(
                StudySession.user_id == user_id,
                StudySession.start_time >= block_start,
                StudySession.start_time < block_end
            )
            .scalar()
        ) or 0
        daily_chart.append({
            "day": block_start.strftime("%H:%M"),
            "minutes": round(block_seconds / 60.0, 1)
        })

    # 7c. Monthly Progress Chart Data (Last 28 days, grouped into 4 weeks)
    monthly_chart = []
    for i in range(3, -1, -1):
        week_start = today - datetime.timedelta(days=(i+1)*7)
        week_end = today - datetime.timedelta(days=i*7)
        week_seconds = (
            db.query(func.sum(StudySession.duration_seconds))
            .filter(
                StudySession.user_id == user_id,
                StudySession.start_time >= datetime.datetime.combine(week_start, datetime.time.min),
                StudySession.start_time < datetime.datetime.combine(week_end, datetime.time.max)
            )
            .scalar()
        ) or 0
        monthly_chart.append({
            "day": f"Wk {4-i}",
            "minutes": round(week_seconds / 60.0, 1)
        })

    # 8. Strong vs. Weak Topics Calculation
    # We retrieve recent quizzes and classify subjects with < 70% as weak, and >= 70% as strong.
    weak_subjects = set()
    strong_subjects = set()
    for q in completed_quizzes:
        pct = (q.score / q.max_score) * 100 if q.max_score > 0 else 0
        subject_name = q.subject.name if q.subject else "General"
        if pct < 70:
            weak_subjects.add(subject_name)
        else:
            strong_subjects.add(subject_name)

    # Remove overlaps from strong if they are currently weak
    strong_subjects = strong_subjects - weak_subjects

    # 9. Recent Activities Feed
    recent_activities = []
    # Fetch recent uploads
    recent_files = (
        db.query(File)
        .filter(File.user_id == user_id)
        .order_by(File.created_at.desc())
        .limit(3)
        .all()
    )
    for f in recent_files:
        recent_activities.append({
            "type": "upload",
            "message": f"Uploaded material '{f.name}'",
            "time": f.created_at.isoformat()
        })
    
    # Fetch recent quiz submissions
    recent_quizzes = (
        db.query(Quiz)
        .filter(Quiz.user_id == user_id, Quiz.status == QuizStatus.COMPLETED)
        .order_by(Quiz.updated_at.desc())
        .limit(3)
        .all()
    )
    for q in recent_quizzes:
        recent_activities.append({
            "type": "quiz",
            "message": f"Scored {q.score}/{q.max_score} in quiz '{q.title}'",
            "time": q.updated_at.isoformat()
        })

    # Sort recent activities descending
    recent_activities = sorted(recent_activities, key=lambda x: x["time"], reverse=True)[:5]

    return {
        "streak_days": streak,
        "time_studied_minutes": round(total_study_seconds / 60.0, 1),
        "files_uploaded": total_files,
        "ai_conversations": total_convs,
        "flashcards_total": total_cards,
        "flashcards_mastered": mastered_cards,
        "quiz_count": total_quizzes,
        "quiz_average_percent": average_quiz_score,
        "weak_subjects": list(weak_subjects),
        "strong_subjects": list(strong_subjects),
        "weekly_progress": weekly_chart,
        "daily_progress": daily_chart,
        "monthly_progress": monthly_chart,
        "recent_activity": recent_activities
    }
