from classifier.db_config import EventLoopSafeLock

TRAINING_PROCESS = None
LOG_FILE_HANDLE = None

TRAINING_LOCK = EventLoopSafeLock()
