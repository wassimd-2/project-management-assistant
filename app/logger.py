import logging
from pathlib import Path
from app.database import add_log

# Dynamically resolve the path to the logs directory
BASE_DIR = Path(__file__).parent.parent
LOG_FILE = BASE_DIR / "logs" / "agent.log"

# Ensure the logs directory exists
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Configure the Python built-in logger for file output
logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def log_agent_action(intent: str, tool_used: str, details: str = "") -> None:
    """
    Logs an agent's action to both the file system and the SQLite database.
    
    Args:
        intent (str): The current intention of the agent (e.g., 'task_creation').
        tool_used (str): The specific tool invoked.
        details (str): Any additional context, inputs, or outcomes.
    """
    # 1. Write to the backend text log
    log_message = f"Intent: [{intent}] | Tool: [{tool_used}] | Details: {details}"
    logging.info(log_message)
    
    # 2. Write to the persistent SQLite database
    try:
        # Default to "Unknown" if intent is empty to prevent DB constraint errors
        safe_intent = intent if intent else "Unknown"
        add_log(intent=safe_intent, tool_used=tool_used, details=details)
    except Exception as e:
        # Fallback error logging if the DB is locked or fails
        logging.error(f"CRITICAL: Failed to write log to database. Error: {e}")

def get_system_logger():
    """Returns the base logger instance for standard debugging."""
    return logging.getLogger(__name__)