import logging
from parser.package import Package, PackageLayer
from typing import List, Set

log = logging.getLogger(__name__)


def print_layers(layers: List[PackageLayer]):
    print("---------")
    for i, layer in enumerate(layers):
        msg = "\nLayer %s" % i
        if layer.bootstrap:
            msg += " (Bootstrap)"

        print(msg)

        print("---")
        for package in layer.packages:
            print(package)

    print("")
    print("---------")


def get_bootstrap_dependency(
    packages: List[Package], layer_packages: Set[str]
) -> Package:
    """
    Find the best package to bootstrap, heuristically.

    The script will ideally try to find the package that is a dependency of most packages,
    that is not already parsed.
    """
    frequencies: List[str] = []
    for package in packages:
        for dependency in package.depends:
            # if package already in previous layers, then we don't need to re-parse it
            if dependency.lower() in layer_packages or dependency in layer_packages:
                continue

            if dependency == "go":
                continue

            frequencies.append(dependency)

    print(layer_packages)
    bootstrap_package_name = max(frequencies, key=frequencies.count)
    for package in packages:
        if package.import_name == bootstrap_package_name:
            return package

    log.error("Bootstrap package: %s", bootstrap_package_name)
    log.error("Packages list: %s", packages)
    raise RuntimeError("Most frequent package not found in initial list.")


def create_package_layers(packages: List[Package]) -> List[PackageLayer]:
    layers: List[PackageLayer] = []
    packages_of_previous_layers: Set[str] = set()

    while packages:
        # Iterate through all the current packages. Once the iteration is done, we have a layer
        current_layer = PackageLayer()
        for package in packages:
            log.info("Parsing package: %s", package)

            if not package.depends:
                log.info("Package is a leaf one. Adding it to current layer.")
                current_layer.packages.add(package)
                continue

            dependencies_in_previous_layers = True
            for dependency in package.depends:
                if dependency == "go":
                    continue

                if (
                    dependency.lower() not in packages_of_previous_layers
                    and dependency not in packages_of_previous_layers
                ):
                    log.info("Dependency not parsed yet: %s", dependency)
                    dependencies_in_previous_layers = False
                    break

            # all package dependencies exist in current layers
            if dependencies_in_previous_layers:
                log.info(
                    "All dependencies exist in current layers. Adding %s to current layer.",
                    package,
                )
                current_layer.packages.add(package)

        if not current_layer.packages and packages:
            log.warning(
                "Current layer unexpectedly was empty but there are still pacakges to parse."
            )
            log.info(
                "Circular dependency detected! Will try to unblock with bootstrapping."
            )

            bootstrap_dependency = get_bootstrap_dependency(
                packages, packages_of_previous_layers
            )
            current_layer.packages.add(bootstrap_dependency)
            current_layer.bootstrap = True

        log.info("Created new layer: %s", current_layer.packages)
        layers.append(current_layer)

        log.info("Marking packages in current layer as parsed.")
        for package in current_layer.packages:
            packages_of_previous_layers.add(package.import_name)
            if not current_layer.bootstrap:
                packages.remove(package)
            else:
                log.info("Layer is a bootstrap one. Will keep package to be processed.")

        print_layers(layers)

    return layers
