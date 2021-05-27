from itertools import groupby

from lint_domain_packages.interfaces import ImportViolation, ImportViolationGroup


def group_violations(violations: list[ImportViolation]) -> list[ImportViolationGroup]:
    """Group import violations by the violation key."""
    sorted_violations = sorted(violations, key=_group_key)
    ret = []
    for group_key, violations_in_group in groupby(sorted_violations, _group_key):
        violations_in_group_list = list(violations_in_group)
        error_message = violations_in_group_list[0].error_message()
        ret.append(
            ImportViolationGroup(group_key, error_message, violations_in_group_list)
        )
    return ret


def _group_key(import_violation: ImportViolation):
    return import_violation.group_key()
