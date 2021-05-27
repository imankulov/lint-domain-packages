import pathlib

import toml

from lint_domain_packages.interfaces import LinterSettings

DOMAIN_PACKAGES_FILENAME = "domain_packages.toml"
ROOT_CONFIG_SECTION = "domain_packages"


def get_linter_settings(project_directory: pathlib.Path) -> LinterSettings:
    """
    Find linter settings in a project directory.
    """
    config_file = project_directory / DOMAIN_PACKAGES_FILENAME
    if not config_file.is_file():
        raise ValueError(f"Config file {config_file} not found")
    raw_config = toml.loads(config_file.read_text())[ROOT_CONFIG_SECTION]
    return LinterSettings(
        root=raw_config["root"],
        public_packages=raw_config["public_packages"],
        public_modules=raw_config["public_modules"],
        dependencies=raw_config["dependencies"],
    )
