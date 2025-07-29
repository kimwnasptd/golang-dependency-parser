import logging
import os
import re
from parser.package import Package
from pathlib import Path
from typing import List, Set

import tomlkit

log = logging.getLogger(__name__)


def read_poetry_uv_packages(root_dir: str, file="poetry.lock") -> List[Package]:
    if not os.path.isdir(root_dir):
        raise ValueError(f"Error: Folder '{dir}' does not exist.")

    # Store the current working directory to return later
    original_cwd = os.getcwd()

    contents = None

    try:
        os.chdir(root_dir)
        log.info("Changed working dir to: %s", root_dir)
        contents = Path(file).read_text()
    finally:
        # Always change back to the original directory
        os.chdir(original_cwd)

    if not contents:
        raise RuntimeError("Couldn't initialise the contents from poetry.lock")

    data = tomlkit.parse(contents)

    packages: List[Package] = []
    for package in data.get("package", []):
        dependencies: Set[str] = set()
        for dep in package.get("dependencies", []):
            dependencies.add(dep)

        pkg = Package(import_name=package["name"], version=package["version"])
        pkg.depends = dependencies
        packages.append(pkg)

    return packages


def read_piptools_packages(root_dir: str) -> List[Package]:
    requirements_content = Path(os.path.join(root_dir, "requirements.txt")).read_text()

    # Split the content into lines and iterate
    lines = requirements_content.strip().split("\n")

    packages: List[Package] = []
    dependencies_map = {}
    for i, line in enumerate(lines):
        # This loop is only for parasing packages
        # We parse comments only after we've parsed a package
        if "#" in line:
            continue

        if not line:
            break

        line = line.strip()
        name = ""
        version = ""

        if "==" in line:
            name, version = line.split("==")

        packages.append(Package(name, version))

        # read dependencies from comments
        j = i + 1
        next_line = lines[j]
        if "#" in next_line and "via" in next_line:
            while "#" in next_line:
                if "-r -" in next_line:
                    j += 1
                    next_line = lines[j]
                    continue

                if "via" in next_line:
                    last_word = next_line.split(" ")[-1]
                    if last_word == "via" or last_word == "-":
                        j += 1
                        next_line = lines[j]
                        continue

                    dep_name = last_word

                else:
                    # comment with package name
                    dep_name = next_line.split(" ")[-1]

                dependencies_map[dep_name] = dependencies_map.get(dep_name, []) + [name]
                j += 1
                next_line = lines[j]

    # add the dependencies to the packages
    for package in packages:
        package.depends = set(dependencies_map.get(package.import_name, []))

    return packages
