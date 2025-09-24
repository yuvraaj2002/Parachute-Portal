import logging
import requests
import sys
import os
from celery import Celery
from config import settings

# Add the backend directory to the Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Configure logging
logger = logging.getLogger(__name__)

# Create Celery instance with optimized connection pooling
# Target: 1 worker × 2 processes × 10 connections = 20 total connections for Celery
celery_app = Celery(
    'parachute_portal',
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=['services.celery_service'] # Module containing task definitions
)

# Enhanced Celery configuration with optimized connection pooling
# Each worker process gets 10 connections (5 for broker + 5 for result backend)
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    
    # Redis broker configuration
    broker_connection_retry=True,  # Retry if connection is lost
    broker_connection_max_retries=10,
    broker_pool_limit=10,  # Increased broker connections
    broker_connection_retry_on_timeout=True,
    broker_connection_retry_delay=0.2,
    broker_connection_retry_max_delay=10.0,
    broker_connection_timeout=30,

    # Broker transport options for better Redis handling
    broker_transport_options={
        'visibility_timeout': 3600,  # 1 hour
        'retry_policy': {
            'timeout': 5.0,
            'max_retries': 3
        },
        'socket_connect_timeout': 30,
        'socket_timeout': 30,
        'retry_on_timeout': True,
        'max_connections': 10,
        'health_check_interval': 30
    },

    # Result backend configuration
    result_backend_transport_options={
        'socket_connect_timeout': 30,
        'socket_timeout': 30,
        'retry_on_timeout': True,
        'max_connections': 10,  # Increased backend connections
        'health_check_interval': 30,
        'connection_retry_on_timeout': True,
        'connection_retry_delay': 0.2,
        'connection_retry_max_delay': 10.0
    },
    
    # Worker configuration - UPDATED FOR 20-CONNECTION BUDGET
    worker_concurrency=2,  # 2 worker processes = 20 total connections
    worker_prefetch_multiplier=1, # Fair task distribution
    worker_max_tasks_per_child=200, # Memory management
    
    # Connection pool optimizations
    broker_connection_pool_limit=5,  # 5 connections for broker pool
    result_backend_connection_pool_limit=5,  # 5 connections for result backend pool
    
    # Task routing and queue management
    task_default_queue='default',
    task_queues={
        'default': {
            'exchange': 'default',
            'routing_key': 'default',
        }
    }
)


