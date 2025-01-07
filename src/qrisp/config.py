import logging
import sys

def setup_logging(level=logging.INFO):
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger('qrisp')
    # Avoid duplicate handlers
    if not root_logger.handlers:
        root_logger.addHandler(console_handler)
    root_logger.setLevel(level)

# Auto-setup with default settings
setup_logging() 