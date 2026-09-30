import re
from typing import Tuple


def parse_semver(v: str) -> Tuple[int, int, int]:
    """Parse semver string like '0.2.0' into (0, 2, 0)."""
    clean_v = v.strip().lstrip("v")
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)", clean_v)
    if not match:
        parts = clean_v.split(".")
        try:
            major = int(parts[0]) if len(parts) > 0 else 0
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
            return major, minor, patch
        except ValueError:
            return 0, 0, 0
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def is_version_compatible(current_version: str, constraint: str) -> bool:
    """
    Evaluates whether current_version satisfies constraint.
    Supported constraints:
      '*' -> Any version
      '>=X.Y.Z' -> Greater than or equal to X.Y.Z
      '<=X.Y.Z' -> Less than or equal to X.Y.Z
      '>X.Y.Z'  -> Strictly greater than X.Y.Z
      '<X.Y.Z'  -> Strictly less than X.Y.Z
      '==X.Y.Z' -> Exact match
      '^X.Y.Z'  -> Compatible with major version X
      'X.Y.Z'   -> Exact match
    """
    if not constraint or constraint == "*":
        return True

    curr = parse_semver(current_version)

    # Handle range combined with comma (e.g. ">=0.1.0, <1.0.0")
    if "," in constraint:
        sub_constraints = [c.strip() for c in constraint.split(",") if c.strip()]
        return all(is_version_compatible(current_version, sc) for sc in sub_constraints)

    constraint = constraint.strip()

    if constraint.startswith(">="):
        target = parse_semver(constraint[2:])
        return curr >= target
    elif constraint.startswith("<="):
        target = parse_semver(constraint[2:])
        return curr <= target
    elif constraint.startswith(">"):
        target = parse_semver(constraint[1:])
        return curr > target
    elif constraint.startswith("<"):
        target = parse_semver(constraint[1:])
        return curr < target
    elif constraint.startswith("=="):
        target = parse_semver(constraint[2:])
        return curr == target
    elif constraint.startswith("^"):
        target = parse_semver(constraint[1:])
        # ^0.2.0 allows >=0.2.0 and <1.0.0 (or <0.3.0 for zero-major)
        if target[0] == 0:
            return curr >= target and curr[1] == target[1]
        return curr >= target and curr[0] == target[0]
    else:
        # Default exact match
        target = parse_semver(constraint)
        return curr == target
