"""GB/T 1804 general-tolerance lookup.

Cross-verified against multiple independent published sources (ISO 2768-1
tables + a GB/T-1804-specific source with matching f-grade values) as of
2026-07-23. NOT verified against the primary official GB/T 1804-2000 standard
document text itself — treat as high-confidence but not
authoritative-source-confirmed.
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
            if tolerance is None:
                msg = (
                    f"GB/T 1804 grade {normalized_grade!r} has no tolerance "
                    f"for nominal dimension {nominal!r} mm"
                )
                raise ValueError(msg)
            return tolerance, -tolerance

    msg = f"no GB/T 1804 tolerance range contains {nominal!r} mm"
    raise ValueError(msg)
