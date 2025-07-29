import logging
from parser.io.reader import read_packages
from parser.layers import create_package_layers
from parser.report import create_report

import click

LOG_FORMAT = "%(levelname)s | %(message)s"
logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG)

log = logging.getLogger(__name__)


@click.command()
@click.argument(
    "project-folder",
    type=click.Path(exists=False, file_okay=True, dir_okay=True, readable=True),
)
def parse(project_folder: str):
    packages = read_packages(project_folder)
    layers = create_package_layers(packages)

    log.info("Creating the report for: %s", project_folder)
    create_report(project_folder, layers)
