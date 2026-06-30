import asyncio
import os

API_KEY_ENV = os.getenv("API_KEY", "")
TRAINING_PROCESS = None
LOG_FILE_HANDLE = None
from classifier.db_config import EventLoopSafeLock
TRAINING_LOCK = EventLoopSafeLock()
