"""Constants shared by drawing-inspection modules."""

# Cross-verified against multiple independent published sources (ISO 2768-1
# tables + a GB/T-1804-specific source with matching f-grade values) as of
# 2026-07-23. NOT verified against the primary official GB/T 1804-2000 standard
# document text itself — treat as high-confidence but not
# authoritative-source-confirmed.
GB1804_TOLERANCES: dict[tuple[float, float], dict[str, float | None]] = {
    (0.5, 3.0): {"f": 0.05, "m": 0.1, "c": 0.2, "v": None},
    (3.0, 6.0): {"f": 0.05, "m": 0.1, "c": 0.3, "v": 0.5},
    (6.0, 30.0): {"f": 0.1, "m": 0.2, "c": 0.5, "v": 1.0},
    (30.0, 120.0): {"f": 0.15, "m": 0.3, "c": 0.8, "v": 1.5},
    (120.0, 400.0): {"f": 0.2, "m": 0.5, "c": 1.2, "v": 2.5},
    (400.0, 1000.0): {"f": 0.3, "m": 0.8, "c": 2.0, "v": 4.0},
    (1000.0, 2000.0): {"f": 0.5, "m": 1.2, "c": 3.0, "v": 6.0},
    (2000.0, 4000.0): {"f": None, "m": 2.0, "c": 4.0, "v": 8.0},
}
