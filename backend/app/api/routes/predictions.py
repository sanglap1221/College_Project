"""FastAPI routes for the Complete Jyotish Prediction Engine, AI Validation,
and English Prediction Reports.
"""

import logging
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response
from fastapi.responses import FileResponse, HTMLResponse
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, Field

from app.auth_middleware import get_current_user, get_optional_user
from app.predictions.service import (
    generate_prediction_report,
    get_prediction_by_id,
    regenerate_prediction_section,
    save_manual_edit,
    compute_chart_hash,
)
from app.predictions.engine import ai_service

logger = logging.getLogger("astro_app.predictions.routes")

router = APIRouter(prefix="/api/predictions", tags=["predictions"])

# Memory tracker for prediction PDF compilation tasks
pred_pdf_statuses: Dict[str, Dict[str, Any]] = {}
pred_pdf_payloads: Dict[str, Dict[str, Any]] = {}


# ── Request / Response Schemas ──

class PredictionGenerateRequest(BaseModel):
    report_id: Optional[str] = None
    customer_data: Dict[str, Any]
    use_ai: bool = False
    provider: Optional[str] = None
    model: Optional[str] = None
    topics: Optional[List[str]] = None
    ref_date: Optional[str] = None


class RegenerateSectionRequest(BaseModel):
    topic: str
    use_ai: bool = False
    provider: Optional[str] = None
    model: Optional[str] = None
    customer_data: Optional[Dict[str, Any]] = None


class SectionEditRequest(BaseModel):
    topic: str
    content: str


class AiConfigRequest(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None


# ── Prediction Endpoints ──

@router.post("/generate")
def generate_prediction_endpoint(
    payload: PredictionGenerateRequest,
    current_user: Optional[dict] = Depends(get_optional_user),
) -> Dict[str, Any]:
    """Generate or recalculate complete Jyotish prediction report."""
    try:
        report_id = payload.report_id or f"pred-{uuid.uuid4().hex[:10]}"
        report = generate_prediction_report(
            report_id=report_id,
            payload=payload.customer_data,
            use_ai=payload.use_ai,
            topics=payload.topics,
            ref_date=payload.ref_date,
            provider=payload.provider,
            model=payload.model,
        )
        return report
    except ValueError as exc:
        logger.error(f"Validation error generating prediction: {exc}")
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"Unexpected error generating prediction: {exc}")
        raise HTTPException(status_code=500, detail=f"Prediction generation failed: {exc}") from exc


@router.get("/ai-config")
def get_ai_config_endpoint(
    current_user: Optional[dict] = Depends(get_optional_user),
) -> Dict[str, Any]:
    """Retrieve available AI providers, configuration status, and model lists."""
    return ai_service.list_providers_status()


@router.post("/ai-config")
def update_ai_config_endpoint(
    payload: AiConfigRequest,
    current_user: Optional[dict] = Depends(get_optional_user),
) -> Dict[str, Any]:
    """Update active AI provider, model, or API key."""
    updated = ai_service.update_runtime_ai_config(
        provider=payload.provider,
        model=payload.model,
        api_key=payload.api_key,
        base_url=payload.base_url,
    )
    return {
        "status": "success",
        "active_provider": updated["provider"],
        "active_model": updated["model"],
        "is_configured": updated["is_configured"],
    }


@router.get("/{report_id}")
def get_prediction_endpoint(
    report_id: str,
    chart_hash: Optional[str] = Query(None),
    current_user: Optional[dict] = Depends(get_optional_user),
) -> Dict[str, Any]:
    """Fetch saved prediction report and check if outdated."""
    doc = get_prediction_by_id(report_id, current_hash=chart_hash)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Prediction report '{report_id}' not found.")
    return doc


