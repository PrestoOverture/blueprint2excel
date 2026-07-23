"""Constants shared by drawing-inspection modules."""

# ⚠️ UNVERIFIED PLACEHOLDER TABLE — only (6-30mm, grade m)=0.1 and
# (400-1000mm, grade m)=0.4 are confirmed against docs/roadmap.md. All other
# cells are unverified estimates and MUST be checked against the authoritative
# GB/T 1804 standard text before this table is used for real inspection
# decisions.
GB1804_TOLERANCES: dict[tuple[float, float], dict[str, float]] = {
    (0.5, 3.0): {"f": 0.02, "m": 0.05, "c": 0.1, "v": 0.2},
    (3.0, 6.0): {"f": 0.03, "m": 0.075, "c": 0.15, "v": 0.3},
    (6.0, 30.0): {"f": 0.05, "m": 0.1, "c": 0.2, "v": 0.4},
    (30.0, 120.0): {"f": 0.08, "m": 0.15, "c": 0.3, "v": 0.6},
    (120.0, 400.0): {"f": 0.1, "m": 0.25, "c": 0.5, "v": 1.0},
    (400.0, 1000.0): {"f": 0.2, "m": 0.4, "c": 0.8, "v": 1.6},
    (1000.0, 2000.0): {"f": 0.3, "m": 0.6, "c": 1.2, "v": 2.4},
    (2000.0, 4000.0): {"f": 0.5, "m": 1.0, "c": 2.0, "v": 4.0},
}
