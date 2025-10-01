import boto3
import uuid
import logging
import tempfile
import os
from datetime import datetime
from fastapi import UploadFile, HTTPException
from fastapi.responses import FileResponse
from config import settings
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

class FileHandler:
    """Service for handling PDF uploads and S3 operations with HIPAA compliance"""
    
    def __init__(self):
        from botocore.config import Config
        
        # Configure S3 client with proper timeout settings
        config = Config(
            read_timeout=60,
            connect_timeout=60,
            retries={'max_attempts': 3}
        )
        
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
            config=config
        )
        self.bucket_name = settings.aws_bucket_name
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)

    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for HIPAA compliance"""
        if getattr(settings, 'encryption_key', None):
            key = settings.encryption_key.strip()
            try:
                # Validate the key format
                if isinstance(key, str):
                    key_bytes = key.encode()
                else:
                    key_bytes = key
                
                # Test if key is valid
                Fernet(key_bytes)
                return key_bytes
            except Exception as e:
                logger.error(f"Invalid encryption_key provided in settings: {e}. Falling back to local key file.")
        
        key_file = "encryption_key.key"
        try:
            if os.path.exists(key_file):
                with open(key_file, "rb") as f:
                    key = f.read()
                    # Validate existing key
                    Fernet(key)
                    return key
            else:
                key = Fernet.generate_key()
                with open(key_file, "wb") as f:
                    f.write(key)
                logger.info("Generated new encryption key for HIPAA compliance")
                return key
        except Exception as e:
            logger.error(f"Error handling encryption key: {e}")
            raise HTTPException(status_code=500, detail="Failed to initialize encryption key")

    def encrypt_data(self, data: bytes) -> bytes:
        return self.cipher_suite.encrypt(data)

    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        return self.cipher_suite.decrypt(encrypted_data)

    def save_pdf_to_s3(self, file: UploadFile, file_id: str = None) -> dict:
        """Save uploaded PDF file to S3 with encryption"""
        try:
            if not file_id:
                file_id = str(uuid.uuid4())

            file_extension = ".pdf"
            s3_key = f"medical_pdf_uploads/{file_id}{file_extension}"

            logger.info(f"Uploading PDF: {file.filename} -> S3 key: {s3_key}")

            file.file.seek(0)
            file_content = file.file.read()
            
            # Validate file size (max 50MB)
            max_size = 50 * 1024 * 1024  # 50MB
            if len(file_content) > max_size:
                raise HTTPException(status_code=400, detail="File size exceeds 50MB limit")
            
            # Validate PDF header
            if not file_content.startswith(b'%PDF'):
                raise HTTPException(status_code=400, detail="Invalid PDF file format")

            encrypted_content = self.encrypt_data(file_content)

            # Create a temporary encrypted file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".enc") as temp_file:
                temp_file.write(encrypted_content)
                temp_file.flush()
                temp_path = temp_file.name

            # Upload encrypted file to S3
            with open(temp_path, "rb") as encrypted_file:
                self.s3_client.upload_fileobj(
                    encrypted_file,
                    self.bucket_name,
                    s3_key,
                    ExtraArgs={
                        "ContentType": "application/pdf",
                        "Metadata": {
                            "original_filename": file.filename,
                            "file_id": file_id,
                            "encrypted": "true",
                            "original_content_type": file.content_type
                        }
                    }
                )

            os.unlink(temp_path)  # cleanup

            s3_url = f"https://{self.bucket_name}.s3.{settings.aws_region}.amazonaws.com/{s3_key}"
            return {
                "success": True,
                "file_id": file_id,
                "s3_key": s3_key,
                "s3_url": s3_url,
                "original_filename": file.filename,
                "content_type": file.content_type
            }

        except Exception as e:
            logger.error(f"Error uploading PDF to S3: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to upload PDF: {str(e)}")

    def load_pdf_from_s3(self, s3_key: str) -> str:
        """
        Download and decrypt PDF file from S3.
        Returns a path to a temporary decrypted file you can serve or process further.
        """
        tmp_download_path = None
        try:
            # Temporary download encrypted file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".enc") as tmp_download_file:
                tmp_download_path = tmp_download_file.name

            self.s3_client.download_file(self.bucket_name, s3_key, tmp_download_path)

            with open(tmp_download_path, "rb") as f:
                encrypted_content = f.read()

            # Try decrypting
            decrypted_content = self.decrypt_data(encrypted_content)

            # Save decrypted content as PDF temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_decrypted_file:
                tmp_decrypted_file.write(decrypted_content)
                tmp_decrypted_file.flush()
                decrypted_path = tmp_decrypted_file.name

            return decrypted_path

        except Exception as e:
            logger.error(f"Error loading PDF from S3: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to load PDF from S3: {str(e)}")
        finally:
            # Cleanup encrypted temp file
            if tmp_download_path and os.path.exists(tmp_download_path):
                try:
                    os.unlink(tmp_download_path)
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp file {tmp_download_path}: {e}")

    def load_markdown_from_s3(self, s3_url: str) -> str:
        """
        Load markdown content from S3 URL.
        
        Args:
            s3_url: Full S3 URL (e.g., https://bucket.s3.region.amazonaws.com/path/file.md)
        
        Returns:
            Markdown content as string
        """
        try:
            # Parse S3 URL to extract bucket and key
            if not s3_url.startswith('https://'):
                raise ValueError("Invalid S3 URL format")
            
            # Extract bucket and key from URL
            # Format: https://bucket.s3.region.amazonaws.com/key
            url_parts = s3_url.replace('https://', '').split('/')
            if len(url_parts) < 2:
                raise ValueError("Invalid S3 URL format")
            
            # Handle different S3 URL formats
            if '.s3.' in url_parts[0]:
                bucket_name = url_parts[0].split('.s3.')[0]
                s3_key = '/'.join(url_parts[1:])
            else:
                # Fallback: assume first part is bucket
                bucket_name = url_parts[0]
                s3_key = '/'.join(url_parts[1:])
            
            logger.info(f"Loading markdown from S3: bucket={bucket_name}, key={s3_key}")
            
            # Download the markdown file from S3
            response = self.s3_client.get_object(Bucket=bucket_name, Key=s3_key)
            markdown_content = response['Body'].read().decode('utf-8')
            
            logger.info(f"Successfully loaded markdown from S3: {len(markdown_content)} characters")
            return markdown_content
            
        except Exception as e:
            logger.error(f"Error loading markdown from S3 URL {s3_url}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to load markdown from S3: {str(e)}")

    def download_pdf_template_from_s3(self, s3_path: str) -> str:
        """
        Download a PDF template from S3 (unencrypted).
        PDF templates are stored unencrypted as they are not patient data.
        
        Args:
            s3_path: S3 key or full URL to the template PDF
        
        Returns:
            Path to temporary downloaded PDF file
        """
        try:
            import urllib.parse
            
            # Extract S3 key from full URL if needed
            if s3_path.startswith('https://'):
                # Parse URL to get S3 key
                # Format: https://bucket.s3.region.amazonaws.com/key
                url_parts = s3_path.replace('https://', '').split('/')
                if '.s3.' in url_parts[0]:
                    s3_key = '/'.join(url_parts[1:])
                else:
                    s3_key = '/'.join(url_parts[1:])
                
                # Decode URL encoding (e.g., %20 -> space)
                s3_key = urllib.parse.unquote(s3_key)
                logger.info(f"Extracted and decoded S3 key from URL: {s3_key}")
            else:
                s3_key = s3_path
            
            logger.info(f"Downloading PDF template from S3: bucket={self.bucket_name}, key={s3_key}")
            
            # Create temporary file for PDF template
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_path = temp_file.name
            
            # Download PDF template from S3 (unencrypted)
            self.s3_client.download_file(
                self.bucket_name,
                s3_key,
                temp_path
            )
            
            logger.info(f"Successfully downloaded PDF template to: {temp_path}")
            return temp_path
            
        except Exception as e:
            logger.error(f"Error downloading PDF template from S3: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to download PDF template from S3: {str(e)}")

    def upload_generated_pdf_to_s3(self, local_pdf_path: str, group_id: str, template_name: str) -> dict:
        """
        Upload a generated PDF file to S3 in the generated_documents folder.
        
        Args:
            local_pdf_path: Local path to the generated PDF file
            group_id: Document group ID
            template_name: Name of the template used
        
        Returns:
            Dictionary with upload result including S3 key and URL
        """
        try:
            import uuid
            
            # Generate unique filename
            file_id = str(uuid.uuid4())
            safe_template_name = "".join(c for c in template_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_template_name = safe_template_name.replace(' ', '_').lower()
            
            # Create S3 key in generated_documents folder
            s3_key = f"generated_documents/{group_id}/{safe_template_name}_{file_id}.pdf"
            
            logger.info(f"Uploading generated PDF to S3: {local_pdf_path} -> {s3_key}")
            
            # Upload file to S3
            with open(local_pdf_path, 'rb') as pdf_file:
                self.s3_client.upload_fileobj(
                    pdf_file,
                    self.bucket_name,
                    s3_key,
                    ExtraArgs={
                        "ContentType": "application/pdf",
                        "Metadata": {
                            "group_id": group_id,
                            "template_name": template_name,
                            "file_id": file_id,
                            "generated_at": datetime.now().isoformat()
                        }
                    }
                )
            
            # Generate S3 URL
            s3_url = f"https://{self.bucket_name}.s3.{settings.aws_region}.amazonaws.com/{s3_key}"
            
            logger.info(f"Successfully uploaded generated PDF to S3: {s3_url}")
            
            return {
                "success": True,
                "s3_key": s3_key,
                "s3_url": s3_url,
                "file_id": file_id,
                "template_name": template_name
            }
            
        except Exception as e:
            logger.error(f"Error uploading generated PDF to S3: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to upload generated PDF to S3: {str(e)}")


# Global instance
file_handler = FileHandler()
