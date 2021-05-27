import abc
from dataclasses import dataclass

from grimp.application.ports.graph import AbstractImportGraph


@dataclass
class LinterSettings:

    # Root package that we analyzes
    root: str

    # List of public domain packages.
    #
    # All modules of public domain packages  are open to import. Usually, those are
    # so-called, "utility packages", an assorted list of helper classes and functions.
    #
    # Note that marking a domain package as public doesn't automatically add it to
    # the list of dependencies.
    public_packages: list[str]

    # List of public modules.
    #
    # Usually contains things like services and interfaces, but doesn't contain
    # things that are specific to internal implementation of the package.
    #
    # Applies to all domain packages.
    #
    # Note that in order to be able to import these modules from the
    # outside, you need to add the enclosing package in dependencies
    public_modules: list[str]

    # A self-imposed dependency map.
    #
    # Contains mapping from dependent modules to depending ones.
    # For example, dependencies={"payments": ["users", "projects"]} means that
    # the domain package "payments" depends on (imports) packages "users" and
    # "projects"
    dependencies: dict[str, list[str]]

    def is_public(self, module_import_path: str) -> bool:
        """
        Return true if module is public.

        The module is considered public, if it belongs to a public domain package
        (like, "myproject.utils") or the top-level module is public itself.
        (like, "myproject.foo.services").
        """
        chunks = self._get_module_chunks(module_import_path)
        root, package = chunks[:2]
        if len(chunks) > 2:
            toplevel_module = chunks[2]
        else:
            toplevel_module = None  # doesn't exist
        if package in self.public_packages:
            return True
        if toplevel_module and toplevel_module in self.public_modules:
            return True
        return False

    def listed_in_dependencies(
        self, module_import_path: str, imported_module_import_path: str
    ) -> bool:
        """
        Return True if the package of `imported_module_import_path` is marked as
        a dependency of the package of `module_import_path`.
        """
        package_name = self._get_module_chunks(module_import_path)[1]
        imported_package_name = self._get_module_chunks(imported_module_import_path)[1]
        if package_name not in self.dependencies:
            return False
        return imported_package_name in self.dependencies[package_name]

    def _get_module_chunks(self, module_import_path):
        chunks = module_import_path.split(".")
        if chunks[0] != self.root:
            raise RuntimeError(f"{module_import_path} doesn't belong to {self.root}")
        return chunks


@dataclass
class ImportDetails:
    line_number: int
    line_contents: str


@dataclass
class ImportViolationGroup:
    group_key: str
    error_message: str
    violations: list["ImportViolation"]


@dataclass
class ImportViolation:
    """Generic class for an import violation."""

    graph: AbstractImportGraph
    importer: str
    imported: str

    def get_import_details(self) -> ImportDetails:
        details = self.graph.get_import_details(
            importer=self.importer, imported=self.imported
        )[0]
        return ImportDetails(details["line_number"], details["line_contents"])

    def get_location(self) -> str:
        details = self.get_import_details()
        return (
            f"{self.importer_filename}:{details.line_number} "
            f"{details.line_contents}"
        )

    @property
    def importer_filename(self) -> str:
        return self.importer.replace(".", "/") + ".py"

    @property
    def imported_filename(self) -> str:
        return self.imported.replace(".", "/") + ".py"

    def error_message(self) -> str:
        raise NotImplementedError("Must be implemented in subclasses.")

    def group_key(self) -> str:
        raise NotImplementedError("Must be implemented in subclasses.")


@dataclass
class NonPublicImportViolation(ImportViolation):
    def error_message(self) -> str:
        return "A module imported outside of the package is not public."

    def group_key(self) -> str:
        return self.imported


@dataclass
class NotDependentImportViolation(ImportViolation):
    def error_message(self) -> str:
        return (
            f"Package {domain_package(self.importer)} implicitly depends on "
            f"{domain_package(self.imported)}."
        )

    def group_key(self) -> str:
        return f"{domain_package(self.importer)}:{domain_package(self.imported)}"


def domain_package(import_path: str):
    return import_path.split(".")[1]
