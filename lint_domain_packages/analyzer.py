import grimp
from grimp.application.ports.graph import AbstractImportGraph

from lint_domain_packages.interfaces import (
    ImportViolation,
    LinterSettings,
    NonPublicImportViolation,
    NotDependentImportViolation,
)


def analyze_dependencies(settings: LinterSettings) -> list[ImportViolation]:
    """
    Analyze dependencies and return the list of violations.
    """
    violations: list[ImportViolation] = []
    graph = grimp.build_graph(settings.root)
    packages = graph.find_children(settings.root)
    for package_import_path in packages:
        violations += analyze_package(package_import_path, settings, graph)
    return violations


def analyze_package(
    package_import_path: str, settings: LinterSettings, graph: AbstractImportGraph
) -> list[ImportViolation]:
    """Analyze domain package for import violations."""
    violations: list[ImportViolation] = []
    descendants = graph.find_descendants(package_import_path)
    for descendant_import_path in descendants:
        violations += analyze_descendant(descendant_import_path, settings, graph)
    return violations


def analyze_descendant(
    descendant_import_path: str, settings: LinterSettings, graph: AbstractImportGraph
) -> list[ImportViolation]:
    """Analyze a descendant (a module or a package) for import violations."""
    violations: list[ImportViolation] = []
    for imported_module_import_path in graph.find_modules_directly_imported_by(
        descendant_import_path
    ):
        if not is_domain_package(graph, imported_module_import_path):
            continue

        if belong_to_the_same_package(
            descendant_import_path, imported_module_import_path
        ):
            continue

        if not settings.is_public(imported_module_import_path):
            violations.append(
                NonPublicImportViolation(
                    graph=graph,
                    importer=descendant_import_path,
                    imported=imported_module_import_path,
                )
            )

        if not settings.listed_in_dependencies(
            descendant_import_path, imported_module_import_path
        ):
            violations.append(
                NotDependentImportViolation(
                    graph=graph,
                    importer=descendant_import_path,
                    imported=imported_module_import_path,
                )
            )
    return violations


def belong_to_the_same_package(
    first_module_import_path: str, second_module_import_path: str
) -> bool:
    """
    Return True if two modules belong to the same domain package.
    """
    first_chunks = first_module_import_path.split(".")
    second_chunks = second_module_import_path.split(".")
    return first_chunks[:2] == second_chunks[:2]


def is_domain_package(graph: AbstractImportGraph, import_path: str) -> bool:
    """Return True if import_path belongs to a domain package."""
    chunks = import_path.split(".")

    if len(chunks) > 2:
        # For example, "myproject.users.services".
        # "myproject.users" is a domain package.
        return True

    if len(chunks) == 2:
        # For example, "myproject.users" or "myproject.config".
        # We need to see if it it's a domain package (has descendants),
        # or a module (doesn't have any descendants)
        has_children = bool(graph.find_children(import_path))
        return has_children

    # For example, "myproject". Not a domain package
    return False
