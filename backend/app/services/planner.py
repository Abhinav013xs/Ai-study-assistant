import json
import logging
import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.quiz import Quiz, QuizStatus
from app.models.subject import Subject
from app.models.study_plan import StudyPlan
from app.schemas.study_plan import StudyPlanCreate
from app.services.llm import llm_service

logger = logging.getLogger(__name__)

class StudyPlannerService:
    def generate_adaptive_plan(
        self,
        db: Session,
        user_id: int,
        req: StudyPlanCreate
    ) -> StudyPlan:
        """
        Gathers user inputs + recent quiz performance to dynamically output
        a personalized study calendar via LLM, saving the record.
        """
        # 1. Fetch user's subjects names
        subjects = db.query(Subject).filter(Subject.id.in_(req.subjects), Subject.user_id == user_id).all()
        subj_names = [s.name for s in subjects]
        if not subj_names:
            raise ValueError("No valid subjects specified for the plan.")

        # 2. Fetch recent quiz scores to identify weak areas (Dynamic Adaptation)
        quizzes = (
            db.query(Quiz)
            .filter(Quiz.user_id == user_id, Quiz.status == QuizStatus.COMPLETED)
            .order_by(Quiz.created_at.desc())
            .limit(10)
            .all()
        )

        weak_subjects_perf = []
        for q in quizzes:
            pct = (q.score / q.max_score) * 100 if q.max_score > 0 else 100
            if pct < 70 and q.subject:
                weak_subjects_perf.append(f"{q.subject.name} (Score: {q.score}/{q.max_score})")

        # Compile weak topics details
        weak_topics_str = ", ".join(req.weak_topics) if req.weak_topics else "None specified"
        weak_perf_str = ", ".join(weak_subjects_perf) if weak_subjects_perf else "None detected (student is scoring well)"
        
        # Compile exam dates
        exams_str = ""
        if req.exam_dates:
            exams_str = "\n".join([f"- {subj}: {date.strftime('%Y-%m-%d')}" for subj, date in req.exam_dates.items()])
        else:
            exams_str = "No specific upcoming exam dates set."

        # 3. Formulate Prompt for LLM
        prompt = (
            f"Generate a customized study calendar between {req.start_date.strftime('%Y-%m-%d')} and {req.end_date.strftime('%Y-%m-%d')}.\n"
            f"User Profile details:\n"
            f"- Subjects to study: {', '.join(subj_names)}\n"
            f"- Targeted study hours per day: {req.daily_hours} hours\n"
            f"- Stated weak topics: {weak_topics_str}\n"
            f"- Quiz performance flags (needs extra focus): {weak_perf_str}\n"
            f"Upcoming Exams:\n{exams_str}\n\n"
            "Task: Generate a daily task schedule list in JSON format. Output MUST be a JSON array of days. "
            "Weight weak subjects/topics with additional review sessions. "
            "Each day object must have exact keys 'date' (string, YYYY-MM-DD) and 'tasks' (array of objects).\n"
            "Each task object must have:\n"
            "- 'subject': string (must match one of the active subjects)\n"
            "- 'topic': string (specific study focus)\n"
            "- 'duration_minutes': integer (duration in minutes)\n"
            "- 'notes': string (brief action plan, e.g., 'Do practice problems', 'Read Chapter 4')\n\n"
            "Ensure the output contains strictly valid JSON and covers all days."
        )

        # Check if LLM keys are configured
        has_keys = bool(llm_service.gemini_key or llm_service.openai_key)
        
        schedule_data = None
        if has_keys:
            try:
                response_text = llm_service.generate_response(prompt=prompt, system_instruction=system_instruction)
                cleaned_json = response_text.replace("```json", "").replace("```", "").strip()
                schedule_data = json.loads(cleaned_json)
            except Exception as e:
                logger.error(f"Error calling LLM or parsing study plan JSON: {str(e)}")

        if not schedule_data:
            logger.info("Using smart heuristic extraction planner for study plan generation...")
            schedule_data = self._heuristic_generate_plan(db, req, subj_names)

        # Save Plan to Database
        db_plan = StudyPlan(
            title=req.title,
            start_date=req.start_date,
            end_date=req.end_date,
            daily_hours=req.daily_hours,
            schedule_json=schedule_data,
            user_id=user_id
        )
        db.add(db_plan)
        db.commit()
        db.refresh(db_plan)
        return db_plan

    def _heuristic_generate_plan(
        self,
        db: Session,
        req: StudyPlanCreate,
        subj_names: List[str]
    ) -> List[Dict[str, Any]]:
        import re
        import datetime
        from app.models.document import DocumentChunk
        from app.models.subject import File
        
        # 1. Gather all file IDs for these subjects
        files = db.query(File).filter(File.subject_id.in_(req.subjects)).all()
        file_ids = [f.id for f in files]
        
        chunks = []
        if file_ids:
            chunks = db.query(DocumentChunk).filter(DocumentChunk.file_id.in_(file_ids)).all()
            
        context_str = "\n".join([c.text_content for c in chunks])
        
        # 2. Extract topics/headings from PDF content
        candidates = []
        for line in context_str.split("\n"):
            line_clean = line.strip()
            # Heading check: starts with capital letter, no ending punctuation except colon, short
            if 10 < len(line_clean) < 45 and re.match(r'^[A-Z][a-zA-Z0-9\s:,-]+$', line_clean):
                if not any(k in line_clean.lower() for k in ("page ", "unit -", "notes", "chapter", "slide", "http")):
                    candidates.append(line_clean)
                    
        # Capitalized phrases check
        if len(candidates) < 5:
            phrases = re.findall(r'\b[A-Z][a-z]{3,15}\s+[A-Z][a-z]{3,15}(?:\s+[A-Z][a-z]{3,15})?\b', context_str)
            for p in phrases:
                p_clean = p.strip()
                if p_clean not in candidates and not any(k in p_clean.lower() for k in ("page", "unit", "notes", "chapter", "slide", "http")):
                    candidates.append(p_clean)
                    
        # Remove duplicates
        unique_topics = []
        for c in candidates:
            if c not in unique_topics:
                unique_topics.append(c)
                
        # Fallbacks if still empty
        if len(unique_topics) < 3:
            has_coa = any(k in context_str.lower() for k in ("coa", "cache", "interrupt", "pipeline", "memory", "alu", "instruction"))
            has_uhv = any(k in context_str.lower() for k in ("uhv", "prosperity", "happiness", "harmony", "sanyam", "suvidha"))
            if has_coa:
                unique_topics = ["Cache Memory Design", "Pipelining & CPU Speed", "Direct Memory Access", "Interrupt Processing", "ALU Subsystem Design"]
            elif has_uhv:
                unique_topics = ["Prosperity and Suvidha", "SVDD vs SSSS Living", "Intention vs Competence", "Four Orders of Nature", "Continuous Happiness & Sanyam"]
            else:
                unique_topics = ["Core Textbook Review", "Key Concept Summary", "Terminology Review", "Methodology Application", "Final Exam Practice"]
                
        # 3. Distribute topics across the schedule calendar
        delta = req.end_date - req.start_date
        num_days = max(1, delta.days)
        
        schedule_data = []
        for i in range(num_days):
            curr_date = req.start_date + datetime.timedelta(days=i)
            # Pick a topic cyclically
            topic = unique_topics[i % len(unique_topics)]
            
            # Formulate specific notes based on the topic
            notes = f"Read the corresponding textbook sections for {topic}. Outline key details, write down formulas, and solve practice questions."
            if i >= len(unique_topics):
                notes = f"Review and revise notes on {topic}. Take flashcard quizzes and self-evaluate your weak areas."
                
            schedule_data.append({
                "date": curr_date.strftime("%Y-%m-%d"),
                "tasks": [
                    {
                        "subject": subj_names[0] if subj_names else "General Study",
                        "topic": topic,
                        "duration_minutes": req.daily_hours * 60,
                        "notes": notes
                    }
                ]
            })
            
        return schedule_data

study_planner_service = StudyPlannerService()