@router.post("/{report_id}/regenerate-section")
def regenerate_section_endpoint(
    report_id: str,
    payload: RegenerateSectionRequest,
    current_user: Optional[dict] = Depends(get_optional_user),
) -> Dict[str, Any]:
    """Regenerate a single prediction section while keeping other sections intact."""
    try:
        updated_doc = regenerate_prediction_section(
            report_id=report_id,
            topic=payload.topic,
            use_ai=payload.use_ai,
            provider=payload.provider,
            model=payload.model,
            payload=payload.customer_data,
        )
        return updated_doc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.error(f"Failed to regenerate section {payload.topic}: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.put("/{report_id}/section")
def edit_section_endpoint(
    report_id: str,
    payload: SectionEditRequest,
    current_user: Optional[dict] = Depends(get_optional_user),
) -> Dict[str, Any]:
    """Save manual astrologer edits to a specific prediction section."""
    success = save_manual_edit(report_id, payload.topic, payload.content)
    if not success:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' or section '{payload.topic}' not found.")
    return {"status": "success", "message": f"Section '{payload.topic}' saved successfully."}


# ── Prediction PDF Rendering & Compilation ──

def compile_pred_pdf_task(payload: Dict[str, Any], report_id: str):
    """Playwright PDF compilation background task for Prediction report."""
    logger = logging.getLogger("astro_app.pred_pdf_task")
    filename = f"prediction_{report_id}.pdf"

    try:
        pred_pdf_statuses[report_id] = {"status": "compiling", "progress": 25}

        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            templates_dir = Path(sys._MEIPASS) / "app" / "pdf" / "templates"
        else:
            templates_dir = Path(__file__).resolve().parents[2] / "pdf" / "templates"

        env = Environment(loader=FileSystemLoader(str(templates_dir)))
        template = env.get_template("prediction_report.html")
        html_content = template.render(**payload)

        pred_pdf_statuses[report_id] = {"status": "compiling", "progress": 50}

        if getattr(sys, 'frozen', False):
            backend_root = Path(sys.executable).parent
        else:
            backend_root = Path(__file__).resolve().parents[3]
        generated_dir = backend_root / "generated"
        generated_dir.mkdir(exist_ok=True)
        output_path = generated_dir / filename

        pred_pdf_statuses[report_id] = {"status": "compiling", "progress": 75}

        # Render PDF via Playwright
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"]
            )
            page = browser.new_page()
            page.set_content(html_content, wait_until="networkidle")
            page.pdf(
                path=str(output_path),
                format="A4",
                print_background=True,
                margin={"top": "12mm", "right": "12mm", "bottom": "12mm", "left": "12mm"},
            )
            browser.close()

        pred_pdf_statuses[report_id] = {"status": "ready", "progress": 100, "filename": filename}
        logger.info(f"Successfully compiled prediction PDF: {output_path}")

    except Exception as exc:
        logger.error(f"Error compiling prediction PDF for {report_id}: {exc}")
        pred_pdf_statuses[report_id] = {"status": "failed", "progress": 0, "error": str(exc)}


@router.post("/render-pdf")
def render_prediction_pdf_endpoint(
    payload: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: Optional[dict] = Depends(get_optional_user),
) -> Dict[str, Any]:
    """Render prediction report as HTML preview and trigger background PDF compilation."""
    try:
        report_id = payload.get("report_id") or f"pred-{uuid.uuid4().hex[:8]}"

        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            templates_dir = Path(sys._MEIPASS) / "app" / "pdf" / "templates"
        else:
            templates_dir = Path(__file__).resolve().parents[2] / "pdf" / "templates"

        env = Environment(loader=FileSystemLoader(str(templates_dir)))
        template = env.get_template("prediction_report.html")
        html_content = template.render(**payload)

        filename = f"prediction_{report_id}.pdf"

        # Track payload and start compilation in background
        pred_pdf_payloads[report_id] = payload
        pred_pdf_statuses[report_id] = {"status": "pending", "progress": 0}
        background_tasks.add_task(compile_pred_pdf_task, payload, report_id)

        return {
            "html": html_content,
            "pdf_url": f"/api/predictions/download-pdf/{filename}",
            "report_id": report_id,
        }
    except Exception as exc:
        logger.error(f"Error rendering prediction HTML: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/download-pdf/{filename}")
def download_prediction_pdf_endpoint(
    filename: str,
    name: Optional[str] = Query(None),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    """Download compiled prediction PDF."""
    if getattr(sys, 'frozen', False):
        backend_root = Path(sys.executable).parent
    else:
        backend_root = Path(__file__).resolve().parents[3]
    generated_dir = backend_root / "generated"
    file_path = generated_dir / filename

    if not file_path.exists():
        # Check if we can compile synchronously
        report_id = filename.replace("prediction_", "").replace(".pdf", "")
        if report_id in pred_pdf_payloads:
            compile_pred_pdf_task(pred_pdf_payloads[report_id], report_id)

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Prediction PDF file not found or still compiling.")

    download_name = name or filename
    if not download_name.endswith(".pdf"):
        download_name += ".pdf"

    return FileResponse(
        path=str(file_path),
        filename=download_name,
        media_type="application/pdf",
    )
