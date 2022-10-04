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
    'ITEMS_PER_PAGE': int(os.getenv('ITEMS_PER_PAGE', 20)),
    'ROLLBAR_SERVER_TOKEN': os.getenv('ROLLBAR_SERVER_TOKEN'),
}
