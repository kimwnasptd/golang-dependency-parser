import logging
import sys
from parser.package import Package
from typing import List, Set

log = logging.getLogger(__name__)


def print_layers(layers: List[List[Package]]):
    print("---------")
    for i in range(len(layers)):
        print("\nLayer %s" % i)
        print("---")
        for package in layers[i]:
            print(package)

    print("")
    print("---------")


def create_package_layers(packages: List[Package]) -> List[List[Package]]:
    layers = []
    packages_of_previous_layers: Set[str] = set()

    while packages:
        # Iterate through all the current packages. Once the iteration is done, we have a layer
        current_layer: Set[Package] = set()
        for package in packages:
            log.info("Parsing package: %s", package)

            if not package.depends:
                log.info("Package is a leaf one. Adding it to current layer.")
                current_layer.add(package)
                continue

            dependencies_in_previous_layers = True
            for dependency in package.depends:
                if dependency not in packages_of_previous_layers:
                    dependencies_in_previous_layers = False
                    break

            # all package dependencies exist in current layers
            if dependencies_in_previous_layers:
                log.info(
                    "All dependencies exist in current layers. Adding %s to current layer.",
                    package,
                )
                current_layer.add(package)

        if not current_layer and packages:
            log.error(
                "Current layer unexpectedly had zero elements but still pacakges to parse"
            )
            sys.exit(1)

        log.info("Created new layer: %s", current_layer)
        layers.append(current_layer)
        for package in current_layer:
            packages_of_previous_layers.add(package.import_name)
            packages.remove(package)

        print_layers(layers)

    return layers
