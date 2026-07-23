"""GB/T 1804 general-tolerance lookup.

⚠️ UNVERIFIED PLACEHOLDER TABLE — only (6-30mm, grade m)=0.1 and
(400-1000mm, grade m)=0.4 are confirmed against docs/roadmap.md. All other
cells are unverified estimates and MUST be checked against the authoritative
GB/T 1804 standard text before this table is used for real inspection
decisions.
"""

from drawing_inspector.constants import GB1804_TOLERANCES

_VALID_GRADES = frozenset({"f", "m", "c", "v"})
_MIN_NOMINAL = 0.5
_MAX_NOMINAL = 4000.0


def lookup_gb1804(nominal: float, grade: str) -> tuple[float, float]:
    """Return symmetric upper and lower deviations for a nominal dimension."""
    normalized_grade = grade.lower()
    if normalized_grade not in _VALID_GRADES:
        msg = (
            f"invalid GB/T 1804 grade {grade!r}; "
            f"expected one of {sorted(_VALID_GRADES)}"
        )
        raise ValueError(msg)

    if not _MIN_NOMINAL <= nominal <= _MAX_NOMINAL:
        msg = (
            f"nominal dimension {nominal!r} mm is outside the GB/T 1804 "
            f"lookup range {_MIN_NOMINAL}-{_MAX_NOMINAL} mm"
        )
        raise ValueError(msg)

    for (lower_bound, upper_bound), tolerances in GB1804_TOLERANCES.items():
        if lower_bound <= nominal <= upper_bound:
            tolerance = tolerances[normalized_grade]
            return tolerance, -tolerance

    msg = f"no GB/T 1804 tolerance range contains {nominal!r} mm"
    raise ValueError(msg)
