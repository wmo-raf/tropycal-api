import logging

import click
from flask.cli import with_appcontext

from troapi.services import StormService


@click.command(name="update_storms")
@click.argument('jtwc_source', type=click.STRING, default="jtwc")
def update_storms(jtwc_source):
    logging.info("[STORMS]: Running Update storms command")

    StormService.update_storms()


@click.command(name="plot_summary")
@with_appcontext
def plot_summary():
    logging.info("[STORMS]: Plotting Summaries")

    StormService.plot_summary()
