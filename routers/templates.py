import sys
import os
import json
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
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


def fill_pdf_templates(json_result, group_id, templates, db_session):
    """
    Fill PDF templates with extracted data using PyMuPDF (fitz).
    
    Args:
        json_result: Dictionary containing extracted patient data
        group_id: Unique identifier for the document group
        templates: List of template objects from database
        db_session: Database session for creating GeneratedDocument entries
    
    Returns:
        List of dictionaries containing S3 information for generated documents
    """
    try:
        import tempfile
        
        # Generate PDFs for requested templates
        generated_documents = []            
        for temp in templates:
            try:
                logger.info(f"Processing template: {temp.name}")
                logger.info(f"Template S3 path: {temp.s3_path}")
                
                # Download PDF template from S3 using the dedicated function
                temp_pdf_path = file_handler.download_pdf_template_from_s3(temp.s3_path)
                logger.info(f"Downloaded template PDF from S3 to: {temp_pdf_path}")
                
                # Create output path for filled PDF
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as output_file:
                    output_pdf_path = output_file.name
                
                # Function mapping
                logger.info(f"Template name: '{temp.name}' - checking for template type")
                try:
                    if "purewick" in temp.name.lower():
                        logger.info("Using Purewick resupply agreement filling function")
                        filled_pdf_path = pdf_processor.fill_purewick_resupply_agreement(
                            temp_pdf_path, 
                            json_result, 
                            output_pdf_path
                        )
                    elif "non medicare" in temp.name.lower():
                        logger.info("Using Non Medicare DME intake form filling function")
                        filled_pdf_path = pdf_processor.fill_non_medicare_dme_intake_form(
                            temp_pdf_path, 
                            json_result, 
                            output_pdf_path
                        )
                    else:
                        logger.info("Using comprehensive PDF filling function")
                        # Use the comprehensive filling function for all other templates
                        filled_pdf_path = pdf_processor.fill_comprehensive_pdf_template(
                            temp_pdf_path, 
                            json_result, 
                            output_pdf_path
                        )
                    logger.info(f"Successfully filled PDF: {filled_pdf_path}")
                except Exception as e:
                    logger.error(f"Error filling PDF template {temp.name}: {e}")
                    continue
                
                # Upload filled PDF to S3 and create database entry
                try:
                    # Upload to S3
                    upload_result = file_handler.upload_generated_pdf_to_s3(
                        filled_pdf_path, group_id, temp.name
                    )
                    
                    # Create database entry if db_session is provided
                    if db_session:
                        generated_doc = GeneratedDocument(
                            document_group_id=group_id,
                            document_type=f"filled_{temp.name.lower().replace(' ', '_')}",
                            s3_path=upload_result["s3_key"],
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )
                        db_session.add(generated_doc)
                        db_session.commit()
                        db_session.refresh(generated_doc)
                        
                        logger.info(f"Created database entry for generated document: {generated_doc.id}")
                    
                    logger.info(f"Successfully uploaded filled PDF to S3: {upload_result['s3_url']}")
                    
                    # Add to results with S3 information
                    generated_documents.append({
                        "template_name": temp.name,
                        "s3_key": upload_result["s3_key"],
                        "s3_url": upload_result["s3_url"],
                        "file_id": upload_result["file_id"]
                    })
                    
                except Exception as e:
                    logger.error(f"Error uploading filled PDF to S3 or creating database entry: {e}")
                    # Continue with other PDFs even if one fails
                    
            except Exception as e:
                logger.error(f"Error processing template {temp.name}: {e}")
                # Continue with other templates even if one fails
                continue
                
            finally:
                # Clean up temporary files
                try:
                    if temp_pdf_path and os.path.exists(temp_pdf_path):
                        os.unlink(temp_pdf_path)
                    if 'output_pdf_path' in locals() and output_pdf_path and os.path.exists(output_pdf_path):
                        os.unlink(output_pdf_path)
                except Exception as e:
                    logger.warning(f"Could not delete temporary files: {e}")
        
        return generated_documents
        
    except Exception as e:
        logger.error(f"Error filling PDF templates: {e}")
        raise e


@router.get("/")
async def get_templates(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all available templates.
    
    Returns:
        List of templates with id, name, description, and category
    """
    try:
        logger.info(f"Retrieving templates for user {current_user.id}")
        
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
        
        logger.info(f"Retrieved {len(template_list)} templates for user {current_user.id}")
        return {
            "message": "Templates retrieved successfully",
            "total_templates": len(template_list),
            "templates": template_list
        }
        
    except Exception as e:
        logger.error(f"Error retrieving templates for user {getattr(current_user, 'id', 'unknown')}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving templates: {str(e)}")


@router.post("/generate-document/")
async def generate_document(
    request: GenerateDocumentRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
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
        generated_documents = fill_pdf_templates(json_result, group_id, valid_templates, db)

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
    db: Session = Depends(get_db)
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
