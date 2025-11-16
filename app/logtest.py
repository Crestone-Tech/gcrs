import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.logger import setup_logging

logger = setup_logging(log_level="DEBUG")

logger.debug("This is a debug message")