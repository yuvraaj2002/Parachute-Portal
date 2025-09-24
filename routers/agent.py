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
from services.celery_service import celery_app, pdf_processing_task, multi_pdf_processing_task
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
    files: list[UploadFile] = File(...),   
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Analyze one or more medical documents using AI.
    Supports 1-8 PDF files at a time.
    """

    try:
        # Validate number of files
        if len(files) == 0:
            raise HTTPException(status_code=400, detail="At least one file is required")
        
        if len(files) > 8:
            raise HTTPException(status_code=400, detail="Maximum 8 documents allowed per request")
        
        logger.info(f"User {current_user.id} initiated document analysis for {len(files)} files")

        # Generate a unique group ID for this batch of documents
        group_id = str(uuid.uuid4())
        
        # Validate all files first
        validated_files = []
        for file in files:
            # Validate file type
            if not file.filename.lower().endswith('.pdf'):
                logger.warning(f"File upload rejected: {file.filename} is not a PDF")
                raise HTTPException(status_code=400, detail=f"Only PDF files are allowed. {file.filename} is not a PDF")
            
            if file.content_type != 'application/pdf':
                logger.warning(f"File upload rejected: {file.filename} has invalid content type {file.content_type}")
                raise HTTPException(status_code=400, detail=f"Invalid file type. Only PDF files are allowed. {file.filename} has invalid content type")
            
            # Get file size
            file.file.seek(0, 2)  # Seek to end
            file_size = file.file.tell()
            file.file.seek(0)  # Reset to beginning
            
            validated_files.append({
                'file': file,
                'size': file_size
            })

        # Upload all files to S3 and create database records
        uploaded_documents = []
        s3_results = []
        
        for i, file_data in enumerate(validated_files):
            file = file_data['file']
            file_size = file_data['size']
            
            logger.info(f"Uploading file {i+1}/{len(validated_files)}: {file.filename} to S3")
            s3_result = file_handler.save_pdf_to_s3(file)
            
            if not s3_result["success"]:
                logger.error(f"Failed to upload PDF to S3 for file {file.filename}")
                raise HTTPException(status_code=500, detail=f"Failed to upload PDF to S3: {file.filename}")

            logger.info(f"File {file.filename} uploaded to S3 at {s3_result['s3_key']}")

            # Save the document upload to the database
            document_upload = DocumentUpload(
                user_id=current_user.id,
                document_group_id=group_id,  # Group all documents together
                original_filename=s3_result["original_filename"],
                s3_file_path=s3_result["s3_key"],
                file_size=file_size,
                extraction_status="pending"  # Initial status
            )
            db.add(document_upload)
            db.commit()
            db.refresh(document_upload)
            
            uploaded_documents.append(document_upload)
            s3_results.append(s3_result)
            
            logger.info(f"Document upload record created for user {current_user.id}, file {s3_result['original_filename']} with ID {document_upload.id}")

        # Generate unique task ID for Redis tracking
        task_id = f"multi_pdf_processing_{group_id}_{str(uuid.uuid4())[:8]}"
        
        # Delegate multi-document processing to Celery task
        logger.info(f"Delegating multi-document processing to Celery for group {group_id} with task_id {task_id}")
        try:
            # Create list of document IDs and S3 keys for the task
            document_ids = [doc.id for doc in uploaded_documents]
            s3_keys = [result["s3_key"] for result in s3_results]
            
            task = multi_pdf_processing_task.apply_async(
                args=[document_ids, s3_keys, current_user.id, task_id, group_id],
                task_id=task_id
            )
            logger.info(f"Multi-document processing task queued with task ID: {task.id}")
        except Exception as e:
            logger.error(f"Failed to queue multi-document processing task: {e}")
            # Update all document statuses to failed
            for doc in uploaded_documents:
                doc.extraction_status = "failed"
                doc.processing_error = f"Failed to queue processing task: {str(e)}"
            db.commit()
            raise HTTPException(status_code=500, detail="Failed to queue multi-document processing task")

        logger.info(f"Multi-document upload initiated successfully for user {current_user.id}, {len(files)} files")
        return {
            "message": f"{len(files)} PDF(s) uploaded successfully and processing started",
            "group_id": group_id,
            "total_documents": len(uploaded_documents),
            "documents": [
                {
                    "document_id": doc.id,
                    "original_filename": doc.original_filename,
                    "s3_key": s3_results[i]["s3_key"],
                    "s3_url": s3_results[i]["s3_url"],
                    "file_size": doc.file_size
                }
                for i, doc in enumerate(uploaded_documents)
            ],
            "processing_status": "pending",
            "task_id": task_id,
            "stream_url": f"/agent/stream-status/{task_id}",
            "status_url": f"/agent/task-status/{task_id}"
        }
        
    except Exception as e:
        logger.error(f"Error processing PDFs for user {getattr(current_user, 'id', 'unknown')}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing PDFs: {str(e)}")

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

@router.get("/document-groups")
async def get_user_document_groups(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all document groups for the current user.
    """
    try:
        logger.info(f"Retrieving document groups for user {current_user.id}")

        # Query all document groups for the current user
        # Group by document_group_id and get unique groups
        from sqlalchemy import func, distinct
        
        # Get unique group IDs for this user
        group_ids = db.query(distinct(DocumentUpload.document_group_id)).filter(
            DocumentUpload.user_id == current_user.id,
            DocumentUpload.document_group_id.isnot(None)
        ).all()
        
        group_ids = [g[0] for g in group_ids if g[0]]  # Extract from tuples and filter None
        
        logger.info(f"Found {len(group_ids)} document groups for user {current_user.id}")

        # Get details for each group
        document_groups = []
        for group_id in group_ids:
            # Get all documents in this group
            documents = db.query(DocumentUpload).filter(
                DocumentUpload.user_id == current_user.id,
                DocumentUpload.document_group_id == group_id
            ).order_by(DocumentUpload.created_at.asc()).all()
            
            if documents:
                # Calculate group statistics
                total_docs = len(documents)
                completed_docs = len([d for d in documents if d.extraction_status == "completed"])
                failed_docs = len([d for d in documents if d.extraction_status == "failed"])
                processing_docs = len([d for d in documents if d.extraction_status == "processing"])
                pending_docs = len([d for d in documents if d.extraction_status == "pending"])
                
                # Determine overall group status
                if failed_docs > 0:
                    group_status = "failed"
                elif processing_docs > 0 or pending_docs > 0:
                    group_status = "processing"
                elif completed_docs == total_docs:
                    group_status = "completed"
                else:
                    group_status = "pending"
                
                # Get merged JSON result if all documents are completed
                merged_json_result = None
                if completed_docs == total_docs:
                    # The merged JSON result is stored in the first document's extracted_text field
                    first_doc = documents[0]
                    if first_doc.extracted_text:
                        # Check if it's JSON (merged result) or just OCR text
                        try:
                            import json
                            json.loads(first_doc.extracted_text)
                            merged_json_result = first_doc.extracted_text
                        except json.JSONDecodeError:
                            # It's OCR text, not merged JSON - create combined text
                            merged_json_result = "\n\n".join([
                                f"=== {doc.original_filename} ===\n{doc.extracted_text}"
                                for doc in documents if doc.extracted_text
                            ])
                
                document_groups.append({
                    "group_id": group_id,
                    "total_documents": total_docs,
                    "completed_documents": completed_docs,
                    "failed_documents": failed_docs,
                    "processing_documents": processing_docs,
                    "pending_documents": pending_docs,
                    "group_status": group_status,
                    "created_at": documents[0].created_at.isoformat(),
                    "updated_at": max([d.updated_at for d in documents]).isoformat(),
                    "documents": [
                        {
                            "id": doc.id,
                            "original_filename": doc.original_filename,
                            "s3_file_path": doc.s3_file_path,
                            "file_size": doc.file_size,
                            "extraction_status": doc.extraction_status,
                            "processing_started_at": doc.processing_started_at.isoformat() if doc.processing_started_at else None,
                            "processing_completed_at": doc.processing_completed_at.isoformat() if doc.processing_completed_at else None,
                            "processing_error": doc.processing_error,
                            "created_at": doc.created_at.isoformat(),
                            "extracted_text": doc.extracted_text[:500] + "..." if doc.extracted_text and len(doc.extracted_text) > 500 else doc.extracted_text
                        }
                        for doc in documents
                    ],
                    "merged_json_result": merged_json_result[:1000] + "..." if merged_json_result and len(merged_json_result) > 1000 else merged_json_result
                })
        
        # Sort by creation date (newest first)
        document_groups.sort(key=lambda x: x["created_at"], reverse=True)
        
        logger.info(f"Document groups for user {current_user.id} retrieved successfully")
        return {
            "message": "Document groups retrieved successfully",
            "total_groups": len(document_groups),
            "document_groups": document_groups
        }
        
    except Exception as e:
        logger.error(f"Error retrieving document groups for user {getattr(current_user, 'id', 'unknown')}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving document groups: {str(e)}")

