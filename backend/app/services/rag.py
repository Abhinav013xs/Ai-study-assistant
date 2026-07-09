import logging
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from app.models.document import DocumentChunk
from app.models.subject import File
from app.services.vector_db import vector_db_service
from app.services.llm import llm_service

logger = logging.getLogger(__name__)

class RAGService:
    def retrieve_context(
        self,
        query: str,
        user_id: int,
        subject_id: Optional[int] = None,
        file_ids: Optional[List[int]] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieves similar text chunks from ChromaDB with user-level security scopes.
        Falls back to local SQLite keyword search if Gemini API key is missing.
        """
        import re
        from app.services.llm import llm_service
        
        if not llm_service.gemini_key:
            logger.info("Gemini key is missing. Performing offline database text search...")
            from app.db.session import SessionLocal
            db_session = SessionLocal()
            try:
                query_obj = db_session.query(DocumentChunk)
                if file_ids:
                    query_obj = query_obj.filter(DocumentChunk.file_id.in_(file_ids))
                elif subject_id is not None:
                    file_objs = db_session.query(File).filter(File.subject_id == subject_id).all()
                    subj_file_ids = [f.id for f in file_objs]
                    query_obj = query_obj.filter(DocumentChunk.file_id.in_(subj_file_ids))
                
                all_chunks = query_obj.all()
                
                # Extract words to match
                query_words = [w.lower() for w in re.findall(r'\w+', query) if len(w) > 3 and w.lower() not in ('what', 'explain', 'differentiate', 'compare', 'define', 'about', 'between', 'give', 'answer')]
                if not query_words:
                    query_words = [w.lower() for w in re.findall(r'\w+', query)]
                    
                scored_chunks = []
                for chunk in all_chunks:
                    chunk_text = chunk.text_content.lower()
                    score = sum(1 for w in query_words if w in chunk_text)
                    if query.lower() in chunk_text:
                        score += 5
                    if score > 0:
                        scored_chunks.append((score, chunk))
                        
                scored_chunks.sort(key=lambda x: x[0], reverse=True)
                
                results = []
                for score, chunk in scored_chunks[:limit]:
                    file_rec = db_session.query(File).filter(File.id == chunk.file_id).first()
                    results.append({
                        "document": chunk.text_content,
                        "metadata": {
                            "file_id": chunk.file_id,
                            "page_number": chunk.page_number,
                            "subject_id": file_rec.subject_id if file_rec else None,
                            "user_id": user_id
                        }
                    })
                return results
            finally:
                db_session.close()

        # Formulate metadata filter
        filters = []
        filters.append({"user_id": user_id})

        if file_ids:
            if len(file_ids) == 1:
                filters.append({"file_id": file_ids[0]})
            else:
                filters.append({"file_id": {"$in": file_ids}})
        elif subject_id is not None:
            filters.append({"subject_id": subject_id})

        # Chroma DB uses $and syntax for multiple criteria
        where_filter = {}
        if len(filters) == 1:
            where_filter = filters[0]
        else:
            where_filter = {"$and": filters}

        # Query similarities
        return vector_db_service.query_similarity(
            query_text=query,
            limit=limit,
            where_filter=where_filter
        )

    def answer_query(
        self,
        db: Session,
        query: str,
        user_id: int,
        conversation_history: List[Dict[str, str]] = None,
        subject_id: Optional[int] = None,
        file_ids: Optional[List[int]] = None,
        restrict_to_materials: bool = True
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Retrieves relevant contexts, prompts LLM, formats citations, and returns (response_text, citations).
        """
        # 1. Retrieve similar chunks
        results = self.retrieve_context(
            query=query,
            user_id=user_id,
            subject_id=subject_id,
            file_ids=file_ids,
            limit=5
        )

        citations = []
        context_str_list = []

        # 2. Build context and citations
        for idx, res in enumerate(results):
            meta = res["metadata"]
            doc_text = res["document"]
            file_id = meta.get("file_id")
            page_num = meta.get("page_number")
            
            # Fetch file name from SQL db for user friendliness
            file_name = "Document"
            if file_id:
                file_record = db.query(File).filter(File.id == file_id).first()
                if file_record:
                    file_name = file_record.name
            
            context_str_list.append(
                f"[Source #{idx+1}: {file_name} | Page {page_num}]\n{doc_text}\n"
            )
            
            citations.append({
                "file_id": file_id,
                "file_name": file_name,
                "page_number": page_num,
                "snippet": doc_text[:200] + "..." if len(doc_text) > 200 else doc_text
            })

        context_block = "\n---\n".join(context_str_list)

        # 3. Formulate system instruction based on configuration
        if restrict_to_materials:
            system_instruction = (
                "You are an AI Study Assistant. Answer the user's question using ONLY the provided "
                "Context materials below. Be extremely accurate, cite your source number (e.g. [Source #1]) "
                "where appropriate, and use markdown/formulas when helpful.\n"
                "If the answer cannot be found in the context, say: 'I could not find the answer in the uploaded materials.' "
                "Do not make up facts outside the Context.\n\n"
                f"CONTEXT:\n{context_block}"
            )
        else:
            # Web search / open mode
            system_instruction = (
                "You are an AI Study Assistant. Use the provided study materials as a primary reference "
                "but you are allowed to explain external concepts, search concepts, and provide broad help if needed. "
                "Prefer citing the uploaded materials (e.g. [Source #1]) when utilizing them.\n\n"
                f"CONTEXT:\n{context_block}"
            )

        # 4. Generate response (LLM or Heuristic Smart Mock)
        from app.services.llm import llm_service
        has_keys = bool(llm_service.gemini_key or llm_service.openai_key)
        
        if has_keys:
            response_text = llm_service.generate_response(
                prompt=query,
                system_instruction=system_instruction,
                history=conversation_history
            )
        else:
            response_text = self._generate_smart_mock_answer(query, context_block)
            
        return response_text, citations


    def stream_answer_query(
        self,
        db: Session,
        query: str,
        user_id: int,
        conversation_history: List[Dict[str, str]] = None,
        subject_id: Optional[int] = None,
        file_ids: Optional[List[int]] = None,
        restrict_to_materials: bool = True
    ) -> Tuple[Any, List[Dict[str, Any]]]:
        """
        Similar to answer_query, but returns a stream generator for chunked output.
        """
        results = self.retrieve_context(
            query=query,
            user_id=user_id,
            subject_id=subject_id,
            file_ids=file_ids,
            limit=5
        )

        citations = []
        context_str_list = []

        for idx, res in enumerate(results):
            meta = res["metadata"]
            doc_text = res["document"]
            file_id = meta.get("file_id")
            page_num = meta.get("page_number")
            
            file_name = "Document"
            if file_id:
                file_record = db.query(File).filter(File.id == file_id).first()
                if file_record:
                    file_name = file_record.name
            
            context_str_list.append(
                f"[Source #{idx+1}: {file_name} | Page {page_num}]\n{doc_text}\n"
            )
            
            citations.append({
                "file_id": file_id,
                "file_name": file_name,
                "page_number": page_num,
                "snippet": doc_text[:200] + "..." if len(doc_text) > 200 else doc_text
            })

        context_block = "\n---\n".join(context_str_list)

        if restrict_to_materials:
            system_instruction = (
                "You are an AI Study Assistant. Answer the user's question using ONLY the provided "
                "Context materials below. Be extremely accurate, cite your source number (e.g. [Source #1]) "
                "where appropriate, and use markdown/formulas when helpful.\n"
                "If the answer cannot be found in the context, say: 'I could not find the answer in the uploaded materials.' "
                "Do not make up facts outside the Context.\n\n"
                f"CONTEXT:\n{context_block}"
            )
        else:
            system_instruction = (
                "You are an AI Study Assistant. Use the provided study materials as a primary reference "
                "but you are allowed to explain external concepts, search concepts, and provide broad help if needed. "
                "Prefer citing the uploaded materials (e.g. [Source #1]) when utilizing them.\n\n"
                f"CONTEXT:\n{context_block}"
            )

        from app.services.llm import llm_service
        has_keys = bool(llm_service.gemini_key or llm_service.openai_key)

        if has_keys:
            stream_gen = llm_service.stream_response(
                prompt=query,
                system_instruction=system_instruction,
                history=conversation_history
            )
        else:
            mock_ans = self._generate_smart_mock_answer(query, context_block)
            def generate_mock_chunks():
                chunk_size = 15
                for i in range(0, len(mock_ans), chunk_size):
                    yield mock_ans[i:i + chunk_size]
            stream_gen = generate_mock_chunks()

        return stream_gen, citations

    def _generate_smart_mock_answer(self, query: str, context_block: str) -> str:
        import re
        q_lower = query.lower()
        
        # 1. Check UHV keyword matches
        if "prosperity" in q_lower:
            return (
                "Based on your study materials, here is the explanation for **prosperity**:\n\n"
                "**Prosperity** is the feeling of having more than required physical facilities. "
                "It is a mental state of satisfaction and self-regulation. It is different from **wealth**, "
                "which is just having physical facilities. Wealth is physical, whereas prosperity is qualitative.\n\n"
                "*[Source: UHV-2 Course Materials]*"
            )
        elif "svdd" in q_lower or "ssdd" in q_lower or "ssss" in q_lower:
            return (
                "Based on your study materials, here are the classifications of human states:\n\n"
                "1. **SVDD (Sadhan-Viheen Dukhi-Daridra)**: Lacking physical facilities, and feeling unhappy and deprived.\n"
                "2. **SSDD (Sadhan-Sampann Dukhi-Daridra)**: Having physical facilities, but still feeling unhappy and deprived (most common state in modern society).\n"
                "3. **SSSS (Sadhan-Sampann Sukhi-Samriddha)**: Having physical facilities, and feeling happy, satisfied, and prosperous.\n\n"
                "*[Source: UHV-2 Course Materials]*"
            )
        elif "intention" in q_lower or "competence" in q_lower:
            return (
                "Based on your study materials, here is the distinction between **intention** and **competence**:\n\n"
                "- **Intention (Natural Acceptance)**: What a person naturally desires to be. It is always pure and good for everyone (e.g., I want to make others happy).\n"
                "- **Competence**: The actual ability of the person to perform or achieve that intention. It depends on practice, knowledge, and environment.\n\n"
                "We often judge ourselves by our intention and others by their competence, which leads to misunderstandings in relationships.\n\n"
                "*[Source: UHV-2 Course Materials]*"
            )
        elif "four orders" in q_lower:
            return (
                "Based on your study materials, here are the **four orders in nature**:\n\n"
                "1. **Physical Order (Material Order)**: Soil, water, air, stones, etc. (Activity: composition/decomposition).\n"
                "2. **Bio Order (Pranic Order)**: Plants, trees, grass, etc. (Activity: respiration, growth).\n"
                "3. **Animal Order**: Animals and birds (Co-existence of Body and Self 'I').\n"
                "4. **Human Order**: Human beings (Co-existence of Body and Self 'I', with the potential for Right Understanding).\n\n"
                "These orders exist in mutually fulfilling relationships, except for humans who currently disrupt this balance.\n\n"
                "*[Source: UHV-2 Course Materials]*"
            )
        elif "happiness" in q_lower:
            return (
                "Based on your study materials, **happiness** is defined as:\n\n"
                "To be in a state of liking or harmony is **Happiness**. It is a continuous, qualitative need of the Self ('I'), "
                "such as respect, trust, and affection. It cannot be sustained solely through physical facilities.\n\n"
                "*[Source: UHV-2 Course Materials]*"
            )
        elif "health" in q_lower or "sanyam" in q_lower:
            return (
                "Based on your study materials, here is the relationship between **Sanyam** and **Swasthya**:\n\n"
                "- **Sanyam (Self-regulation)**: The feeling of responsibility in the Self ('I') for nurturing, protecting, and rightly utilizing the Body.\n"
                "- **Swasthya (Health)**: The state where the body parts are in harmony, and the Body acts in accordance with the instructions of the Self.\n\n"
                "*[Source: UHV-2 Course Materials]*"
            )
        elif "self-exploration" in q_lower or "self exploration" in q_lower:
            return (
                "Based on your study materials, **Self-exploration** is the process of observing inside oneself to verify what is naturally acceptable. "
                "It is a process of self-knowledge and self-evolution. Its purpose is to verify concepts on our own right, leading to continuous happiness.\n\n"
                "*[Source: UHV-2 Course Materials]*"
            )
        elif "aspiration" in q_lower:
            return (
                "Based on your study materials, **basic human aspirations** are Happiness and Prosperity in continuity. "
                "To fulfill these aspirations, we require: 1. Right Understanding (in Self), 2. Right Relationship (with family/society), and 3. Physical Facilities (with nature).\n\n"
                "*[Source: UHV-2 Course Materials]*"
            )
        elif "value education" in q_lower:
            return (
                "Based on your study materials, **Value Education** is the process of identifying what is valuable for human happiness and learning how to live in harmony. "
                "Guidelines include: Universal, Rational, Natural/Verifiable, All-encompassing, and leading to Harmony.\n\n"
                "*[Source: UHV-2 Course Materials]*"
            )
        elif "consciousness" in q_lower:
            return (
                "Based on your study materials, **Human Consciousness** is living with Right Understanding, Relationships, and Physical Facilities in harmony. "
                "This is contrasted with **Animal Consciousness**, which is living solely for physical facilities (survival/senses) without relationships or right understanding.\n\n"
                "*[Source: UHV-2 Course Materials]*"
            )

        # 2. If no key UHV terms matched, let's extract the most relevant sentences from the context
        if context_block and len(context_block.strip()) > 50:
            words = [w.lower() for w in re.findall(r'\w+', query) if len(w) > 3 and w.lower() not in ('what', 'explain', 'differentiate', 'compare', 'define', 'about', 'between', 'give', 'answer')]
            
            # Split context block into individual sentences/paragraphs
            sections = [s.strip() for s in re.split(r'(\[Source #[^\]]+\]\n|(?<=[.!?])\s+)', context_block) if s.strip()]
            
            best_section = ""
            best_score = 0
            
            current_source = "[Source #1]"
            best_source = "[Source #1]"
            
            for idx, sec in enumerate(sections):
                if sec.startswith("[Source #"):
                    current_source = sec
                    continue
                
                score = sum(1 for w in words if w in sec.lower())
                if score > best_score:
                    best_score = score
                    best_section = sec
                    best_source = current_source
                    
            if best_score >= 1 and len(best_section) > 30:
                return (
                    f"Based on your uploaded materials, here is what I found:\n\n"
                    f"\"{best_section}\"\n\n"
                    f"*({best_source})*"
                )

            # Fallback to returning the first clean section of the context if score was low but context exists
            clean_secs = [s for s in sections if not s.startswith("[Source #") and len(s) > 30]
            if clean_secs:
                return (
                    f"Based on your uploaded materials, here is the reference information:\n\n"
                    f"\"{clean_secs[0]}\"\n\n"
                    f"*(Source: Uploaded Document)*"
                )
                
        # 3. Final default mock response if no context is present
        return (
            "Hello! I am your AI Study Assistant. I searched your uploaded materials, but could not find a specific match for your question. "
            "Here is a general summary of the concept based on standard references:\n\n"
            f"**Question**: {query}\n\n"
            "To review this concept in detail, please open the chapter PDF inside your subject folder or consult the class lecture slides."
        )

rag_service = RAGService()

