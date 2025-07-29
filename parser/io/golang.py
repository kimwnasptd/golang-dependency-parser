import logging
import os
import shutil
import subprocess
from parser.package import Package
from typing import List

log = logging.getLogger(__name__)


def change_dir_run_command(dir: str, command: List[str]) -> str:
    if not os.path.isdir(dir):
        raise ValueError(f"Error: Folder '{dir}' does not exist.")

    # Store the current working directory to return later
    original_cwd = os.getcwd()

    try:
        os.chdir(dir)
        log.info("Changed working dir to: %s", dir)
        result = subprocess.run(command, capture_output=True, text=True, check=True)
    finally:
        # Always change back to the original directory
        os.chdir(original_cwd)

    return result.stdout


def remove_vendor_dir(root_dir: str):
    # Remove the vendor/ folder if it exists
    vendor_dir = root_dir + "/vendor"
    if not os.path.exists(vendor_dir):
        return

    log.info("Removing vendor dir")
    shutil.rmtree(vendor_dir)


def read_go_list_packages(go_mod_folder: str) -> List[Package]:
    packages = []

    remove_vendor_dir(go_mod_folder)

    cmd = ["go", "list", "-m", "all"]
    for line in change_dir_run_command(go_mod_folder, cmd).split("\n"):
        if not line:
            continue

        if "=>" in line:
            # module pointing to another go.mod that will be handled in the graph
            splitted_line = line.split(" ")
            packages.append(Package(splitted_line[0], splitted_line[1]))
            continue

        if " " not in line:
            # top level package
            packages.append(Package(line, ""))
            continue

        path, version = line.split(" ")
        packages.append(Package(path, version))

    return packages


def read_go_mod_graph_packages(go_mod_folder: str) -> List[tuple[Package, Package]]:
    packages = []

    cmd = ["go", "mod", "graph"]
    for line in change_dir_run_command(go_mod_folder, cmd).split("\n"):
        if not line:
            continue

        if "toolchain@" in line:
            continue

        source, requirement = line.split(" ")

        # top level package won't have a @
        source_splitted = source.split("@")
        if "@" in source:
            source_pkg = Package(*source_splitted)
        else:
            source_pkg = Package(source_splitted[0], "")

        req_splitted = requirement.split("@")
        req_pkg = Package(*req_splitted)

        packages.append((source_pkg, req_pkg))

    return packages


def add_package_dependencies(
    go_list_packages: List[Package],
    go_mod_graph_packages: List[tuple[Package, Package]],
):
    # Adds only the import name, and not the version
    for package in go_list_packages:
        log.info("Filling in all dependency packages of: %s", package.import_name)
        for root_package, dependant in go_mod_graph_packages:
            if root_package.import_name == package.import_name:
                package.depends.add(dependant.import_name)


def read_golang_packages(go_mod_folder: str) -> List[Package]:
    log.info("Greating list of modules.")
    go_list_packages = read_go_list_packages(go_mod_folder)

    log.info("Creating modules graph.")
    go_mod_graph_packages = read_go_mod_graph_packages(go_mod_folder)

    log.info("Filling in dependencies for all the packages.")
    add_package_dependencies(go_list_packages, go_mod_graph_packages)

    return go_list_packages
