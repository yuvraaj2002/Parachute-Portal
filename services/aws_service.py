import boto3
import uuid
import logging
import tempfile
import os
from fastapi import UploadFile, HTTPException
from fastapi.responses import FileResponse
from config import settings
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

class FileHandler:
    """Service for handling PDF uploads and S3 operations with HIPAA compliance"""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region
        )
        self.bucket_name = settings.aws_bucket_name
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)

    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for HIPAA compliance"""
        if getattr(settings, 'encryption_key', None):
            key = settings.encryption_key.strip()
            try:
                Fernet(key.encode() if isinstance(key, str) else key)
                return key.encode() if isinstance(key, str) else key
            except Exception:
                logger.error("Invalid encryption_key provided in settings. Falling back to local key file.")
        
        key_file = "encryption_key.key"
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(key)
            return key

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
            s3_key = f"pdf_uploads/{file_id}{file_extension}"

            logger.info(f"Uploading PDF: {file.filename} -> S3 key: {s3_key}")

            file.file.seek(0)
            file_content = file.file.read()

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

            # cleanup encrypted temp file
            os.unlink(tmp_download_path)

            return decrypted_path

        except Exception as e:
            logger.error(f"Error loading PDF from S3: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to load PDF from S3: {str(e)}")


# Global instance
file_handler = FileHandler()
