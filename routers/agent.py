import sys
import os
import json
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime, UTC
from pydantic import BaseModel

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

        # Load PDF from S3 and get decrypted file path
        decrypted_pdf_path = file_handler.load_pdf_from_s3(s3_result["s3_key"])
        logger.info(f"Loaded and decrypted PDF from S3: {decrypted_pdf_path}")
        
        # Extracting the Markdown from the PDF using Mistral AI
        logger.info(f"Extracting text from PDF using MistralPDFExtractor for file: {decrypted_pdf_path}")
        if MistralPDFExtractor is None:
            logger.error("MistralPDFExtractor is not available. Please install mistralai package and set mistral_api_key")
            raise HTTPException(status_code=500, detail="PDF extraction service not available")
        
        try:
            ocr_response = MistralPDFExtractor().extract_text_from_pdf(decrypted_pdf_path)
            # Extract markdown content from OCR response
            markdown_content = ""
            if hasattr(ocr_response, 'pages') and ocr_response.pages:
                for page in ocr_response.pages:
                    if hasattr(page, 'markdown'):
                        markdown_content += page.markdown + "\n\n"
            else:
                # Fallback if response structure is different
                markdown_content = str(ocr_response)
        except Exception as e:
            logger.error(f"Error during PDF extraction: {e}")
            raise HTTPException(status_code=500, detail=f"PDF extraction failed: {str(e)}")
        
        # Save the document upload to the database
        document_upload = DocumentUpload(
            user_id=current_user.id,
            original_filename=s3_result["original_filename"],
            s3_file_path=s3_result["s3_key"],
            file_size=file_size
        )
        
        # Data extraction using LLM
        logger.info(f"Processing extracted text with LLM for user {current_user.id}")
        document_upload.processing_started_at = datetime.now(UTC)
        data = await llm_service.process_medical_document(markdown_content)
        # Saving the extracted data to the database
        document_upload.extracted_text = data
        document_upload.extraction_status = "completed"
        document_upload.processing_completed_at = datetime.now(UTC)
        db.add(document_upload)
        db.commit()
        logger.info(f"Document upload record created for user {current_user.id}, file {s3_result['original_filename']}")

        logger.info(f"Document analysis completed successfully for user {current_user.id}, file {file.filename}")
        return {
            "message": "PDF uploaded successfully",
            "file_id": s3_result["file_id"],
            "s3_key": s3_result["s3_key"],
            "s3_url": s3_result["s3_url"],
            "original_filename": s3_result["original_filename"],
            "extracted_data" : data
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