@celery_app.task(bind=True, name='pdf_processing')
def pdf_processing_task(self, document_id: int, s3_key: str, user_id: int, task_id: str = None):
    """
    Celery task to process a PDF file asynchronously with Redis status tracking.
    """
    # Use provided task_id or generate one
    if not task_id:
        task_id = self.request.id
    else:
        # Use the provided task_id for Redis tracking
        task_id = task_id
    
    try:
        logger.info(f"Processing PDF file from S3: {s3_key} for document_id: {document_id}, task_id: {task_id}")
        
        # Import here to avoid circular imports
        from models.database_models import get_db, DocumentUpload
        from services.aws_service import FileHandler
        from services.openai_service import LLMService
        from services.redis_service import RedisService
        from datetime import datetime, UTC
        
        # Initialize services
        file_handler = FileHandler()
        llm_service = LLMService()
        redis_service = RedisService()
        
        # Set initial status in Redis
        logger.info(f"Setting initial Redis status for task_id: {task_id}")
        redis_service.update_task_progress(
            task_id=task_id,
            stage="starting",
            progress=0,
            message="Initializing PDF processing task",
            data={"document_id": document_id, "user_id": user_id}
        )
        logger.info(f"Initial Redis status set for task_id: {task_id}")
        
        # Get database session
        db = next(get_db())
        
        try:
            # Update task status to processing
            document = db.query(DocumentUpload).filter(DocumentUpload.id == document_id).first()
            if not document:
                logger.error(f"Document with id {document_id} not found")
                redis_service.update_task_progress(
                    task_id=task_id,
                    stage="failed",
                    progress=0,
                    message="Document not found in database"
                )
                return {"status": "error", "message": "Document not found"}
            
            document.processing_started_at = datetime.now(UTC)
            document.extraction_status = "processing"
            db.commit()
            
            # Update Redis status - Loading PDF
            redis_service.update_task_progress(
                task_id=task_id,
                stage="loading_pdf",
                progress=20,
                message="Loading PDF from S3 storage"
            )
            
            # Load PDF from S3 and get decrypted file path
            logger.info(f"Loading and decrypting PDF from S3: {s3_key}")
            decrypted_pdf_path = file_handler.load_pdf_from_s3(s3_key)
            logger.info(f"Loaded and decrypted PDF from S3: {decrypted_pdf_path}")
            
            # Update Redis status - Extracting text
            redis_service.update_task_progress(
                task_id=task_id,
                stage="extracting_text",
                progress=40,
                message="Extracting text from PDF using AI"
            )
            
            # Extract text from PDF using Mistral AI
            logger.info(f"Extracting text from PDF using MistralPDFExtractor")
            try:
                from services.pdf_service import MistralPDFExtractor
                if MistralPDFExtractor is None:
                    raise Exception("MistralPDFExtractor is not available")
                
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
                redis_service.update_task_progress(
                    task_id=task_id,
                    stage="failed",
                    progress=40,
                    message=f"PDF extraction failed: {str(e)}"
                )
                raise Exception(f"PDF extraction failed: {str(e)}")
            
            # Update Redis status - Processing with LLM
            redis_service.update_task_progress(
                task_id=task_id,
                stage="llm_processing",
                progress=70,
                message="Processing extracted text with AI model"
            )
            
            # Process extracted text with LLM
            logger.info(f"Processing extracted text with LLM for document {document_id}")
            import asyncio
            data = asyncio.run(llm_service.process_medical_document(markdown_content))
            
            # Update Redis status - Saving results
            redis_service.update_task_progress(
                task_id=task_id,
                stage="saving_results",
                progress=90,
                message="Saving processed data to database"
            )
            
            # Update document with extracted data
            document.extracted_text = data
            document.extraction_status = "completed"
            document.processing_completed_at = datetime.now(UTC)
            db.commit()
            
            # Final status update - Completed
            redis_service.update_task_progress(
                task_id=task_id,
                stage="completed",
                progress=100,
                message="PDF processing completed successfully",
                data={"extracted_data": data}
            )
            
            logger.info(f"PDF processing completed successfully for document {document_id}")
            return {
                "status": "success", 
                "message": "PDF processing completed successfully",
                "document_id": document_id,
                "extracted_data": data
            }
            
        except Exception as e:
            # Update document with error status
            document = db.query(DocumentUpload).filter(DocumentUpload.id == document_id).first()
            if document:
                document.extraction_status = "failed"
                document.processing_error = str(e)
                document.processing_completed_at = datetime.now(UTC)
                db.commit()
            
            # Update Redis with error status
            redis_service.update_task_progress(
                task_id=task_id,
                stage="failed",
                progress=-1,
                message=f"Processing failed: {str(e)}"
            )
            
            logger.error(f"Error processing PDF for document {document_id}: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return {"status": "error", "message": str(e)}
            
        finally:
            db.close()

    except Exception as e:
        # Update Redis with critical error status
        try:
            from services.redis_service import RedisService
            redis_service = RedisService()
            redis_service.update_task_progress(
                task_id=task_id,
                stage="failed",
                progress=-1,
                message=f"Critical error in PDF processing task: {str(e)}"
            )
        except:
            pass  # Don't fail if Redis update fails
        
        logger.error(f"Error in PDF processing task: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return {"status": "error", "message": str(e)}


@celery_app.task(bind=True, name='multi_pdf_processing')
def multi_pdf_processing_task(self, document_ids: list, s3_keys: list, user_id: int, task_id: str = None, group_id: str = None):
    """
    Celery task to process multiple PDF files asynchronously with Redis status tracking.
    Processes documents sequentially and combines their text for final analysis.
    """
    # Use provided task_id or generate one
    if not task_id:
        task_id = self.request.id
    else:
        task_id = task_id
    
    try:
        logger.info(f"Processing {len(document_ids)} PDF files for group {group_id}, task_id: {task_id}")
        
        # Import here to avoid circular imports
        from models.database_models import get_db, DocumentUpload
        from services.aws_service import FileHandler
        from services.openai_service import LLMService
        from services.redis_service import RedisService
        from datetime import datetime, UTC
        
        # Initialize services
        file_handler = FileHandler()
        llm_service = LLMService()
        redis_service = RedisService()
        
        # Set initial status in Redis
        logger.info(f"Setting initial Redis status for multi-document task_id: {task_id}")
        redis_service.update_task_progress(
            task_id=task_id,
            stage="starting",
            progress=0,
            message=f"Initializing multi-document processing for {len(document_ids)} documents",
            data={"document_ids": document_ids, "user_id": user_id, "group_id": group_id}
        )
        
        # Get database session
        db = next(get_db())
        
        try:
            # Update all documents status to processing
            documents = db.query(DocumentUpload).filter(DocumentUpload.id.in_(document_ids)).all()
            if not documents:
                logger.error(f"No documents found for IDs {document_ids}")
                redis_service.update_task_progress(
                    task_id=task_id,
                    stage="failed",
                    progress=0,
                    message="No documents found in database"
                )
                return {"status": "error", "message": "No documents found"}
            
            # Update all documents to processing status
            for doc in documents:
                doc.processing_started_at = datetime.now(UTC)
                doc.extraction_status = "processing"
            db.commit()
            
            # Process each document sequentially: OCR → LLM → JSON
            all_json_responses = []
            processed_count = 0
            
            for i, (document_id, s3_key) in enumerate(zip(document_ids, s3_keys)):
                try:
                    # Calculate base progress for this document (70% total for all documents)
                    base_progress = int((i / len(document_ids)) * 70)
                    document_progress_range = int(70 / len(document_ids))  # Progress range per document
                    
                    # Update Redis status - Starting document X of Y
                    redis_service.update_task_progress(
                        task_id=task_id,
                        stage="processing_documents",
                        progress=base_progress,
                        message=f"Starting document {i+1} of {len(document_ids)}: {documents[i].original_filename}"
                    )
                    
                    # Load PDF from S3 and get decrypted file path
                    logger.info(f"Loading and decrypting PDF {i+1}/{len(document_ids)} from S3: {s3_key}")
                    
                    # Update progress - Loading PDF
                    progress = base_progress + int(document_progress_range * 0.1)  # 10% of document progress
                    redis_service.update_task_progress(
                        task_id=task_id,
                        stage="processing_documents",
                        progress=progress,
                        message=f"Loading PDF {i+1} of {len(document_ids)} from S3 storage"
                    )
                    
                    decrypted_pdf_path = file_handler.load_pdf_from_s3(s3_key)
                    logger.info(f"Loaded and decrypted PDF from S3: {decrypted_pdf_path}")
                    
                    # Update progress - Starting OCR
                    progress = base_progress + int(document_progress_range * 0.2)  # 20% of document progress
                    redis_service.update_task_progress(
                        task_id=task_id,
                        stage="processing_documents",
                        progress=progress,
                        message=f"Starting OCR extraction for document {i+1} of {len(document_ids)}"
                    )
                    
                    # Step 1: Extract text from PDF using Mistral AI (OCR)
                    logger.info(f"Step 1: OCR extraction from PDF {i+1} using MistralPDFExtractor")
                    try:
                        from services.pdf_service import MistralPDFExtractor
                        pdf_extractor = MistralPDFExtractor()
                        ocr_response = pdf_extractor.extract_text_from_pdf(decrypted_pdf_path)
                        
                        # Use OCR response directly as markdown content
                        markdown_content = str(ocr_response)
                        logger.info(f"Successfully extracted OCR text from PDF {i+1}, length: {len(markdown_content)}")
                        
                        # Update progress - OCR completed
                        progress = base_progress + int(document_progress_range * 0.5)  # 50% of document progress
                        redis_service.update_task_progress(
                            task_id=task_id,
                            stage="processing_documents",
                            progress=progress,
                            message=f"OCR extraction completed for document {i+1} of {len(document_ids)} ({len(markdown_content)} characters)"
                        )
                        
                    except Exception as e:
                        logger.error(f"Failed to extract OCR text from PDF {i+1}: {str(e)}")
                        markdown_content = f"Error extracting text from {documents[i].original_filename}: {str(e)}"
                    
                    # Clean up temporary file
                    try:
                        import os
                        os.unlink(decrypted_pdf_path)
                    except Exception as e:
                        logger.warning(f"Failed to cleanup temp file {decrypted_pdf_path}: {e}")
                    
                    # Update progress - Starting LLM processing
                    progress = base_progress + int(document_progress_range * 0.6)  # 60% of document progress
                    redis_service.update_task_progress(
                        task_id=task_id,
                        stage="processing_documents",
                        progress=progress,
                        message=f"Starting AI analysis for document {i+1} of {len(document_ids)}"
                    )
                    
                    # Step 2: Process OCR text with LLM to get JSON response
                    logger.info(f"Step 2: Processing OCR text with LLM for document {i+1}")
                    try:
                        import asyncio
                        json_response = asyncio.run(llm_service.process_medical_document(markdown_content))
                        if json_response:
                            logger.info(f"Successfully processed document {i+1} with LLM")
                            all_json_responses.append(json_response)
                            
                            # Update progress - LLM completed
                            progress = base_progress + int(document_progress_range * 0.9)  # 90% of document progress
                            redis_service.update_task_progress(
                                task_id=task_id,
                                stage="processing_documents",
                                progress=progress,
                                message=f"AI analysis completed for document {i+1} of {len(document_ids)}"
                            )
                        else:
                            logger.error(f"LLM processing failed for document {i+1}")
                            all_json_responses.append(None)
                    except Exception as e:
                        logger.error(f"Error processing document {i+1} with LLM: {str(e)}")
                        all_json_responses.append(None)
                    
                    # Update document with extracted text and JSON response
                    document = db.query(DocumentUpload).filter(DocumentUpload.id == document_id).first()
                    if document:
                        document.extracted_text = markdown_content  # Store OCR text
                        document.extraction_status = "completed"
                        document.processing_completed_at = datetime.now(UTC)
                        db.commit()
                        
                        processed_count += 1
                        logger.info(f"Successfully processed document {i+1}/{len(document_ids)}: {document.original_filename}")
                        
                        # Update progress - Document completed
                        progress = base_progress + document_progress_range  # 100% of document progress
                        redis_service.update_task_progress(
                            task_id=task_id,
                            stage="processing_documents",
                            progress=progress,
                            message=f"Document {i+1} of {len(document_ids)} completed successfully: {document.original_filename}"
                        )
                    
                except Exception as e:
                    logger.error(f"Error processing document {i+1} ({document_id}): {str(e)}")
                    # Update document status to failed
                    document = db.query(DocumentUpload).filter(DocumentUpload.id == document_id).first()
                    if document:
                        document.extraction_status = "failed"
                        document.processing_error = str(e)
                        document.processing_completed_at = datetime.now(UTC)
                        db.commit()
                    all_json_responses.append(None)
            
            # Update Redis status - Starting merge process
            redis_service.update_task_progress(
                task_id=task_id,
                stage="merging_json_responses",
                progress=75,
                message=f"Starting merge process for {processed_count} processed documents"
            )
            
            # Step 3: Merge all JSON responses
            logger.info("Step 3: Merging JSON responses from all documents")
            try:
                # Filter out None responses
                valid_json_responses = [resp for resp in all_json_responses if resp is not None]
                
                redis_service.update_task_progress(
                    task_id=task_id,
                    stage="merging_json_responses",
                    progress=80,
                    message=f"Validating {len(valid_json_responses)} JSON responses for merging"
                )
                
                if valid_json_responses:
                    redis_service.update_task_progress(
                        task_id=task_id,
                        stage="merging_json_responses",
                        progress=85,
                        message=f"Applying intelligent merge algorithm to combine data from {len(valid_json_responses)} documents"
                    )
                    
                    merged_json = llm_service.merge_json_responses(valid_json_responses)
                    if merged_json:
                        logger.info("Successfully merged JSON responses from all documents")
                        combined_analysis = merged_json
                        
                        redis_service.update_task_progress(
                            task_id=task_id,
                            stage="merging_json_responses",
                            progress=90,
                            message=f"Successfully merged data from {len(valid_json_responses)} documents ({len(merged_json)} characters)"
                        )
                    else:
                        logger.error("Failed to merge JSON responses")
                        combined_analysis = "Error: Failed to merge JSON responses from documents"
                else:
                    logger.error("No valid JSON responses to merge")
                    combined_analysis = "Error: No valid JSON responses from any documents"
                    
            except Exception as e:
                logger.error(f"Error merging JSON responses: {str(e)}")
                combined_analysis = f"Error merging JSON responses: {str(e)}"
            
            # Store the merged JSON result in the first document (as a representative)
            if combined_analysis and processed_count > 0:
                try:
                    redis_service.update_task_progress(
                        task_id=task_id,
                        stage="saving_results",
                        progress=95,
                        message="Saving merged analysis results to database"
                    )
                    
                    # Find the first successfully processed document to store the merged result
                    first_doc = db.query(DocumentUpload).filter(
                        DocumentUpload.id.in_(document_ids),
                        DocumentUpload.extraction_status == "completed"
                    ).first()
                    
                    if first_doc:
                        # Store the merged JSON in the extracted_text field of the first document
                        # This will be the combined analysis from all documents
                        first_doc.extracted_text = combined_analysis
                        db.commit()
                        logger.info(f"Stored merged JSON result in document {first_doc.id}")
                        
                        redis_service.update_task_progress(
                            task_id=task_id,
                            stage="saving_results",
                            progress=98,
                            message=f"Successfully saved merged analysis to database (document ID: {first_doc.id})"
                        )
                except Exception as e:
                    logger.error(f"Error storing merged JSON result: {str(e)}")
            
            # Update Redis status - Completed
            redis_service.update_task_progress(
                task_id=task_id,
                stage="completed",
                progress=100,
                message=f"Successfully processed {processed_count} documents and merged JSON responses",
                data={
                    "processed_documents": processed_count,
                    "total_documents": len(document_ids),
                    "merged_json_length": len(combined_analysis) if combined_analysis else 0,
                    "analysis_completed": True,
                    "merged_json_available": combined_analysis is not None
                }
            )
            
            logger.info(f"Multi-document processing completed successfully for group {group_id}")
            return {
                "status": "success",
                "message": f"Successfully processed {processed_count} documents and merged JSON responses",
                "processed_documents": processed_count,
                "total_documents": len(document_ids),
                "merged_json_length": len(combined_analysis) if combined_analysis else 0,
                "analysis_completed": True,
                "merged_json_available": combined_analysis is not None
            }
            
        except Exception as e:
            logger.error(f"Error in multi-document processing: {str(e)}")
            # Update all documents to failed status
            for document_id in document_ids:
                document = db.query(DocumentUpload).filter(DocumentUpload.id == document_id).first()
                if document:
                    document.extraction_status = "failed"
                    document.processing_error = str(e)
                    document.processing_completed_at = datetime.now(UTC)
            db.commit()
            
            redis_service.update_task_progress(
                task_id=task_id,
                stage="failed",
                progress=0,
                message=f"Multi-document processing failed: {str(e)}"
            )
            return {"status": "error", "message": str(e)}
            
    except Exception as e:
        logger.error(f"Error in multi-document processing task: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return {"status": "error", "message": str(e)}


# Export the Celery app for use in other modules
__all__ = ['celery_app', 'pdf_processing_task', 'multi_pdf_processing_task'] 
