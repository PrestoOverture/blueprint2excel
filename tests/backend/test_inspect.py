from pathlib import Path

import pymupdf
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)
FIXTURE = Path(__file__).parents[1] / "fixtures" / "HJMZ01-01-01.pdf"


def test_health_reports_backend_is_ready() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_inspect_returns_drawing_data_and_downloadable_reports() -> None:
    with FIXTURE.open("rb") as pdf_file:
        response = client.post(
            "/inspect",
            files={"file": ("HJMZ01-01-01.pdf", pdf_file, "application/pdf")},
        )

    assert response.status_code == 200
    result = response.json()
    assert result["drawing_number"] == "HJMZ01-01-01"
    assert len(result["dimensions"]) == 18
    assert len(result["hole_features"]) == 11

    excel_response = client.get(result["excel_download_url"])
    assert excel_response.status_code == 200
    assert excel_response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert excel_response.content.startswith(b"PK")

    diagram_response = client.get(result["bubble_diagram_download_url"])
    assert diagram_response.status_code == 200
    assert diagram_response.headers["content-type"].startswith("application/pdf")
    assert diagram_response.content.startswith(b"%PDF")


def test_inspect_rejects_image_only_pdf(tmp_path: Path) -> None:
    image_pdf = tmp_path / "image-only.pdf"
    image = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 10, 10), False)
    image.clear_with(255)

    document = pymupdf.open()
    page = document.new_page()
    page.insert_image(page.rect, stream=image.tobytes("png"))
    document.save(image_pdf)
    document.close()

    with image_pdf.open("rb") as pdf_file:
        response = client.post(
            "/inspect",
            files={"file": ("image-only.pdf", pdf_file, "application/pdf")},
        )

    assert response.status_code == 422
    assert "扫描件" in response.json()["detail"]


def test_unknown_job_excel_download_returns_not_found() -> None:
    response = client.get("/inspect/not-a-real-job/excel")

    assert response.status_code == 404
