"""Flask Blueprint for the copyable SCLL Phase 1 module."""

from __future__ import annotations

import json
import os
import re
import uuid
from pathlib import Path

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, send_file, url_for
from werkzeug.utils import secure_filename

from ..backend.classifier import process_scll_phase1

scll_bp = Blueprint(
    "scll",
    __name__,
    template_folder="../templates",
    static_folder="../static",
)

_JOBS: dict[str, dict] = {}

_PAGE_CONTEXT = {
    "active_page": "scll",
    "tool_title": "Critical Line List Classifier",
    "tool_subtitle": "Line List Criticality Classification · Phase 1",
}


def _upload_folder() -> Path:
    return Path(current_app.config.get("SCLL_UPLOAD_FOLDER", current_app.instance_path)) / "scll_uploads"


def _output_folder() -> Path:
    return Path(current_app.config.get("SCLL_OUTPUT_FOLDER", current_app.instance_path)) / "scll_outputs"


def _summary_path(job_id: str) -> Path:
    return _output_folder() / f"{job_id}_summary.json"


def _save_job(job_id: str, job: dict) -> None:
    _JOBS[job_id] = job
    _output_folder().mkdir(parents=True, exist_ok=True)
    _summary_path(job_id).write_text(json.dumps(job, indent=2), encoding="utf-8")


def _load_job(job_id: str) -> dict | None:
    if job_id in _JOBS:
        return _JOBS[job_id]
    path = _summary_path(job_id)
    if not path.is_file():
        return None
    job = json.loads(path.read_text(encoding="utf-8"))
    _JOBS[job_id] = job
    return job


@scll_bp.get("/scll")
def scll_home():
    return render_template("scll/upload.html", **_PAGE_CONTEXT)


@scll_bp.post("/scll/upload")
def scll_upload():
    wants_json = request.accept_mimetypes.best == "application/json"

    def _fail(message: str, status: int):
        if wants_json:
            return jsonify({"error": message}), status
        return render_template("scll/upload.html", error=message, **_PAGE_CONTEXT), status

    file = request.files.get("line_list") or request.files.get("file")
    if not file or not file.filename:
        return _fail("No Excel line list uploaded.", 400)
    if not file.filename.lower().endswith((".xlsx", ".xlsm")):
        return _fail("Only .xlsx or .xlsm line lists are accepted.", 400)

    job_id = uuid.uuid4().hex
    upload_dir = _upload_folder() / job_id
    output_dir = _output_folder() / job_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_stem, raw_ext = os.path.splitext(file.filename)
    raw_stem = re.sub(r"(\s*\(\d+\))+$", "", raw_stem).strip()  # strip browser "(1)" dup-download markers
    filename = secure_filename(f"{raw_stem}{raw_ext}") or secure_filename(file.filename)
    input_path = upload_dir / filename
    file.save(input_path)

    try:
        summary = process_scll_phase1(str(input_path), str(output_dir))
    except Exception as exc:
        _save_job(job_id, {"status": "failed", "error": str(exc)})
        return _fail(f"Failed to process line list: {exc}", 500)

    job = {
        "status": "complete",
        "input_path": str(input_path),
        "summary": summary,
        "output_excel_path": summary["output_excel_path"],
    }
    _save_job(job_id, job)

    if wants_json:
        return jsonify({
            "job_id": job_id,
            "results_url": url_for("scll.scll_results", job_id=job_id),
            "download_url": url_for("scll.scll_download", job_id=job_id),
            "summary": summary,
        })
    return redirect(url_for("scll.scll_results", job_id=job_id), code=303)


@scll_bp.get("/scll/results/<job_id>")
def scll_results(job_id: str):
    job = _load_job(job_id)
    if not job:
        if request.accept_mimetypes.best == "application/json":
            return jsonify({"error": "SCLL job not found"}), 404
        return render_template("scll/upload.html", error="SCLL job not found — please upload again.", **_PAGE_CONTEXT), 404
    if request.accept_mimetypes.best == "application/json":
        return jsonify(job)
    return render_template("scll/results.html", job_id=job_id, job=job, **_PAGE_CONTEXT)


@scll_bp.get("/scll/download/<job_id>")
def scll_download(job_id: str):
    job = _load_job(job_id)
    if not job or job.get("status") != "complete":
        return jsonify({"error": "SCLL output not available"}), 404

    output_root = _output_folder().resolve()
    output_path = Path(job["output_excel_path"]).resolve()
    if os.path.commonpath([str(output_root), str(output_path)]) != str(output_root):
        return jsonify({"error": "Invalid output path"}), 400
    if not output_path.is_file():
        return jsonify({"error": "Output Excel file not found"}), 404

    return send_file(output_path, as_attachment=True, download_name=output_path.name)


# Future Phase 2 CN routes can be registered separately after Phase 1 is complete.
