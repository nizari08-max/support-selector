"""
app.py  —  JESA Piping Support Selector  (Web Application)
Run:  python app.py   then open  http://localhost:5000
"""
import os
import sys
import re

# Load .env.local (local dev overrides) before anything else.
# Requires python-dotenv (pip install python-dotenv).  Safe to skip if missing.
try:
    from dotenv import load_dotenv
    load_dotenv(".env.local")
except ImportError:
    pass

from flask import Flask, render_template, request, jsonify, Response, abort

# Allow imports from the same directory as app.py
sys.path.insert(0, os.path.dirname(__file__))

from selector import select_support        # noqa: E402
from pdf_service import get_drawing_pdf    # noqa: E402

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Map a support-code string → illustration filename (without .svg)
# Priority order is important: GH before SH, LS before S, etc.
# ---------------------------------------------------------------------------
def get_image_key(support_code: str) -> str:
    if not support_code:
        return "not_applicable"
    s = support_code.upper()
    if "DIRECT REST" in s:
        return "direct_rest"
    if re.search(r"\bGH\d", s):
        return "hold_down"
    if re.search(r"\bLS\d", s):
        return "line_stop"
    if re.search(r"\bGL\d", s):
        return "guide"
    if re.search(r"\bCF\d", s):
        return "frp_clamp"
    if re.search(r"\bSC7[123]\b", s):   # FRP saddle supports (SC71 / SC72 / SC73)
        return "frp_clamp"
    if re.search(r"\bSC\d", s):
        return "shoe_clamp"
    if re.search(r"\bSH\d", s):
        return "pipe_shoe"
    if re.search(r"\bWA\d", s):
        return "wear_pad"
    if re.search(r"\bBP\d", s):
        return "bearing_plate"
    return "not_applicable"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/select", methods=["POST"])
def api_select():
    data = request.get_json(force=True)
    try:
        result = select_support(
            nps=float(data["nps"]),
            material=str(data["material"]),
            pwht=bool(data.get("pwht", False)),
            insulation=str(data["insulation"]),
            support_function=str(data["function"]),
        )
        return jsonify({
            "success":          True,
            "support_code":     result.support_code,
            "drawings":         result.drawings,
            "drawings_labeled": result.drawings_labeled,
            "notes":            result.note_texts,
            "is_applicable":    result.is_applicable(),
            "image_key":        get_image_key(result.support_code),
            "size_range":       result.size_range,
        })
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Unexpected error: {e}"}), 500


@app.route("/api/drawing/<path:drawing_ref>")
def api_drawing(drawing_ref: str):
    """
    Extract and return a drawing page from the JESA standard PDF.

    Query parameters:
      nps  (float, optional) — selected pipe size in inches.
           When supplied, matching NPS values in the dimension table are
           highlighted yellow in the returned PDF.

    The PDF is streamed inline so the browser can display it directly
    (or the user can save it).  Filename: <drawing_ref>_<nps>in.pdf
    """
    nps = None
    nps_raw = request.args.get("nps")
    if nps_raw:
        try:
            nps = float(nps_raw)
        except ValueError:
            abort(400, description="Invalid nps parameter")

    pdf_bytes = get_drawing_pdf(drawing_ref, nps=nps)
    if pdf_bytes is None:
        abort(404, description=(
            f"Drawing '{drawing_ref}' not found. "
            "The standard PDF may not be available on this server."
        ))

    # Build a clean filename: JS-PE-DPS-0327-001_30in.pdf
    safe_ref = re.sub(r"[^A-Za-z0-9\-_]", "_", drawing_ref)
    if nps is not None:
        nps_label = int(nps) if nps == int(nps) else nps
        filename = f"{safe_ref}_{nps_label}in.pdf"
    else:
        filename = f"{safe_ref}.pdf"

    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    app.run(debug=debug, port=port, host="0.0.0.0")
