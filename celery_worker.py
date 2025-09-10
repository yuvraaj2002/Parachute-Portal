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

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# Import the celery app from the services module
from services.celery_service import celery_app

if __name__ == "__main__":
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
    ])
