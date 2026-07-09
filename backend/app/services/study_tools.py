import datetime
import json
import logging
import math
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.document import DocumentChunk
from app.models.subject import File
from app.models.flashcard import Flashcard
from app.services.llm import llm_service

logger = logging.getLogger(__name__)

class StudyToolsService:
    def generate_smart_notes(
        self,
        db: Session,
        user_id: int,
        file_ids: List[int],
        note_type: str = "detailed"
    ) -> str:
        """
        Gathers text context from selected files, triggers LLM note generation,
        and returns the markdown notes.
        """
        # Fetch document chunks for context
        chunks = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.file_id.in_(file_ids))
            .order_by(DocumentChunk.page_number, DocumentChunk.chunk_index)
            .limit(15)  # Pull key initial content to avoid prompt size blowup
            .all()
        )

        if not chunks:
            return "No content found in selected files to generate notes."

        context_str = "\n".join([f"[Page {c.page_number}] {c.text_content}" for c in chunks])

        # Prompt formatting based on type
        prompt_templates = {
            "detailed": "Create highly detailed, structured revision notes from the material. Include headings, bullet points, and definitions.",
            "bullet": "Create concise bulleted study notes summarizing the core points of the text.",
            "revision": "Create a quick revision cheat-sheet. Highlight only critical facts, key formulas, and must-know summaries.",
            "formula": "Extract all mathematical formulas, physics equations, chemical equations, or quantitative models. Present them in LaTeX block format with explanations.",
            "definitions": "Generate a dictionary-style list of key terms, vocabulary, concepts, and their precise definitions.",
            "mindmap": "Create a text-based hierarchical mind-map layout using indented markdown list format representing how concepts connect."
        }

        instruction = prompt_templates.get(note_type, prompt_templates["detailed"])
        
        prompt = (
            f"Study Context:\n---\n{context_str}\n---\n"
            f"Task: {instruction}\n"
            "Format the output entirely in beautiful GitHub Flavored Markdown. "
            "Use LaTeX for formulas (inline with \\(...\\), display blocks with \\[[...]\\]) if applicable."
        )

        system_instruction = "You are an elite academic assistant specializing in distilling and summarizing textbooks."
        return llm_service.generate_response(prompt=prompt, system_instruction=system_instruction)

    def generate_flashcards(
        self,
        db: Session,
        user_id: int,
        file_id: int,
        num_cards: int = 5
    ) -> List[Flashcard]:
        """
        Queries PDF/file content, uses LLM to generate Q/A pairs in JSON format,
        and saves them to the database. Falls back to a smart heuristic
        parser if no API keys are present or if LLM fails.
        """
        file_record = db.query(File).filter(File.id == file_id, File.user_id == user_id).first()
        if not file_record:
            raise ValueError("File not found or unauthorized.")

        # Pull chunks
        chunks = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.file_id == file_id)
            .limit(10)
            .all()
        )

        context_str = "\n".join([c.text_content for c in chunks])

        prompt = (
            f"Review this learning material:\n---\n{context_str}\n---\n"
            f"Generate exactly {num_cards} distinct flashcards. Each card must have a question on the front "
            "and a detailed answer/explanation on the back. Return the response strictly as a JSON array "
            "of objects, with each object having exact keys 'front', 'back', 'difficulty', and 'topic'.\n"
            "Example format:\n"
            "[\n"
            "  {\n"
            "    \"front\": \"What is RAG?\",\n"
            "    \"back\": \"Retrieval-Augmented Generation...\",\n"
            "    \"difficulty\": \"medium\",\n"
            "    \"topic\": \"AI Engineering\"\n"
            "  }\n"
            "]"
        )

        system_instruction = "You are an expert examiner. You output strictly valid, parsable JSON matching schemas requested."

        # Check if LLM keys are configured
        from app.services.llm import llm_service
        has_keys = bool(llm_service.gemini_key or llm_service.openai_key)
        
        cards_data = []
        if has_keys:
            try:
                response_text = llm_service.generate_response(prompt=prompt, system_instruction=system_instruction)
                cleaned_json = response_text.replace("```json", "").replace("```", "").strip()
                cards_data = json.loads(cleaned_json)
            except Exception as err:
                logger.error(f"Error calling LLM or parsing json for flashcards: {err}")

        # Fallback to heuristic parser if no keys or LLM output failed/empty
        if not cards_data:
            logger.info("Using smart heuristic extraction parser for flashcard generation...")
            cards_data = self._heuristic_generate_flashcards(context_str, file_record.name, num_cards)

        flashcards = []
        for card in cards_data:
            db_card = Flashcard(
                front=card.get("front", "Empty Question"),
                back=card.get("back", "Empty Answer"),
                difficulty=card.get("difficulty", "medium"),
                topic=card.get("topic", "General"),
                subject_id=file_record.subject_id,
                user_id=user_id
            )
            db.add(db_card)
            flashcards.append(db_card)
        db.commit()

        return flashcards

    def _heuristic_generate_flashcards(self, context_str: str, file_name: str, num_cards: int) -> List[Dict[str, Any]]:
        import re
        
        # 1. Clean context and split into sentences
        clean_context = re.sub(r'\[Scanned page[^\]]*\]', '', context_str)
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean_context) if len(s.strip()) > 20]
        
        # 2. Try to extract definitions dynamically from sentences
        definition_cards = []
        patterns = [
            (r'^([^.]{3,35})\s+is\s+the\s+([^.]+)\.'),
            (r'^([^.]{3,35})\s+is\s+a\s+([^.]+)\.'),
            (r'^([^.]{3,35})\s+refers\s+to\s+([^.]+)\.'),
            (r'^([^.]{3,35})\s+means\s+([^.]+)\.'),
            (r'^([^.]{3,35})\s+is\s+defined\s+as\s+([^.]+)\.')
        ]
        
        seen_terms = set()
        for sentence in sentences:
            for pattern in patterns:
                match = re.match(pattern, sentence, re.IGNORECASE)
                if match:
                    term = match.group(1).strip()
                    # Basic checks to ensure it's a valid term (not a pronoun, and short)
                    words = term.split()
                    if (
                        len(words) <= 4 and 
                        words[0].lower() not in ("it", "they", "this", "these", "there", "which", "who", "he", "she", "we", "you", "that", "in", "on", "at", "by", "for", "with") and
                        term.lower() not in seen_terms
                    ):
                        seen_terms.add(term.lower())
                        definition_cards.append({
                            "front": f"What is {term}?",
                            "back": sentence,
                            "difficulty": "medium",
                            "topic": "Core Concept"
                        })
                        break # Go to next sentence
                        
        logger.info(f"Extracted {len(definition_cards)} dynamic definition flashcards from context.")
        
        # 3. If we got enough cards, return them
        if len(definition_cards) >= num_cards:
            return definition_cards[:num_cards]
            
        # 4. Otherwise, pad with our default questions but pair them with sentences from context
        fronts_list = [q["front"] for q in definition_cards]
        seen_fronts = set(fronts_list)
        
        # General templates we can customize
        has_coa = any(k in context_str.lower() for k in ("coa", "cache", "interrupt", "pipeline", "memory", "alu", "instruction"))
        has_uhv = any(k in context_str.lower() for k in ("uhv", "prosperity", "happiness", "harmony", "sanyam", "suvidha"))
        
        fallback_templates = []
        if has_coa:
            fallback_templates = [
                ("What is Cache Memory and why is it used?", "cache"),
                ("Explain the concept of Pipelining in computer processors.", "pipeline"),
                ("What is Direct Memory Access (DMA) and what advantage does it provide?", "dma"),
                ("What is an Interrupt and how does the CPU handle it?", "interrupt"),
                ("What is the purpose of the Arithmetic Logic Unit (ALU) in a CPU?", "alu")
            ]
        elif has_uhv:
            fallback_templates = [
                ("What is the difference between prosperity and wealth?", "prosperity"),
                ("Differentiate between SVDD and SSDD status.", "svdd"),
                ("Explain the difference between intention and competence.", "intention"),
                ("What are the four orders of nature?", "four orders"),
                ("Define continuous happiness according to UHV.", "happiness")
            ]
        else:
            # Try to build term questions from random capitalized words
            capital_words = []
            for s in sentences[:30]:
                for word in re.findall(r'\b[A-Z][a-z]{3,15}\b', s):
                    if word.lower() not in ("the", "this", "that", "what", "which", "google", "gemini", "chapter", "section", "page", "failed", "error", "scanned"):
                        capital_words.append(word)
            # Remove duplicates
            unique_words = []
            for w in capital_words:
                if w not in unique_words:
                    unique_words.append(w)
            
            for word in unique_words[:10]:
                fallback_templates.append((f"What is the significance of {word} as discussed in the text?", word.lower()))
                
            # Default fallbacks
            fallback_templates.extend([
                (f"What is the core theme of {file_name}?", "purpose"),
                (f"What is the main concept discussed in {file_name}?", "key"),
                (f"What are the key definitions in {file_name}?", "definition"),
                (f"What are the main takeaways from {file_name}?", "takeaway")
            ])
            
        used_backs = {c["back"] for c in definition_cards}
        for q_text, keyword in fallback_templates:
            if len(definition_cards) >= num_cards:
                break
            if q_text in seen_fronts:
                continue
                
            seen_fronts.add(q_text)
            
            # Find best sentence using smart scoring
            best_sentence = ""
            best_score = -999999
            for s in sentences:
                s_clean = s.strip()
                if not s_clean or s_clean.lower() == q_text.lower() or "[scanned" in s_clean.lower() or s_clean in used_backs:
                    continue
                if keyword in s_clean.lower():
                    # Favor sentences close to 100 characters
                    length_score = -abs(len(s_clean) - 100)
                    
                    # Definition boost
                    def_bonus = 0
                    s_lower = s_clean.lower()
                    if any(verb in s_lower for verb in ("is the", "is a", "refers to", "means", "acts as", "defined as", "used for", "used to")):
                        def_bonus = 250
                        
                    # Header/footer penalty
                    header_penalty = 0
                    if any(term in s_lower for term in ("page ", "notes", "unit -", "chapter", "slide", "http", "fundamentals")):
                        header_penalty = -400
                        
                    score = length_score + def_bonus + header_penalty
                    if score > best_score:
                        best_score = score
                        best_sentence = s_clean
            
            if not best_sentence:
                # Find any clean sentence of medium length that hasn't been used yet
                clean_list = [s.strip() for s in sentences if len(s.strip()) > 30 and s.strip() not in used_backs and not any(term in s.strip().lower() for term in ("page ", "notes", "unit -", "chapter"))]
                if clean_list:
                    best_sentence = clean_list[0]
                else:
                    best_sentence = "Review the details of this topic inside your chapter notes for complete understanding."
                
            used_backs.add(best_sentence)
            definition_cards.append({
                "front": q_text,
                "back": best_sentence,
                "difficulty": "medium",
                "topic": "Core Concept"
            })
            
        while len(definition_cards) < num_cards:
            definition_cards.append({
                "front": f"Key Term Review from {file_name} (Card {len(definition_cards)+1})",
                "back": f"Please study the notes and slides related to {file_name} to review this chapter's key formulas and terms.",
                "difficulty": "easy",
                "topic": "General"
            })
            
        return definition_cards



    def review_flashcard_sm2(self, db: Session, flashcard_id: int, rating: int, user_id: int) -> Flashcard:
        """
        Updates spaced repetition variables on a flashcard using the SuperMemo-2 algorithm.
        Rating: 0 (forgot) to 5 (excellent response).
        """
        card = db.query(Flashcard).filter(Flashcard.id == flashcard_id, Flashcard.user_id == user_id).first()
        if not card:
            raise ValueError("Flashcard not found or unauthorized.")

        # SM-2 Algorithm implementation
        if rating < 3:
            card.repetitions = 0
            card.interval = 1
        else:
            if card.repetitions == 0:
                card.interval = 1
            elif card.repetitions == 1:
                card.interval = 6
            else:
                card.interval = math.ceil(card.interval * card.ease_factor)
            
            card.repetitions += 1

        # Adjust ease factor: EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        card.ease_factor = card.ease_factor + (0.1 - (5 - rating) * (0.08 + (5 - rating) * 0.02))
        if card.ease_factor < 1.3:
            card.ease_factor = 1.3

        # Calculate next review date
        card.next_review = datetime.datetime.utcnow() + datetime.timedelta(days=card.interval)
        db.commit()
        db.refresh(card)
        return card

study_tools_service = StudyToolsService()
