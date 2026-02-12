import os
import logging
from logging.handlers import TimedRotatingFileHandler
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class SensitiveDataFilter(logging.Filter):
    """Filter to remove sensitive data from log records"""

    def filter(self, record):
        # Sanitize the main message
        if hasattr(record, 'msg') and record.msg:
            record.msg = sanitize_message(record.msg)

        # Sanitize args if present
        if hasattr(record, 'args') and record.args:
            record.args = tuple(sanitize_message(str(arg))
                                for arg in record.args)

        return True


def sanitize_message(message):
    """Remove sensitive data from log messages"""
    if not isinstance(message, str):
        message = str(message)

    # Define patterns for sensitive data
    sensitive_patterns = [
        (r'sk_live_[a-zA-Z0-9]{24,}', '[STRIPE_SECRET_REDACTED]'),
        (r'pk_live_[a-zA-Z0-9]{24,}', '[STRIPE_PUBLIC_REDACTED]'),
        (r'sk_test_[a-zA-Z0-9]{24,}', '[STRIPE_TEST_SECRET_REDACTED]'),
        (r'rk_live_[a-zA-Z0-9]{24,}', '[STRIPE_RESTRICTED_REDACTED]'),
        (r'"password"\s*:\s*"[^"]*"', '"password": "[REDACTED]"'),
        (r'"token"\s*:\s*"[^"]*"', '"token": "[REDACTED]"'),
        (r'Bearer\s+[a-zA-Z0-9\-._~+/]+=*', 'Bearer [REDACTED]'),
        (r'Authorization:\s*[^\s]+', 'Authorization: [REDACTED]'),
        # Add more patterns as needed
    ]

    for pattern, replacement in sensitive_patterns:
        message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)
    return message


def setup_logger(logging_enabled=True):
    try:
        if not logging_enabled:
            return None

        # Create logs directory structure
        logs_folder = os.path.join(BASE_DIR, "Attachments", "logs")
        exception_folder = os.path.join(logs_folder, "exception")

        os.makedirs(exception_folder, exist_ok=True)

        log_filename = os.path.join(exception_folder, "api_exceptions.txt")

        # Create handler with rotation to prevent huge log files
        from logging.handlers import RotatingFileHandler
        handler = RotatingFileHandler(
            log_filename,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        handler.setLevel(logging.ERROR)

        # Add sensitive data filter
        sensitive_filter = SensitiveDataFilter()
        handler.addFilter(sensitive_filter)

        # Improved formatter - less verbose
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
        )
        handler.setFormatter(formatter)

        # Get or create logger
        logger = logging.getLogger(__name__)

        # Clear existing handlers to prevent duplicates
        logger.handlers.clear()
        logger.addHandler(handler)
        logger.setLevel(logging.ERROR)

        # Don't propagate to avoid duplicate logs
        logger.propagate = False

        return logger

    except Exception as e:
        # Use print instead of logging to avoid recursion
        # print(f"Logger setup failed: {e}")
        return None


logger = setup_logger(logging_enabled=True)



