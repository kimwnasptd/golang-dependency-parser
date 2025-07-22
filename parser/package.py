from typing import Set


class Package:
    import_name: str
    version: str
    depends: Set[str]

    def __init__(self, import_name: str, version: str) -> None:
        self.import_name = import_name
        self.version = version
        self.depends = set()

    @property
    def is_root(self) -> bool:
        if not self.version:
            return True

        return False

    def __repr__(self) -> str:
        if not self.is_root:
            return self.import_name + " " + self.version

        return self.import_name

    def __hash__(self) -> int:
        return hash(self.__repr__())
