"""Report and Document Download Routes."""

from __future__ import annotations

from pathlib import Path
from typing import List
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.api.schemas.models import ReportItem
from backend.api.services.data_loader import OUTPUTS_DIR, REPORTS_DIR, SUBMISSION_DIR

router = APIRouter(prefix="/reports", tags=["Reports"])

REPORTS_REGISTRY = {
    "methodology-pdf": {
        "title": "Official Methodology Report (PDF)",
        "category": "Publication",
        "file": SUBMISSION_DIR / "methodology_report.pdf",
        "mime_type": "application/pdf",
        "description": "Complete 8-page publication PDF with formulas, embedded charts, and Top 10 dossiers.",
    },
    "methodology-md": {
        "title": "Methodology Report (Markdown Source)",
        "category": "Source Document",
        "file": SUBMISSION_DIR / "methodology_report.md",
        "mime_type": "text/markdown",
        "description": "Full technical specification covering all 17 mandatory sections.",
    },
    "top-10-batters-csv": {
        "title": "Official Top 10 Batters (CSV)",
        "category": "Submission Dataset",
        "file": SUBMISSION_DIR / "top_10_batters.csv",
        "mime_type": "text/csv",
        "description": "Standardized CSV containing the verified Top 10 Batters in exact rank order.",
    },
    "top-10-bowlers-csv": {
        "title": "Official Top 10 Bowlers (CSV)",
        "category": "Submission Dataset",
        "file": SUBMISSION_DIR / "top_10_bowlers.csv",
        "mime_type": "text/csv",
        "description": "Standardized CSV containing the verified Top 10 Bowlers in exact rank order.",
    },
    "submission-selections": {
        "title": "Unstop Selection Reference (MD)",
        "category": "Portal Reference",
        "file": SUBMISSION_DIR / "submission_selections.md",
        "mime_type": "text/markdown",
        "description": "Formatted dropdown reference for manual entry on the Unstop portal.",
    },
    "submission-validation": {
        "title": "Independent Submission Audit (MD)",
        "category": "Quality Audit",
        "file": SUBMISSION_DIR / "submission_validation.md",
        "mime_type": "text/markdown",
        "description": "Exhaustive compliance checklist and 16-point quality gate audit.",
    },
    "evidence-manifest": {
        "title": "Evidence Traceability Manifest (MD)",
        "category": "Traceability",
        "file": SUBMISSION_DIR / "evidence_manifest.md",
        "mime_type": "text/markdown",
        "description": "Traceability mapping every table, chart, and equation to source code and data.",
    },
    "submission-zip": {
        "title": "Full Submission Package (ZIP)",
        "category": "Archive",
        "file": SUBMISSION_DIR / "superr_selector_round1_submission.zip",
        "mime_type": "application/zip",
        "description": "Clean self-contained 1.05 MB archive containing all verified submission deliverables.",
    },
}


@router.get("", response_model=List[ReportItem])
def list_reports() -> List[ReportItem]:
    """Lists all available official reports and submission files."""
    results = []
    for r_id, info in REPORTS_REGISTRY.items():
        f: Path = info["file"]
        size = f.stat().st_size if f.exists() else 0
        results.append(ReportItem(
            report_id=r_id,
            title=info["title"],
            category=info["category"],
            filename=f.name,
            file_size_bytes=size,
            mime_type=info["mime_type"],
            description=info["description"],
            download_url=f"/api/reports/{r_id}/download",
        ))
    return results


@router.get("/{report_id}/download")
def download_report(report_id: str):
    """Downloads a report with correct Content-Disposition header and MIME type, strictly protected against path traversal."""
    if report_id not in REPORTS_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Report ID '{report_id}' not found.")

    info = REPORTS_REGISTRY[report_id]
    file_path: Path = info["file"].resolve()

    # Prevent path traversal outside allowed directories
    allowed_roots = [SUBMISSION_DIR.resolve(), REPORTS_DIR.resolve(), OUTPUTS_DIR.resolve()]
    if not any(str(file_path).startswith(str(root)) for root in allowed_roots):
        raise HTTPException(status_code=403, detail="Access denied: path traversal forbidden.")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File for report '{report_id}' does not exist on disk.")

    return FileResponse(
        path=str(file_path),
        media_type=info["mime_type"],
        filename=file_path.name,
        headers={"Content-Disposition": f"attachment; filename={file_path.name}"},
    )

