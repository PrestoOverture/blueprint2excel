"""Backend API tests.

Pytest imports this directory as the top-level ``backend`` package, so expose the
application package on the same package search path during test collection.
"""

from pathlib import Path

__path__.append(str(Path(__file__).parents[2] / "backend"))
