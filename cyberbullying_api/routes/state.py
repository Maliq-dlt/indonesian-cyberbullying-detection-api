import asyncio
import os

API_KEY_ENV = os.getenv("API_KEY", "")
TRAINING_PROCESS = None
LOG_FILE_HANDLE = None
TRAINING_LOCK = asyncio.Lock()
