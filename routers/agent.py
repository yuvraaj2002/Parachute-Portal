import sys
import os
import json
import logging
import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime, UTC
from pydantic import BaseModel
import asyncio

# Add project root to path for imports
ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_PATH not in sys.path:
    sys.path.append(ROOT_PATH)

from models.database_models import User, get_db, DocumentUpload
from services.auth_service import get_current_active_user
from services.openai_service import LLMService
from config import settings
from langchain_core.messages import SystemMessage, HumanMessage
from prompt_registry import *
from services.aws_service import FileHandler
from services.celery_service import celery_app, pdf_processing_task
from services.redis_service import RedisService

logger = logging.getLogger(__name__)

try:
    from services.pdf_service import MistralPDFExtractor
except ImportError as e:
    logger.warning(f"Could not import MistralPDFExtractor: {e}")
    MistralPDFExtractor = None
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

router = APIRouter(prefix="/agent", tags=["Mental Health Agent"])

# Initialize file handler
file_handler = FileHandler()    

# Initialize services
llm_service = LLMService()

@router.post("/analyze-document")
async def analyze_medical_doc(
    file: UploadFile = File(...),   
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Analyze a medical document using AI.
    """

    try:
        logger.info(f"User {current_user.id} initiated document analysis for file: {file.filename}")

        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            logger.warning(f"File upload rejected: {file.filename} is not a PDF")
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        if file.content_type != 'application/pdf':
            logger.warning(f"File upload rejected: {file.filename} has invalid content type {file.content_type}")
            raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are allowed")
        
        # Get file size before upload
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        # Upload the PDF document to the S3 bucket
        logger.info(f"Uploading file {file.filename} to S3")
        s3_result = file_handler.save_pdf_to_s3(file)
        
        if not s3_result["success"]:
            logger.error(f"Failed to upload PDF to S3 for file {file.filename}")
            raise HTTPException(status_code=500, detail="Failed to upload PDF to S3")

        logger.info(f"File {file.filename} uploaded to S3 at {s3_result['s3_key']}")

        # Save the document upload to the database (partial insertion)
        document_upload = DocumentUpload(
            user_id=current_user.id,
            original_filename=s3_result["original_filename"],
            s3_file_path=s3_result["s3_key"],
            file_size=file_size,
            extraction_status="pending"  # Initial status
        )
        db.add(document_upload)
        db.commit()
        db.refresh(document_upload) 
        logger.info(f"Document upload record created for user {current_user.id}, file {s3_result['original_filename']} with ID {document_upload.id}")

        # Generate unique task ID for Redis tracking
        task_id = f"pdf_processing_{document_upload.id}_{str(uuid.uuid4())[:8]}"
        
        # Delegate PDF processing to Celery task
        logger.info(f"Delegating PDF processing to Celery for document {document_upload.id} with task_id {task_id}")
        try:
            task = pdf_processing_task.apply_async(
                args=[document_upload.id, s3_result["s3_key"], current_user.id, task_id],
                task_id=task_id
            )
            logger.info(f"PDF processing task queued with task ID: {task.id}")
        except Exception as e:
            logger.error(f"Failed to queue PDF processing task: {e}")
            # Update document status to failed
            document_upload.extraction_status = "failed"
            document_upload.processing_error = f"Failed to queue processing task: {str(e)}"
            db.commit()
            raise HTTPException(status_code=500, detail="Failed to queue PDF processing task")

        logger.info(f"Document upload initiated successfully for user {current_user.id}, file {file.filename}")
        return {
            "message": "PDF uploaded successfully and processing started",
            "file_id": s3_result["file_id"],
            "s3_key": s3_result["s3_key"],
            "s3_url": s3_result["s3_url"],
            "original_filename": s3_result["original_filename"],
            "document_id": document_upload.id,
            "processing_status": "pending",
            "task_id": task_id,
            "stream_url": f"/agent/stream-status/{task_id}",
            "status_url": f"/agent/task-status/{task_id}"
        }
        
    except Exception as e:
        logger.error(f"Error processing PDF for user {getattr(current_user, 'id', 'unknown')}, file {getattr(file, 'filename', 'unknown')}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@router.get("/documents")
async def get_user_documents(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all uploaded documents for the current user.
    """
    try:
        logger.info(f"Retrieving documents for user {current_user.id}")

        # Query all document uploads for the current user
        documents = db.query(DocumentUpload).filter(
            DocumentUpload.user_id == current_user.id
        ).order_by(DocumentUpload.created_at.desc()).all()
        
        logger.info(f"Found {len(documents)} documents for user {current_user.id}")

        # Convert to response format
        document_list = []
        for doc in documents:
            logger.debug(f"Processing document id {doc.id} for user {current_user.id}")
            document_list.append({
                "id": doc.id,
                "original_filename": doc.original_filename,
                "s3_file_path": doc.s3_file_path,
                "file_size": doc.file_size,
                "extraction_status": doc.extraction_status,
                "processing_started_at": doc.processing_started_at.isoformat() if doc.processing_started_at else None,
                "processing_completed_at": doc.processing_completed_at.isoformat() if doc.processing_completed_at else None,
                "processing_error": doc.processing_error,
                "created_at": doc.created_at.isoformat(),
                "updated_at": doc.updated_at.isoformat(),
                "extracted_text": doc.extracted_text[:500] + "..." if doc.extracted_text and len(doc.extracted_text) > 500 else doc.extracted_text  # Truncate for list view
            })
        
        logger.info(f"Documents for user {current_user.id} retrieved successfully")
        return {
            "message": "Documents retrieved successfully",
            "total_documents": len(document_list),
            "documents": document_list
        }
        
    except Exception as e:
        logger.error(f"Error retrieving documents for user {getattr(current_user, 'id', 'unknown')}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving documents: {str(e)}")


@router.get("/stream-status/{task_id}")
async def stream_processing_status(task_id: str):
    """SSE endpoint to stream processing status from Redis"""
    async def event_generator():
        redis_service = RedisService()
        last_progress = -1
        last_stage = None
        
        while True:
            try:
                # Get current status from Redis
                status = redis_service.get_task_status(task_id)
                
                if not status:
                    # Task might not exist or Redis key expired
                    yield f"data: {json.dumps({'error': 'Task not found or expired', 'task_id': task_id})}\n\n"
                    break
                
                # Only send update if progress or stage changed
                current_progress = status.get('progress', 0)
                current_stage = status.get('stage', '')
                
                if current_progress != last_progress or current_stage != last_stage:
                    yield f"data: {json.dumps(status)}\n\n"
                    last_progress = current_progress
                    last_stage = current_stage
                
                # Check if processing is complete
                if status.get('stage') in ['completed', 'failed']:
                    # Send final update and close connection
                    yield f"data: {json.dumps(status)}\n\n"
                    break
                
                # Wait before checking again
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in SSE stream for task {task_id}: {e}")
                yield f"data: {json.dumps({'error': 'Stream error', 'message': str(e)})}\n\n"
                break
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """Get current processing status from Redis"""
    try:
        redis_service = RedisService()
        status = redis_service.get_task_status(task_id)
        
        if not status:
            # Also check Celery's result backend
            try:
                task_result = celery_app.AsyncResult(task_id)
                if task_result.ready():
                    if task_result.successful():
                        status = task_result.result
                    else:
                        status = {"error": "Task failed", "traceback": str(task_result.traceback)}
            except:
                pass
            
            if not status:
                raise HTTPException(status_code=404, detail="Task ID not found")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving task status for task {task_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving task status: {str(e)}")

@router.get("/task-info/{task_id}")
async def get_celery_task_info(task_id: str):
    """Get detailed Celery task information"""
    try:
        task_result = celery_app.AsyncResult(task_id)
        
        info = {
            "task_id": task_id,
            "status": task_result.status,
            "ready": task_result.ready(),
            "successful": task_result.successful(),
            "failed": task_result.failed(),
            "state": task_result.state
        }
        
        if task_result.ready():
            if task_result.successful():
                info["result"] = task_result.result
            else:
                info["error"] = str(task_result.result)
                info["traceback"] = str(task_result.traceback)
        
        return info
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Task not found: {str(e)}")

