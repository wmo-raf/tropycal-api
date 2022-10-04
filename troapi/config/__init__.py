import os

from dotenv import load_dotenv

from . import base, dev, production

load_dotenv()

SETTINGS = base.SETTINGS

if not os.getenv('FLASK_DEBUG'):
    SETTINGS.update(dev.SETTINGS)

if os.getenv('FLASK_DEBUG'):
    SETTINGS.update(production.SETTINGS)
