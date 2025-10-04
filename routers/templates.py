import sys
import os
import json
import logging
from typing import List
from rich import print
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime

# Add project root to path for imports
ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_PATH not in sys.path:
    sys.path.append(ROOT_PATH)

from models.database_models import User, get_db, DocumentUpload, Templates, GeneratedDocument
from models.pydantic_models.document_pydantic_models import GenerateDocumentRequest
from services.auth_service import get_current_active_user
from services.openai_service import LLMService
from services.pdf_service import PdfProcessor
from services.aws_service import file_handler
from services.redis_service import RedisService
from services.db_service import DatabaseService

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

router = APIRouter(prefix="/templates", tags=["Templates"])
openai_service = LLMService()
pdf_processor = PdfProcessor()
redis_service = RedisService()


@router.get("/")
async def get_templates(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Get all available templates.
    
    Returns:
        List of templates with id, name, description, and category
    """
    try:

        # Checking if the data exists in the cache
        cache_key = "templates"
        cached_data = redis_service.get_key(cache_key)
        if cached_data:
            logger.info("Returning the data from cache")
            return json.loads(cached_data)
        
        logger.info(f"Retrieving templates")
        
        # Query all templates
        templates = db.query(Templates).all()
        
        # Format response
        template_list = []
        for template in templates:
            template_list.append({
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "category": template.category
            })
        
        logger.info(f"Retrieved {len(template_list)} templates")

        # Prepare the complete response
        response_data = {
            "message": "Templates retrieved successfully",
            "total_templates": len(template_list),
            "templates": template_list
        }

        # Storing the complete response in cache
        logger.info("Storing the complete response data in cache")
        redis_service.set_key(cache_key, json.dumps(response_data), expire_seconds=600)
        
        # Create audit log for templates access
        DatabaseService.create_audit_log(
            db=db,
            user_id=current_user.id,
            category="data_access",
            action_details=f"User {current_user.email} accessed templates list ({len(template_list)} templates)",
            resource_type="templates",
            request=request
        )
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error retrieving templates: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving templates: {str(e)}")


@router.post("/generate-document/")
async def generate_document(
    request: GenerateDocumentRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    http_request: Request = None
):
    """
    Generate PDF documents from templates using extracted patient data.
    
    Args:
        request: Request body containing group_id and template_ids list
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        List of generated PDF file paths and download URLs
    """
    try:
        group_id = request.group_id
        logger.info(f"Generating document for group {group_id} for user {current_user.id}")

        # Get the document group
        documents = db.query(DocumentUpload).filter(
            DocumentUpload.document_group_id == group_id,
            DocumentUpload.user_id == current_user.id
        ).all()
        
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

        # Merging the jsons for all the docs
        doc_jsons = []
        for doc in documents:
            if doc.extracted_text:
                try:
                    # Try to parse as JSON - if successful, this is our merged result
                    json.loads(doc.extracted_text)
                    doc_jsons.append(doc.extracted_text)
                    break
                except json.JSONDecodeError:
                    # This is OCR text, not merged JSON, continue looking
                    continue
        
        if not doc_jsons:
            raise HTTPException(status_code=404, detail="No merged JSON result available")
        
        # Get the merged JSON using merge_json_responses from openai_service
        json_result = openai_service.merge_json_responses(doc_jsons)
        json_result = json.loads(json_result)
        print(json_result)

        # Fetch templates from database and then using the s3 paths to get PDFs from the s3 bucket
        templates = db.query(Templates).filter(
            Templates.id.in_(request.template_ids)
        ).all()
        
        if not templates:
            raise HTTPException(status_code=404, detail="No templates found with the provided IDs")
        
        # Filter templates that have S3 paths (required for PDF loading)
        valid_templates = [t for t in templates if t.s3_path]
        
        if not valid_templates:
            raise HTTPException(
                status_code=400, 
                detail="No valid templates found. Templates must have s3_path set."
            )
        
        logger.info(f"Processing {len(valid_templates)} valid PDF templates out of {len(templates)} requested")
        
        # Initialize PDF processor and fill PDFs using PyMuPDF
        generated_documents = pdf_processor.fill_pdf_templates(json_result, group_id, valid_templates, db)

        # Prepare response with S3 file information
        pdf_files = []
        for doc_info in generated_documents:
            pdf_files.append({
                "template_name": doc_info["template_name"],
                "s3_key": doc_info["s3_key"],
                "s3_url": doc_info["s3_url"],
                "file_id": doc_info["file_id"],
                "download_url": f"/templates/download-document/{doc_info['file_id']}",
                "preview_url": f"/templates/preview-document/{doc_info['file_id']}"
            })

        logger.info(f"Successfully generated {len(pdf_files)} PDFs for group {group_id}")
        
        # Create audit log for document generation
        DatabaseService.create_audit_log(
            db=db,
            user_id=current_user.id,
            category="document_processing",
            action_details=f"User {current_user.email} generated {len(pdf_files)} PDF documents from {len(request.template_ids)} templates for group {group_id}. Templates: {request.template_ids}",
            resource_type="document_generation",
            request=http_request
        )
        
        return {
            "message": f"Successfully generated {len(pdf_files)} PDF documents",
            "group_id": group_id,
            "generated_pdfs": pdf_files,
            "total_files": len(pdf_files)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating document for group {group_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating document: {e}")


@router.get("/download-document/{file_id}")
async def download_document(
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Download a generated PDF file from S3.
    
    Args:
        file_id: Generated document file ID
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        PDF file as streaming response from S3
    """
    try:
        from models.database_models import GeneratedDocument
        from services.aws_service import file_handler
        
        # Find the generated document by file_id (extracted from s3_key)
        generated_doc = db.query(GeneratedDocument).filter(
            GeneratedDocument.s3_path.like(f"%{file_id}%")
        ).first()
        
        if not generated_doc:
            raise HTTPException(status_code=404, detail="Generated document not found")
        
        # Verify the user has access to this document group
        documents = db.query(DocumentUpload).filter(
            DocumentUpload.document_group_id == generated_doc.document_group_id,
            DocumentUpload.user_id == current_user.id
        ).first()
        
        if not documents:
            raise HTTPException(status_code=404, detail="Document group not found or access denied")
        
        # Download file from S3
        try:
            # Create a temporary file to store the PDF
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Download from S3
            file_handler.s3_client.download_file(
                file_handler.bucket_name,
                generated_doc.s3_path,
                temp_path
            )
            
            # Return the file as a streaming response
            def iterfile():
                try:
                    with open(temp_path, mode="rb") as file_like:
                        yield from file_like
                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(temp_path)
                    except Exception:
                        pass
            
            # Extract filename from s3_path for download
            filename = os.path.basename(generated_doc.s3_path)
            
            # Create audit log for document download
            DatabaseService.create_audit_log(
                db=db,
                user_id=current_user.id,
                category="file_operations",
                action_details=f"User {current_user.email} downloaded generated PDF document: {filename} (file_id: {file_id})",
                resource_type="document_download",
                request=request
            )
            
            return StreamingResponse(
                iterfile(),
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
            
        except Exception as e:
            logger.error(f"Error downloading PDF from S3: {e}")
            raise HTTPException(status_code=500, detail="Error downloading PDF from S3")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading PDF {file_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error downloading PDF: {e}")


@router.get("/preview-document/{file_id}")
async def preview_document(
    file_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Preview a generated PDF file from S3 in the browser.
    
    Args:
        file_id: Generated document file ID
        current_user: Current authenticated user
        db: Database session
    
    Returns:
        PDF file as streaming response for browser preview (inline display)
    """
    try:
        from models.database_models import GeneratedDocument
        from services.aws_service import file_handler
        
        # Find the generated document by file_id (extracted from s3_key)
        generated_doc = db.query(GeneratedDocument).filter(
            GeneratedDocument.s3_path.like(f"%{file_id}%")
        ).first()
        
        if not generated_doc:
            raise HTTPException(status_code=404, detail="Generated document not found")
        
        # Verify the user has access to this document group
        documents = db.query(DocumentUpload).filter(
            DocumentUpload.document_group_id == generated_doc.document_group_id,
            DocumentUpload.user_id == current_user.id
        ).first()
        
        if not documents:
            raise HTTPException(status_code=404, detail="Document group not found or access denied")
        
        # Download file from S3
        try:
            # Create a temporary file to store the PDF
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Download from S3
            file_handler.s3_client.download_file(
                file_handler.bucket_name,
                generated_doc.s3_path,
                temp_path
            )
            
            # Return the file as a streaming response for inline preview
            def iterfile():
                try:
                    with open(temp_path, mode="rb") as file_like:
                        yield from file_like
                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(temp_path)
                    except Exception:
                        pass
            
            # Extract filename from s3_path for display
            filename = os.path.basename(generated_doc.s3_path)
            
            return StreamingResponse(
                iterfile(),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"inline; filename={filename}",
                    "Content-Security-Policy": "default-src 'self'",
                    "X-Content-Type-Options": "nosniff",
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
            )
            
        except Exception as e:
            logger.error(f"Error previewing PDF from S3: {e}")
            raise HTTPException(status_code=500, detail="Error previewing PDF from S3")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing PDF {file_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error previewing PDF: {e}")
