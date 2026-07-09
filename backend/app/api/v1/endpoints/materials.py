from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile, BackgroundTasks, status
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User
from app.models.subject import Subject, File as DbFile, FileStatus, OCRStatus
from app.schemas.subject import SubjectCreate, SubjectOut, FileOut
from app.services.storage import storage_service
from app.services.pipeline import process_file_pipeline

router = APIRouter()

# Max file size limits (50MB for documents, 10MB for images)
MAX_DOC_SIZE = 50 * 1024 * 1024
MAX_IMG_SIZE = 10 * 1024 * 1024

VALID_MIME_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
    "text/plain": "txt",
    "image/png": "png",
    "image/jpeg": "jpeg",
    "image/jpg": "jpg",
}

@router.post("/subjects", response_model=SubjectOut, status_code=status.HTTP_201_CREATED)
def create_subject(
    subject_in: SubjectCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Creates a new subject directory/tag for organizing materials.
    """
    db_subject = Subject(
        name=subject_in.name,
        description=subject_in.description,
        color=subject_in.color,
        user_id=current_user.id
    )
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return db_subject

@router.get("/subjects", response_model=List[SubjectOut])
def list_subjects(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Lists all subjects owned by the current authenticated user.
    """
    return db.query(Subject).filter(Subject.user_id == current_user.id).all()

@router.delete("/subjects/{subject_id}", status_code=status.HTTP_200_OK)
def delete_subject(
    subject_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Deletes a subject. Associated files remain in database but set subject_id to null.
    """
    subject = db.query(Subject).filter(Subject.id == subject_id, Subject.user_id == current_user.id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found or access denied."
        )
    db.delete(subject)
    db.commit()
    return {"status": "success", "message": "Subject deleted successfully."}

@router.post("/upload", response_model=FileOut, status_code=status.HTTP_202_ACCEPTED)
async def upload_material(
    background_tasks: BackgroundTasks,
    file: UploadFile = FastAPIFile(...),
    subject_id: Optional[int] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Uploads a learning material file.
    Validates file sizes, mime types, saves to storage, and enqueues OCR/chunking pipeline.
    """
    # Validate MIME type
    if file.content_type not in VALID_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Supported types: {', '.join(VALID_MIME_TYPES.keys())}"
        )

    # Read content to check file size
    file_bytes = await file.read()
    file_size = len(file_bytes)
    
    # Check file size limits
    is_image = "image" in file.content_type
    limit = MAX_IMG_SIZE if is_image else MAX_DOC_SIZE
    if file_size > limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum upload size limit of {limit // (1024*1024)}MB."
        )

    # Validate subject if provided
    if subject_id:
        subject = db.query(Subject).filter(Subject.id == subject_id, Subject.user_id == current_user.id).first()
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target Subject folder not found."
            )

    # Save to storage (S3 or Local)
    try:
        storage_path = storage_service.upload_file(file_bytes, file.filename)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file to storage system: {str(e)}"
        )

    # Create Database record
    db_file = DbFile(
        name=file.filename,
        path=storage_path,
        mime_type=file.content_type,
        file_size=file_size,
        status=FileStatus.UPLOADING,
        ocr_status=OCRStatus.PENDING,
        subject_id=subject_id,
        user_id=current_user.id
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    # Enqueue pipeline task asynchronously
    background_tasks.add_task(process_file_pipeline, db_file.id)

    return db_file

@router.get("/files", response_model=List[FileOut])
def list_files(
    subject_id: Optional[int] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    List all materials uploaded by the user, optionally filtered by subject_id.
    """
    query = db.query(DbFile).filter(DbFile.user_id == current_user.id)
    if subject_id:
        query = query.filter(DbFile.subject_id == subject_id)
    return query.all()

@router.get("/files/{file_id}", response_model=FileOut)
def get_file_status(
    file_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Retrieves the processing status of a specific file.
    """
    file_record = db.query(DbFile).filter(DbFile.id == file_id, DbFile.user_id == current_user.id).first()
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found or access denied."
        )
    return file_record

@router.delete("/files/{file_id}", status_code=status.HTTP_200_OK)
def delete_file(
    file_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Deletes the file metadata, database cascade chunks, and physical storage object.
    """
    file_record = db.query(DbFile).filter(DbFile.id == file_id, DbFile.user_id == current_user.id).first()
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found or access denied."
        )
    
    # Delete from storage first
    storage_service.delete_file(file_record.path)

    # Delete from Vector DB
    try:
        from app.services.vector_db import vector_db_service
        vector_db_service.delete_by_filter({"file_id": file_id})
    except Exception as e:
        # Don't fail the primary deletion if Chroma has an issue
        pass

    # Delete from DB (automatically cascades to ocr_results and document_chunks)
    db.delete(file_record)
    db.commit()

    return {"status": "success", "message": "File deleted successfully."}

@router.patch("/files/{file_id}/subject", response_model=FileOut)
def update_file_subject(
    file_id: int,
    subject_id: Optional[int] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Assigns or updates the subject folder for a specific file.
    """
    file_record = db.query(DbFile).filter(DbFile.id == file_id, DbFile.user_id == current_user.id).first()
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found or access denied."
        )
    if subject_id:
        subject = db.query(Subject).filter(Subject.id == subject_id, Subject.user_id == current_user.id).first()
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target Subject folder not found."
            )
    file_record.subject_id = subject_id
    db.commit()
    db.refresh(file_record)
    return file_record

