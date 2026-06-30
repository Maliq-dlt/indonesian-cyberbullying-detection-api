
TRAINING_PROCESS = None
LOG_FILE_HANDLE = None
from classifier.db_config import EventLoopSafeLock
TRAINING_LOCK = EventLoopSafeLock()
