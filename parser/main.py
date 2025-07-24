import logging
from parser.layers import create_package_layers
from parser.report import create_report

import click

from .utils import (add_package_dependencies, read_go_list_packages,
                    read_go_mod_graph_packages)

LOG_FORMAT = "%(levelname)s | %(message)s"
logging.basicConfig(format=LOG_FORMAT, level=logging.DEBUG)

log = logging.getLogger(__name__)


@click.command()
@click.argument(
    "go-mod-folder",
    type=click.Path(exists=False, file_okay=True, dir_okay=True, readable=True),
)
def parse(go_mod_folder: str):
    log.info("Greating list of modules.")
    go_list_packages = read_go_list_packages(go_mod_folder)

    log.info("Creating modules graph.")
    go_mod_graph_packages = read_go_mod_graph_packages(go_mod_folder)

    log.info("Filling in dependencies for all the packages.")
    add_package_dependencies(go_list_packages, go_mod_graph_packages)
    layers = create_package_layers(go_list_packages)

    log.info("Creating the report for: %s", go_mod_folder)
    create_report(go_mod_folder, layers)
