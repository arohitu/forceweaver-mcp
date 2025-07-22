"""
Logging configuration for ForceWeaver MCP API
"""

import logging
import logging.config
import os

def setup_logging(app):
    """Setup logging configuration."""
    
    # Get log level from environment
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    
    # Configure logging
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
            'detailed': {
                'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s'
            }
        },
        'handlers': {
            'default': {
                'level': log_level,
                'formatter': 'standard',
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout',
            },
            'error_file': {
                'level': 'ERROR',
                'formatter': 'detailed',
                'class': 'logging.FileHandler',
                'filename': 'logs/error.log',
                'mode': 'a',
            },
            'debug_file': {
                'level': 'DEBUG',
                'formatter': 'detailed',
                'class': 'logging.FileHandler',
                'filename': 'logs/debug.log',
                'mode': 'a',
            },
            'health_check_file': {
                'level': 'INFO',
                'formatter': 'detailed',
                'class': 'logging.FileHandler',
                'filename': 'logs/health_checks.log',
                'mode': 'a',
            }
        },
        'loggers': {
            '': {  # root logger
                'handlers': ['default'],
                'level': log_level,
                'propagate': False
            },
            'app': {
                'handlers': ['default', 'error_file', 'debug_file'],
                'level': 'DEBUG',  # Capture all app logs in debug file
                'propagate': False
            },
            'app.services.health_checker_service': {
                'handlers': ['default', 'error_file', 'health_check_file'],
                'level': 'DEBUG',  # Capture all health check logs
                'propagate': False
            },
            'app.services.salesforce_service': {
                'handlers': ['default', 'error_file', 'debug_file'],
                'level': 'DEBUG',  # Capture all Salesforce service logs
                'propagate': False
            },
            'gunicorn.error': {
                'handlers': ['default'],
                'level': log_level,
                'propagate': False
            },
            'gunicorn.access': {
                'handlers': ['default'],
                'level': log_level,
                'propagate': False
            }
        }
    }
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Apply logging configuration
    logging.config.dictConfig(logging_config)
    
    # Set Flask's logger to use our configuration
    app.logger.setLevel(getattr(logging, log_level))
    
    # Log startup message
    app.logger.info(f"ForceWeaver MCP API starting with log level: {log_level}")
    app.logger.info("Health check debugging enabled - check logs/health_checks.log for detailed output") 