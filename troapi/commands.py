import logging

import click

from troapi.services import StormService


@click.command(name="update_storms")
@click.argument('jtwc_source', type=click.STRING, default="jtwc")
def update_storms(jtwc_source):
    logging.info("[STORMS]: Running Update storms command")

    StormService.update_storms()
