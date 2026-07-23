import pytest

from drawing_inspector.tolerance.gb1804 import lookup_gb1804


def test_lookup_confirmed_400_to_1000_grade_m_value() -> None:
    assert lookup_gb1804(920, "m") == (0.4, -0.4)


def test_lookup_confirmed_6_to_30_grade_m_value() -> None:
    assert lookup_gb1804(20, "m") == (0.1, -0.1)


def test_lookup_accepts_case_insensitive_grade() -> None:
    assert lookup_gb1804(20, "M") == (0.1, -0.1)


@pytest.mark.parametrize("nominal", [0.49, 5000])
def test_lookup_rejects_nominal_outside_table(nominal: float) -> None:
    with pytest.raises(ValueError, match="outside"):
        lookup_gb1804(nominal, "m")


def test_lookup_rejects_invalid_grade() -> None:
    with pytest.raises(ValueError, match="invalid"):
        lookup_gb1804(20, "x")