@router.get("/document-group/{group_id}/merged-result")
async def get_merged_json_result(
    group_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get the full merged JSON result for a specific document group.
    """
    try:
        logger.info(f"Retrieving merged JSON result for group {group_id} for user {current_user.id}")

        # Get all documents in this group
        documents = db.query(DocumentUpload).filter(
            DocumentUpload.user_id == current_user.id,
            DocumentUpload.document_group_id == group_id
        ).order_by(DocumentUpload.created_at.asc()).all()
        
        if not documents:
            raise HTTPException(status_code=404, detail="Document group not found")
        
        # Check if all documents are completed
        completed_docs = len([d for d in documents if d.extraction_status == "completed"])
        total_docs = len(documents)
        
        if completed_docs != total_docs:
            raise HTTPException(
                status_code=400, 
                detail=f"Document group processing not complete. {completed_docs}/{total_docs} documents processed."
            )
        
        # Find the document that contains the merged JSON result
        # The merged JSON is stored in the extracted_text field of the first completed document
        merged_doc = None
        for doc in documents:
            if doc.extracted_text:
                try:
                    import json
                    # Try to parse as JSON - if successful, this is our merged result
                    json.loads(doc.extracted_text)
                    merged_doc = doc
                    break
                except json.JSONDecodeError:
                    # This is OCR text, not merged JSON, continue looking
                    continue
        
        if not merged_doc:
            raise HTTPException(status_code=404, detail="No merged JSON result available")
        
        # Parse and return the merged JSON
        import json
        merged_json = json.loads(merged_doc.extracted_text)
        logger.info(f"Merged JSON result retrieved for group {group_id} from document {merged_doc.id}")
        return {
            "message": "Merged JSON result retrieved successfully",
            "group_id": group_id,
            "total_documents": total_docs,
            "merged_json": merged_json
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving merged JSON result for group {group_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving merged JSON result: {str(e)}")

@router.get("/stream-status/{task_id}")
async def stream_processing_status(task_id: str):
    """SSE endpoint to stream processing status from Redis"""
    async def event_generator():
        redis_service = RedisService()
        last_progress = -1
        last_stage = None
        retry_count = 0
        max_retries = 10  # Wait up to 10 seconds for task to appear
        
        while True:
            try:
                # Get current status from Redis
                status = redis_service.get_task_status(task_id)
                
                if not status:
                    retry_count += 1
                    if retry_count <= max_retries:
                        # Wait a bit for the task to start and set initial status
                        await asyncio.sleep(1)
                        continue
                    else:
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

