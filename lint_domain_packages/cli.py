#!/usr/bin/env python
import pathlib
import sys

import click

from lint_domain_packages.analyzer import analyze_dependencies
from lint_domain_packages.config import get_linter_settings
from lint_domain_packages.grouper import group_violations


@click.group()
def cli():
    pass


@cli.command()
@click.argument(
    "project_directory", type=click.Path(exists=True, dir_okay=True, file_okay=False)
)
def analyze(project_directory: str):
    settings = get_linter_settings(pathlib.Path(project_directory))
    sys.path.insert(1, project_directory)
    violations = analyze_dependencies(settings)
    violation_groups = group_violations(violations)
    for group in violation_groups:
        click.secho(group.error_message, bold=True)
        for violation in group.violations:
            click.echo(violation.get_location())
        click.echo()

    if violation_groups:
        click.secho(
            f"Found {len(violation_groups)} dependency violations. 💥 💔 💥", fg="red"
        )
        return 1
    click.secho("All good! ✨ 🍰 ✨", fg="green")
    return 0


if __name__ == "__main__":
    cli()
