from os import PathLike
from pathlib import Path

import pymupdf


def is_vector_pdf(pdf_path: str | PathLike[str]) -> bool:
    """Return whether any page in a PDF references an embedded font."""

    with pymupdf.open(Path(pdf_path)) as document:  # type: ignore[no-untyped-call]
        return any(page.get_fonts() for page in document)
