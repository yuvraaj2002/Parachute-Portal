import boto3
import pandas as pd
import uuid
from typing import Dict, Any, List, Tuple
from functools import wraps
from fastapi import UploadFile, HTTPException, File, Depends
from fastapi.responses import JSONResponse
from app.config import settings
from app.agent_config import VALID_TAG_TYPES
import logging
import tempfile
import os
import requests
import hashlib
import base64
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

class FileHandler:
    """Service for handling file uploads and S3 operations with HIPAA compliance"""
    
    def __init__(self):
        self.s3_client = boto3.client('s3',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region
        )
        self.bucket_name = settings.aws_bucket_name
        
        # Initialize encryption key for HIPAA compliance
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for HIPAA compliance"""
        # Prefer a stable key from settings if provided
        if getattr(settings, 'encryption_key', None):
            key = settings.encryption_key.strip()
            try:
                # Validate and return bytes
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
        """Encrypt sensitive data for HIPAA compliance"""
        return self.cipher_suite.encrypt(data)
    
    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        """Decrypt sensitive data"""
        return self.cipher_suite.decrypt(encrypted_data)
    
   
    def save_to_s3(self, file: UploadFile, file_id: str = None) -> Dict[str, Any]:
        """Save uploaded file to S3 bucket with HIPAA-compliant encryption"""
        try:
            if not file_id:
                file_id = str(uuid.uuid4())
            
            file_extension = '.' + file.filename.split('.')[-1].lower()
            s3_key = f"uploads/{file_id}{file_extension}"
            
            logger.info(f"Starting S3 upload for file: {file.filename}")
            logger.info(f"File size: {file.size} bytes")
            logger.info(f"S3 key: {s3_key}")
            logger.info(f"Bucket: {self.bucket_name}")
            
            file.file.seek(0)
            file_content = file.file.read()
            logger.info(f"Read file content: {len(file_content)} bytes")
            
            # Encrypt file content for HIPAA compliance
            encrypted_content = self.encrypt_data(file_content)
            logger.info(f"Encrypted content: {len(encrypted_content)} bytes")
            
            # Create a temporary file with encrypted content
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(encrypted_content)
                temp_file.flush()
                logger.info(f"Created temporary file: {temp_file.name}")
                
                # Upload encrypted file to S3
                with open(temp_file.name, 'rb') as encrypted_file:
                    logger.info(f"Uploading to S3...")
                    self.s3_client.upload_fileobj(
                        encrypted_file, self.bucket_name, s3_key,
                        ExtraArgs={
                            'ContentType': 'application/octet-stream',  # Encrypted content
                            'Metadata': {
                                'original_filename': file.filename,
                                'file_id': file_id,
                                'encrypted': 'true',
                                'original_content_type': file.content_type
                            }
                        }
                    )
                    logger.info(f"Successfully uploaded to S3: {s3_key}")
                
                # Clean up temporary file
                os.unlink(temp_file.name)
                logger.info(f"Cleaned up temporary file")
            
            s3_url = f"https://{self.bucket_name}.s3.{settings.aws_region}.amazonaws.com/{s3_key}"
            logger.info(f"File uploaded successfully to S3: {s3_key}")
            
            return {
                "success": True,
                "file_id": file_id,
                "s3_key": s3_key,
                "s3_url": s3_url,
                "original_filename": file.filename,
                "content_type": file.content_type
            }
            
        except Exception as e:
            logger.error(f"Error uploading file to S3: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to upload file to S3: {str(e)}")

    def generate_presigned_url(self, s3_key: str, expires_in: int = 3600) -> str:
        """
        Generate a pre-signed URL for an S3 object key.
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expires_in
            )
            return url
        except Exception as e:
            logger.error(f"Error generating pre-signed URL: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to generate pre-signed URL: {str(e)}")

    def load_s3_file_as_dataframe(self, s3_key: str, expires_in: int = 3600) -> pd.DataFrame:
        """
        Download a file from S3 and load it as a pandas DataFrame.
        Supports CSV, XLS, XLSX formats with HIPAA-compliant decryption.
        """
        try:
            # Download directly from S3 using boto3 (more reliable than presigned URLs)
            logger.info(f"Downloading file from S3: {s3_key}")
            
            # Create a temporary file to store the downloaded content
            file_extension = '.' + s3_key.split('.')[-1].lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_download_file:
                tmp_download_file_path = tmp_download_file.name
            
            try:
                # Download file directly from S3
                self.s3_client.download_file(self.bucket_name, s3_key, tmp_download_file_path)
                logger.info(f"Successfully downloaded file from S3 to: {tmp_download_file_path}")
                
                # Read the downloaded file
                with open(tmp_download_file_path, 'rb') as f:
                    encrypted_content = f.read()
                logger.info(f"Read encrypted content: {len(encrypted_content)} bytes")
                
                # Check if the content is encrypted based on metadata
                try:
                    obj_metadata = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
                    is_encrypted = obj_metadata.get('Metadata', {}).get('encrypted', 'false') == 'true'
                    logger.info(f"File encryption status from metadata: {is_encrypted}")
                except Exception as meta_error:
                    logger.warning(f"Could not get metadata: {str(meta_error)}")
                    # Default to assuming it's encrypted since we encrypt by default
                    is_encrypted = True
                
                # Decrypt the content if it's encrypted
                if is_encrypted:
                    try:
                        decrypted_content = self.decrypt_data(encrypted_content)
                        logger.info(f"Successfully decrypted content, size: {len(decrypted_content)} bytes")
                    except Exception as decrypt_error:
                        logger.error(f"Failed to decrypt content: {str(decrypt_error)}")
                        # Fail fast: Do not try to parse ciphertext as Excel/CSV
                        raise HTTPException(status_code=500, detail="S3 object is marked as encrypted but decryption failed. Ensure the same Fernet key is used for upload and download.")
                else:
                    logger.info("Content not encrypted according to metadata, using as-is")
                    decrypted_content = encrypted_content
                
                # Create a new temporary file with the decrypted content
                with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_decrypted_file:
                    tmp_decrypted_file.write(decrypted_content)
                    tmp_decrypted_file.flush()
                    temp_decrypted_path = tmp_decrypted_file.name
                    logger.info(f"Created decrypted temporary file: {temp_decrypted_path}")
                
                # Try to read as DataFrame
                try:
                    if file_extension == '.csv':
                        df = pd.read_csv(temp_decrypted_path)
                        logger.info("Successfully loaded as CSV")
                    elif file_extension in ['.xls', '.xlsx']:
                        # Try different engines for Excel files
                        engines_to_try = ['openpyxl', 'xlrd', 'calamine']
                        df = None
                        last_error = None
                        
                        for engine in engines_to_try:
                            try:
                                df = pd.read_excel(temp_decrypted_path, engine=engine)
                                logger.info(f"Successfully loaded Excel file using engine: {engine}")
                                break
                            except Exception as engine_error:
                                logger.warning(f"Failed to load with engine {engine}: {str(engine_error)}")
                                last_error = engine_error
                                continue
                        
                        if df is None:
                            raise last_error or Exception("Failed to load Excel file with any engine")
                    else:
                        raise ValueError(f'Unsupported file type: {file_extension}')
                    
                    logger.info(f"Successfully loaded DataFrame with {len(df)} rows and {len(df.columns)} columns")
                    logger.info(f"DataFrame columns: {df.columns.tolist()}")
                    
                    # Clean up temporary files
                    os.unlink(temp_decrypted_path)
                    os.unlink(tmp_download_file_path)
                    
                    return df
                    
                except Exception as df_error:
                    logger.error(f"Failed to load DataFrame: {str(df_error)}")
                    # Clean up temporary files
                    if os.path.exists(temp_decrypted_path):
                        os.unlink(temp_decrypted_path)
                    raise df_error
                    
            except Exception as download_error:
                logger.error(f"Failed to download file from S3: {str(download_error)}")
                raise download_error
            finally:
                # Clean up download file
                if os.path.exists(tmp_download_file_path):
                    os.unlink(tmp_download_file_path)
                
        except Exception as e:
            logger.error(f"Error loading S3 file as DataFrame: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to load S3 file as DataFrame: {str(e)}")

   



# Global instance
file_handler = FileHandler()

if __name__ == "__main__":
    file_handler = FileHandler()
    df = file_handler.load_s3_file_as_dataframe("")
    print(df)