import logging
import sys

from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from healthcheck import HealthCheck
from troapi.scheduler import scheduler

from troapi.config import SETTINGS

logging.basicConfig(
    level=SETTINGS.get('logging', {}).get('level'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y%m%d-%H:%M%p',
)

# Flask App
app = Flask(__name__)
CORS(app)

# Ensure all unhandled exceptions are logged
logger = logging.getLogger(__name__)
logger.setLevel(SETTINGS.get('logging', {}).get('level'))
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = handle_exception

# Config
app.config['SQLALCHEMY_DATABASE_URI'] = SETTINGS.get('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# pagination
app.config['ITEMS_PER_PAGE'] = SETTINGS.get('ITEMS_PER_PAGE', 20)

# Database
db = SQLAlchemy(app)

migrate = Migrate(app, db)

# wrap flask app and give a healthcheck url
health = HealthCheck(app, "/healthcheck")


def db_available():
    db.session.execute('SELECT 1')
    return True, "dbworks"


health.add_check(db_available)

# DB has to be ready!
from troapi.routes.api.v1 import endpoints, error

# Blueprint Flask Routing
app.register_blueprint(endpoints, url_prefix='/api/v1')


@app.errorhandler(403)
def forbidden(e):
    return error(status=403, detail='Forbidden')


@app.errorhandler(404)
def page_not_found(e):
    return error(status=404, detail='Not Found')


@app.errorhandler(405)
def method_not_allowed(e):
    return error(status=405, detail='Method Not Allowed')


@app.errorhandler(410)
def gone(e):
    return error(status=410, detail='Gone')


@app.errorhandler(500)
def internal_server_error(e):
    return error(status=500, detail='Internal Server Error')


from troapi import commands

app.cli.add_command(commands.update_storms)

from troapi import tasks

scheduler.start()
#
# scheduler = BackgroundScheduler()
# # in your case you could change seconds to hours
# scheduler.add_job(commands.update_storms, trigger='interval', seconds=3)
# scheduler.start()
