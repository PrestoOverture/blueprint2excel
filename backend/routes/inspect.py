from pathlib import Path
from tempfile import mkdtemp
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from drawing_inspector import pipeline
from drawing_inspector.models import Dimension, DrawingData, HoleFeature
from drawing_inspector.output import bubble_diagram, excel_report
from drawing_inspector.pipeline import NotVectorPDFError

router = APIRouter()

_XLSX_MEDIA_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


class DimensionOut(BaseModel):
    nominal: float
    upper_deviation: float | None
    lower_deviation: float | None
    tolerance_grade: str | None
    dimension_type: str
    x: float
    y: float
    bubble_id: int | None


class HoleFeatureOut(BaseModel):
    label: str
    hole_type: str
    primary_diameter: float | str
    depth: float | str
    counterbore_diameter: float | None
    counterbore_depth: float | None
    thread_spec: str | None
    pilot_hole: float | None
    quantity: int
    back_side: bool


class InspectionResult(BaseModel):
    job_id: str
    drawing_number: str
    part_name: str
    material: str
    scale: str
    date: str
    tolerance_standard: str
    tech_requirements: list[str]
    dimensions: list[DimensionOut]
    hole_features: list[HoleFeatureOut]
    excel_download_url: str
    bubble_diagram_download_url: str


class _JobFiles(BaseModel):
    temp_directory: Path
    excel: Path
    bubble_diagram: Path


_jobs: dict[str, _JobFiles] = {}


@router.post("/inspect", response_model=InspectionResult)
async def inspect_drawing(
    file: Annotated[UploadFile, File()],
) -> InspectionResult:
    temp_directory = Path(mkdtemp())
    source_pdf = temp_directory / "source.pdf"
    source_pdf.write_bytes(await file.read())

    try:
        drawing_data = pipeline.assemble_drawing_data(source_pdf)
    except NotVectorPDFError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    excel_path = temp_directory / "inspection-report.xlsx"
    bubble_diagram_path = temp_directory / "bubble-diagram.pdf"
    excel_report.write_excel_report(drawing_data, excel_path)
    bubble_diagram.render_bubble_diagram(
        drawing_data, source_pdf, bubble_diagram_path
    )

    job_id = uuid4().hex
    _jobs[job_id] = _JobFiles(
        temp_directory=temp_directory,
        excel=excel_path,
        bubble_diagram=bubble_diagram_path,
    )
    return _inspection_result(job_id, drawing_data)


@router.get("/inspect/{job_id}/excel", response_class=FileResponse)
def download_excel(job_id: str) -> FileResponse:
    job = _get_job(job_id)
    return FileResponse(
        job.excel,
        media_type=_XLSX_MEDIA_TYPE,
        filename=job.excel.name,
    )


@router.get("/inspect/{job_id}/bubble-diagram", response_class=FileResponse)
def download_bubble_diagram(job_id: str) -> FileResponse:
    job = _get_job(job_id)
    return FileResponse(
        job.bubble_diagram,
        media_type="application/pdf",
        filename=job.bubble_diagram.name,
    )


def _get_job(job_id: str) -> _JobFiles:
    try:
        return _jobs[job_id]
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Job not found") from error


def _inspection_result(
    job_id: str, drawing_data: DrawingData
) -> InspectionResult:
    return InspectionResult(
        job_id=job_id,
        drawing_number=drawing_data.drawing_number,
        part_name=drawing_data.part_name,
        material=drawing_data.material,
        scale=drawing_data.scale,
        date=drawing_data.date,
        tolerance_standard=drawing_data.tolerance_standard,
        tech_requirements=drawing_data.tech_requirements,
        dimensions=[
            _dimension_out(dimension) for dimension in drawing_data.dimensions
        ],
        hole_features=[
            _hole_feature_out(hole) for hole in drawing_data.hole_features
        ],
        excel_download_url=f"/inspect/{job_id}/excel",
        bubble_diagram_download_url=f"/inspect/{job_id}/bubble-diagram",
    )


def _dimension_out(dimension: Dimension) -> DimensionOut:
    return DimensionOut(
        nominal=dimension.nominal,
        upper_deviation=dimension.upper_deviation,
        lower_deviation=dimension.lower_deviation,
        tolerance_grade=dimension.tolerance_grade,
        dimension_type=dimension.dimension_type,
        x=dimension.x,
        y=dimension.y,
        bubble_id=dimension.bubble_id,
    )


def _hole_feature_out(hole: HoleFeature) -> HoleFeatureOut:
    return HoleFeatureOut(
        label=hole.label,
        hole_type=hole.hole_type,
        primary_diameter=hole.primary_diameter,
        depth=hole.depth,
        counterbore_diameter=hole.counterbore_diameter,
        counterbore_depth=hole.counterbore_depth,
        thread_spec=hole.thread_spec,
        pilot_hole=hole.pilot_hole,
        quantity=hole.quantity,
        back_side=hole.back_side,
    )
