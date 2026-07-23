from pathlib import Path

import pymupdf

from drawing_inspector.detector import is_vector_pdf

FIXTURE = Path(__file__).parent / "fixtures" / "HJMZ01-01-01.pdf"


def test_cad_pdf_with_embedded_fonts_is_vector() -> None:
    assert is_vector_pdf(FIXTURE)


def test_image_only_pdf_is_not_vector(tmp_path: Path) -> None:
    image_pdf = tmp_path / "image-only.pdf"
    image = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 10, 10), False)
    image.clear_with(255)

    document = pymupdf.open()
    page = document.new_page()
    page.insert_image(page.rect, stream=image.tobytes("png"))
    document.save(image_pdf)
    document.close()

    assert not is_vector_pdf(image_pdf)
