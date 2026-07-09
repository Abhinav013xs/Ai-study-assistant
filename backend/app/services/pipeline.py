import logging
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.subject import File, FileStatus, OCRStatus
from app.models.document import DocumentMetadata, OcrResult, DocumentChunk
from app.services.storage import storage_service
from app.services.ocr import ocr_service

logger = logging.getLogger(__name__)

def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 100) -> list:
    """
    Split text into character chunks with a sliding window.
    """
    chunks = []
    if not text:
        return chunks
    
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        # If the chunk reaches the end, break out of loop
        if end >= len(text):
            break
        start += chunk_size - chunk_overlap
    return chunks

def process_file_pipeline(file_id: int):
    """
    Core pipeline task that retrieves a file, runs OCR/text extraction,
    chunks the text, generates metadata, and updates status.
    This function is run asynchronously.
    """
    db: Session = SessionLocal()
    try:
        file_record = db.query(File).filter(File.id == file_id).first()
        if not file_record:
            logger.error(f"File {file_id} not found in pipeline processing.")
            return

        # Update status to processing
        file_record.status = FileStatus.PROCESSING
        file_record.ocr_status = OCRStatus.PROCESSING
        
        # Clean up any existing records for this file_id first to prevent unique constraint failures (from failed retries)
        db.query(DocumentMetadata).filter(DocumentMetadata.file_id == file_id).delete()
        db.query(OcrResult).filter(OcrResult.file_id == file_id).delete()
        db.query(DocumentChunk).filter(DocumentChunk.file_id == file_id).delete()
        
        db.commit()

        # Get file contents from storage
        file_bytes = storage_service.get_file_content(file_record.path)

        # Determine file type and extract text page-by-page
        pages = []
        mime = file_record.mime_type.lower()

        if "pdf" in mime:
            pages = ocr_service.extract_text_from_pdf(file_bytes)
        elif "wordprocessingml" in mime or "docx" in mime:
            pages = ocr_service.extract_text_from_docx(file_bytes)
        elif "presentationml" in mime or "pptx" in mime or "powerpoint" in mime:
            pages = ocr_service.extract_text_from_pptx(file_bytes)
        elif "text" in mime or "plain" in mime or file_record.name.endswith(".txt"):
            text_content = file_bytes.decode("utf-8", errors="ignore")
            pages = [{"page_number": 1, "extracted_text": text_content}]
        elif "image" in mime or mime in ("png", "jpg", "jpeg"):
            pages = ocr_service.extract_text_from_image(file_bytes)
        else:
            raise ValueError(f"Unsupported file type: {file_record.mime_type}")

        # Create Metadata
        total_pages = len(pages)
        metadata_record = DocumentMetadata(
            file_id=file_id,
            total_pages=total_pages,
            title=file_record.name
        )
        db.add(metadata_record)

        # Save OCR Results and Chunks
        chunk_count = 0
        for page in pages:
            page_num = page["page_number"]
            extracted_text = page["extracted_text"]

            # Save page OCR result
            ocr_record = OcrResult(
                file_id=file_id,
                page_number=page_num,
                extracted_text=extracted_text
            )
            db.add(ocr_record)

            # Chunk page content
            text_chunks = chunk_text(extracted_text)
            for idx, text_chunk in enumerate(text_chunks):
                # We save a placeholder vector_id which will be updated or created in ChromaDB during RAG phase
                vector_id = f"chunk_{file_id}_{page_num}_{idx}"
                chunk_record = DocumentChunk(
                    file_id=file_id,
                    page_number=page_num,
                    chunk_index=idx,
                    text_content=text_chunk,
                    vector_id=vector_id
                )
                db.add(chunk_record)
                chunk_count += 1

        # Commit database records first so they have IDs
        db.commit()

        # Fetch and prepare chunks for indexing
        chunks = db.query(DocumentChunk).filter(DocumentChunk.file_id == file_id).all()
        if chunks:
            ids = [c.vector_id for c in chunks]
            texts = [c.text_content for c in chunks]
            metadatas = [
                {
                    "file_id": file_id,
                    "user_id": file_record.user_id,
                    "subject_id": file_record.subject_id if file_record.subject_id is not None else -1,
                    "page_number": c.page_number
                }
                for c in chunks
            ]
            
            from app.services.vector_db import vector_db_service
            success = vector_db_service.add_chunks(ids=ids, texts=texts, metadatas=metadatas)
            if not success:
                raise Exception("Failed to index chunks into Vector Database.")

        # Complete file processing
        file_record.status = FileStatus.PROCESSED
        file_record.ocr_status = OCRStatus.COMPLETED
        db.commit()
        logger.info(f"Successfully processed file {file_id}. Saved {total_pages} pages and {chunk_count} chunks.")

    except Exception as e:
        db.rollback()
        # Fetch file record again to record error safely
        file_record = db.query(File).filter(File.id == file_id).first()
        if file_record:
            file_record.status = FileStatus.FAILED
            file_record.ocr_status = OCRStatus.FAILED
            file_record.error_message = str(e)
            db.commit()
        logger.exception(f"Pipeline processing failed for file {file_id}: {str(e)}")
    finally:
        db.close()
