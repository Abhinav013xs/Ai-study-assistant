from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

# --- StudyPlan Schemas ---
class StudyPlanBase(BaseModel):
    title: str
    start_date: datetime
    end_date: datetime
    daily_hours: int = Field(2, ge=1, le=12)

class StudyPlanCreate(StudyPlanBase):
    subjects: List[int]  # List of subject IDs to include
    weak_topics: Optional[List[str]] = None
    exam_dates: Optional[Dict[str, datetime]] = None  # subject name -> exam date

class StudyPlanOut(StudyPlanBase):
    id: int
    user_id: int
    schedule_json: Any  # JSON structure containing tasks / days
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- StudySession Schemas ---
class StudySessionBase(BaseModel):
    notes: Optional[str] = None
    subject_id: Optional[int] = None

class StudySessionCreate(StudySessionBase):
    start_time: datetime

class StudySessionEnd(BaseModel):
    end_time: datetime
    notes: Optional[str] = None

class StudySessionOut(StudySessionBase):
    id: int
    user_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: int
    created_at: datetime

    class Config:
        from_attributes = True
