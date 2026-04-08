import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging(name="quant_autoresearch", log_file="experiments/logs/run.log", level=logging.INFO):
    """Setup central logging with rotating file handler and console output"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    log_file_path = os.fspath(log_file)
    log_dir = os.path.dirname(log_file_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    # Avoid duplicate handlers
    if not logger.handlers:
        # Create formatters
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        
        # File handler (10MB per file, max 5 backups)
        file_handler = RotatingFileHandler(log_file_path, maxBytes=10*1024*1024, backupCount=5)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
    return logger

# Global logger
logger = setup_logging()
