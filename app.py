"""
app.py  —  JESA Piping Support Selector  (Web Application)
Run:  python app.py   then open  http://localhost:5000
"""
import os
import sys
import re
from urllib.parse import quote

# Load .env.local (local dev overrides) before anything else.
# Requires python-dotenv (pip install python-dotenv).  Safe to skip if missing.
try:
    from dotenv import load_dotenv
    load_dotenv(".env.local")
except ImportError:
    pass

from flask import Flask, render_template, request, jsonify, Response, abort, send_from_directory

# Allow imports from the same directory as app.py
sys.path.insert(0, os.path.dirname(__file__))

from selector import select_support                    # noqa: E402
from pdf_service import get_drawing_pdf                # noqa: E402
from span_calculator import calculate_span             # noqa: E402
from material_classes import resolve_class, classes_for_api  # noqa: E402
from pipe_flange_data import DN_SIZES, FLANGE_RATINGS  # noqa: E402
from rack_calculator import calculate_rack             # noqa: E402
from rack_diagram import generate_diagram              # noqa: E402

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Map a support-code string → illustration filename (without .svg)
# Priority order is important: GH before SH, LS before S, etc.
# ---------------------------------------------------------------------------
def get_image_key(support_code: str) -> str:
    if not support_code:
        return "not_applicable"
    s = support_code.upper()
    exact_supports = re.findall(r"\b(SH0[1-5]|SC0[1-8])\b", s)
    exact_unique = []
    for code in exact_supports:
        if code not in exact_unique:
            exact_unique.append(code)
    if len(exact_unique) == 1:
        return exact_unique[0].lower()
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
        piping_class = str(data["piping_class"]).strip().upper() if data.get("piping_class") else None
        result = select_support(
            nps=float(data["nps"]),
            material=str(data["material"]),
            pwht=bool(data.get("pwht", False)),
            insulation=str(data["insulation"]),
            support_function=str(data["function"]),
            refinements=data.get("refinements") or {},
        )
        return jsonify({
            "success":          True,
            "status":           result.status,
            "support_code":     result.support_code,
            "drawings":         result.drawings,
            "drawings_labeled": result.drawings_labeled,
            "notes":            result.note_texts,
            "refinement_questions": result.refinement_questions,
            "applied_refinements":  result.applied_refinements,
            "refinement_warnings":  result.refinement_warnings,
            "is_applicable":    result.is_applicable(),
            "image_key":        get_image_key(result.support_code),
            "size_range":       result.size_range,
            "piping_class":     piping_class,
        })
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Unexpected error: {e}"}), 500


@app.route("/span")
def span_page():
    return render_template("span_calculator.html", mpms_data=classes_for_api())


@app.route("/api/span", methods=["POST"])
def api_span():
    data = request.get_json(force=True)
    try:
        result = calculate_span(
            nps=float(data["nps"]),
            material=str(data["material"]),
            condition=str(data.get("condition", "bare_empty")),
            schedule=str(data.get("schedule", "sch40")),
            temp_range=str(data.get("temp_range", "t1")),
        )
        return jsonify({"success": True, **result})
    except (KeyError, ValueError) as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Unexpected error: {e}"}), 500


@app.route("/reference")
def reference_page():
    return render_template("reference.html")


@app.route("/api/mpms-classes")
def api_mpms_classes():
    """Return all MPMS piping class codes grouped by span-material category."""
    return jsonify(classes_for_api())


@app.route("/api/resolve-class/<code>")
def api_resolve_class(code: str):
    """Resolve a single MPMS class code to its span material mapping."""
    result = resolve_class(code)
    if result is None:
        return jsonify({"found": False, "code": code.upper()}), 404
    return jsonify({"found": True, **result})


@app.route("/standard-pdf")
def serve_standard_pdf():
    """Serve the JESA piping support standard PDF from the project root."""
    return send_from_directory(
        os.path.dirname(os.path.abspath(__file__)),
        "QW2507-00-PE-STD-00001.pdf",
        mimetype="application/pdf",
    )


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

    pdf_bytes = get_drawing_pdf(drawing_ref, nps=nps, base_url=request.url_root)
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


@app.route("/drawing-link/<path:drawing_ref>")
def drawing_link(drawing_ref: str):
    """Open a drawing link from inside a PDF without replacing the PDF tab."""
    nps_raw = request.args.get("nps")
    query = f"?nps={re.sub(r'[^0-9.]', '', nps_raw)}" if nps_raw else ""
    target = f"/api/drawing/{quote(drawing_ref, safe='')}{query}"
    return Response(
        f"""<!doctype html>
<html>
<head><meta charset="utf-8"><title>Opening drawing...</title></head>
<body>
<script>
  const target = {target!r};
  window.open(target, "_blank", "noopener");
  history.back();
</script>
</body>
</html>""",
        mimetype="text/html",
    )


# ---------------------------------------------------------------------------
# Rack Width Calculator routes
# ---------------------------------------------------------------------------
@app.route('/rack-calculator', methods=['GET'])
def rack_calculator():
    return render_template(
        'rack_calculator.html',
        dn_sizes=DN_SIZES,
        flange_ratings=FLANGE_RATINGS,
        pipes=None,
        result=None,
        diagram=None,
        options={'expansion_pct': 20, 'steel_column_mm': 190},
        error=None,
    )


@app.route('/rack-calculator', methods=['POST'])
def rack_calculate():
    dns = request.form.getlist('dn')
    ratings = request.form.getlist('rating')
    insulations = request.form.getlist('insulation')
    try:
        expansion_pct = int(request.form.get('expansion_pct', 20))
        steel_column_mm = int(request.form.get('steel_column_mm', 190))
    except ValueError:
        expansion_pct, steel_column_mm = 20, 190
    options = {'expansion_pct': expansion_pct, 'steel_column_mm': steel_column_mm}
    pipes = []
    for dn, rating, ins in zip(dns, ratings, insulations):
        try:
            pipes.append({'dn': int(dn), 'rating': int(rating), 'insulation': int(ins)})
        except (ValueError, TypeError):
            return render_template(
                'rack_calculator.html',
                dn_sizes=DN_SIZES, flange_ratings=FLANGE_RATINGS,
                pipes=None, result=None, diagram=None,
                options=options,
                error="Invalid input — please check all fields are filled with numbers.",
            )
    try:
        result = calculate_rack(pipes, expansion_pct=expansion_pct, steel_column_mm=steel_column_mm)
    except (ValueError, KeyError) as e:
        return render_template(
            'rack_calculator.html',
            dn_sizes=DN_SIZES, flange_ratings=FLANGE_RATINGS,
            pipes=pipes, result=None, diagram=None,
            options=options, error=str(e),
        )
    diagram = generate_diagram(pipes, result)
    return render_template(
        'rack_calculator.html',
        dn_sizes=DN_SIZES, flange_ratings=FLANGE_RATINGS,
        pipes=pipes, result=result, diagram=diagram,
        options=options, error=None,
    )


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    app.run(debug=debug, port=port, host="0.0.0.0")
