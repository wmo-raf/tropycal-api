import logging
import os

log_level = logging.getLevelName(os.getenv('LOG', "INFO"))

SETTINGS = {
    'logging': {
        'level': log_level
    },
    'service': {
        'port': os.getenv('PORT')
    },
    'SQLALCHEMY_DATABASE_URI': os.getenv('SQLALCHEMY_DATABASE_URI'),
    'STORMS_MINUTES_UPDATE_INTERVAL': os.getenv('STORMS_MINUTES_UPDATE_INTERVAL', 5),
    "UPLOAD_FOLDER": os.getenv('UPLOAD_FOLDER', os.path.join(os.getcwd(), 'uploads'))
}
