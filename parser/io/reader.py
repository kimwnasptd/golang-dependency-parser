import logging
import os
from parser.io.golang import read_golang_packages
from parser.io.python import read_piptools_packages, read_poetry_uv_packages
from parser.package import Package
from typing import List

log = logging.getLogger(__name__)


def read_packages(root_dir: str) -> List[Package]:
    if not os.path.isdir(root_dir):
        raise ValueError(f"Error: Folder '{dir}' does not exist.")

    go_mod_file = os.path.join(root_dir, "go.mod")
    if os.path.exists(go_mod_file):
        log.info("go.mod detected. Will load golang packages.")
        return read_golang_packages(root_dir)

    poetry_lock_file = os.path.join(root_dir, "poetry.lock")
    if os.path.exists(poetry_lock_file):
        log.info("poetry.lock file detected. Will load python packages.")
        return read_poetry_uv_packages(root_dir, "poetry.lock")

    uv_lock_file = os.path.join(root_dir, "uv.lock")
    if os.path.exists(poetry_lock_file):
        log.info("uv.lock file detected. Will load python packages.")
        return read_poetry_uv_packages(root_dir, "uv.lock")

    requirements_in_file = os.path.join(root_dir, "requirements.in")
    if os.path.exists(requirements_in_file):
        log.info("requirements.in file detected. Will load python packages.")
        return read_piptools_packages(root_dir)

    raise RuntimeError(
        "Unsupported directory. No go.mod, poetry.lock or requirements.in"
    )
