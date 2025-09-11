#!/usr/bin/env python3
"""
Celery Worker Startup Script

This script starts the Celery worker for the Parachute Portal FastAPI application.
Run this script to start processing background PDF processing tasks.

Usage:
    python celery_worker.py
"""

import os
import sys
import time
import logging

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# Import the celery app from the services module
from services.celery_service import celery_app
from services.redis_service import RedisService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_redis_connection():
    """Check if Redis is available before starting worker"""
    max_retries = 10
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            redis_service = RedisService()
            if redis_service.is_connected():
                logger.info("Redis connection verified successfully")
                return True
            else:
                logger.warning(f"Redis connection failed, attempt {attempt + 1}/{max_retries}")
        except Exception as e:
            logger.warning(f"Redis connection failed, attempt {attempt + 1}/{max_retries}: {e}")
        
        if attempt < max_retries - 1:
            logger.info(f"Retrying Redis connection in {retry_delay} seconds...")
            time.sleep(retry_delay)
    
    logger.error("Failed to connect to Redis after all retries")
    return False

if __name__ == "__main__":
    # Check Redis connection before starting worker
    if not check_redis_connection():
        logger.error("Cannot start Celery worker without Redis connection")
        sys.exit(1)
    
    logger.info("Starting Celery worker with Redis connection verified")
    
    # Start the Celery worker with optimized settings for PDF processing
    celery_app.worker_main([
        'worker',
        '--loglevel=info',
        '--pool=prefork',   # Use prefork pool for better compatibility with PDF processing
        '--hostname=parachute-pdf-worker@%h',  # Set a descriptive hostname
        '--concurrency=2',  # 2 worker processes for PDF processing
        '--max-tasks-per-child=50',  # Restart workers after 50 tasks to prevent memory leaks
        '--time-limit=1800',  # 30 minutes time limit for PDF processing
        '--soft-time-limit=1500',  # 25 minutes soft time limit
        '--queues=default',  # Process tasks from the default queue
        '--without-gossip',  # Disable gossip to reduce network overhead
        '--without-mingle',  # Disable mingle to reduce startup time
        '--without-heartbeat',  # Disable heartbeat to reduce network traffic
    ])
