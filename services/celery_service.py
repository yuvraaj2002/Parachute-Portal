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



# Export the Celery app for use in other modules
__all__ = ['celery_app', 'pdf_processing_task'] 
