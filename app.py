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
from drawing_index import get_related_drawings, label_drawings  # noqa: E402
from span_calculator import calculate_span             # noqa: E402
from material_classes import resolve_class, classes_for_api  # noqa: E402
from pipe_flange_data import DN_SIZES, FLANGE_RATINGS, rating_label  # noqa: E402
from rack_calculator import calculate_rack             # noqa: E402
from rack_diagram import generate_diagram              # noqa: E402
from rack_dxf import generate_dxf                      # noqa: E402
from structural_profiles import get_profile_width, profiles_for_js  # noqa: E402

_PROFILES_JS = profiles_for_js()   # built once at startup

app = Flask(__name__)


RATING_LABELS = {str(r): rating_label(r) for r in FLANGE_RATINGS}


def _normalize_rating(raw):
    s = str(raw).strip()
    try:
        return int(s)
    except ValueError:
        return s


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
    if re.search(r"\bFF71\b", s):        # FRP Flanged Valve Holder
        return "frp_flange_holder"
    if re.search(r"\bFF\d", s):         # Flange Frame (FF01–FF06)
        return "flange_frame"
    if re.search(r"\bWL0[3-6]\b", s):
        return "vertical_lug"
    if re.search(r"\bRC71\b", s):
        return "rc71"
    if re.search(r"\bRC72\b", s):
        return "rc72"
    if re.search(r"\bRC73\b", s):
        return "rc73"
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
    """Landing page / workspace dashboard."""
    return render_template("landing.html", active_page="landing")


@app.route("/support-selector")
def support_selector():
    """Pipe Support Selector tool."""
    return render_template(
        "index.html",
        active_page="support-selector",
        tool_title="Pipe Support Selector",
        tool_subtitle="Engineering Reference Tool · JESA Standard",
        footer_title="Pipe Support Selector — Engineering Tool",
        footer_dept="Piping Department · JESA",
    )


@app.route("/api/select", methods=["POST"])
def api_select():
    data = request.get_json(force=True)
    try:
        piping_class      = str(data["piping_class"]).strip().upper() if data.get("piping_class") else None
        is_flange    = bool(data.get("is_flange", False))
        flange_class = data.get("flange_class")  # int or None; ignored for FRP
        pipe_orientation = data.get("pipe_orientation", "horizontal")
        vertical_restraint = data.get("vertical_restraint")
        frp_vertical_support = data.get("frp_vertical_support")
        result = select_support(
            nps=float(data["nps"]),
            material=str(data["material"]),
            pwht=bool(data.get("pwht", False)),
            insulation=str(data["insulation"]),
            support_function=str(data["function"]),
            refinements=data.get("refinements") or {},
            is_flange=is_flange,
            flange_class=flange_class,
            pipe_orientation=pipe_orientation,
            vertical_restraint=vertical_restraint,
            frp_vertical_support=frp_vertical_support,
        )
        related_drawings = get_related_drawings(result.drawings)
        return jsonify({
            "success":          True,
            "status":           result.status,
            "support_code":     result.support_code,
            "drawings":         result.drawings,
            "drawings_labeled": result.drawings_labeled,
            "related_drawings":         related_drawings,
            "related_drawings_labeled": label_drawings(related_drawings),
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
    return render_template(
        "span_calculator.html",
        active_page="span",
        tool_title="Support Span Calculator",
        tool_subtitle="Span Verification per KS-PE-SPC-0073",
        footer_title="Support Span Calculator — Engineering Tool",
        footer_dept="Piping Department · JESA",
        mpms_data=classes_for_api(),
    )


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
    return render_template(
        "reference.html",
        active_page="reference",
        tool_title="Reference Tables",
        tool_subtitle="Standards & Lookup Library",
        footer_title="Reference Tables — Engineering Tool",
        footer_dept="Piping Department · JESA",
    )


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


@app.route("/api/support-illustration/<image_key>.svg")
def api_support_illustration(image_key: str):
    """Serve support SVGs with small visual-only label substitutions."""
    allowed = {"flange_frame", "frp_flange_holder"}
    if image_key not in allowed:
        abort(404)

    support_code = request.args.get("code", "").upper()
    if image_key == "flange_frame" and not re.fullmatch(r"FF0[1-6]", support_code):
        support_code = "FF01"
    if image_key == "frp_flange_holder":
        support_code = "FF71"

    svg_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "static",
        "images",
        "supports",
        f"{image_key}.svg",
    )
    if not os.path.isfile(svg_path):
        abort(404)

    with open(svg_path, "r", encoding="utf-8") as f:
        svg = f.read().replace("FF_CODE", support_code)

    return Response(svg, mimetype="image/svg+xml")


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
        active_page="rack-calculator",
        tool_title="Pipe Rack Width Calculator",
        tool_subtitle="Arrangement & DXF Export",
        footer_title="Rack Calculator — Engineering Tool",
        footer_dept="Piping Department · JESA",
        dn_sizes=DN_SIZES,
        flange_ratings=FLANGE_RATINGS,
        rating_labels=RATING_LABELS,
        pipes=None,
        result=None,
        diagram=None,
        options={
            'expansion_pct': 20,
            'profile_family': 'HEA',
            'profile_size': '300',
            'steel_column_mm': 300,
            'spare_space_location': 'right',
        },
        profiles_for_js=_PROFILES_JS,
        error=None,
    )


@app.route('/rack-calculator', methods=['POST'])
def rack_calculate():
    dns = request.form.getlist('dn')
    ratings = request.form.getlist('rating')
    insulations = request.form.getlist('insulation')

    try:
        expansion_pct = int(request.form.get('expansion_pct', 20))
    except ValueError:
        expansion_pct = 20

    profile_family = request.form.get('profile_family', 'HEA').strip()
    profile_size   = request.form.get('profile_size', '300').strip()

    spare_space_location = request.form.get('spare_space_location', 'right').strip()
    if spare_space_location not in ('right', 'center'):
        spare_space_location = 'right'

    if profile_family.lower() == 'custom':
        try:
            steel_column_mm = int(request.form.get('steel_column_mm', 330))
        except (ValueError, TypeError):
            steel_column_mm = 330
        profile_family = 'custom'
    else:
        try:
            steel_column_mm = get_profile_width(profile_family, profile_size)
        except ValueError:
            steel_column_mm = 300

    options = {
        'expansion_pct':        expansion_pct,
        'profile_family':       profile_family,
        'profile_size':         profile_size,
        'steel_column_mm':      steel_column_mm,
        'spare_space_location': spare_space_location,
    }

    pipes = []
    for dn, rating, ins in zip(dns, ratings, insulations):
        try:
            pipes.append({'dn': int(dn), 'rating': _normalize_rating(rating), 'insulation': int(ins)})
        except (ValueError, TypeError):
            return render_template(
                'rack_calculator.html',
                active_page="rack-calculator",
                tool_title="Pipe Rack Width Calculator",
                tool_subtitle="Arrangement & DXF Export",
                footer_title="Rack Calculator — Engineering Tool",
                footer_dept="Piping Department · JESA",
                dn_sizes=DN_SIZES, flange_ratings=FLANGE_RATINGS,
                rating_labels=RATING_LABELS,
                pipes=None, result=None, diagram=None,
                options=options,
                profiles_for_js=_PROFILES_JS,
                error="Invalid input — please check all fields are filled with numbers.",
            )
    try:
        result = calculate_rack(pipes, expansion_pct=expansion_pct, steel_column_mm=steel_column_mm)
    except (ValueError, KeyError) as e:
        return render_template(
            'rack_calculator.html',
            active_page="rack-calculator",
            tool_title="Pipe Rack Width Calculator",
            tool_subtitle="Arrangement & DXF Export",
            footer_title="Rack Calculator — Engineering Tool",
            footer_dept="Piping Department · JESA",
            dn_sizes=DN_SIZES, flange_ratings=FLANGE_RATINGS,
            rating_labels=RATING_LABELS,
            pipes=pipes, result=None, diagram=None,
            options=options,
            profiles_for_js=_PROFILES_JS,
            error=str(e),
        )
    diagram = generate_diagram(pipes, result, spare_space_location=spare_space_location)
    return render_template(
        'rack_calculator.html',
        active_page="rack-calculator",
        tool_title="Pipe Rack Width Calculator",
        tool_subtitle="Arrangement & DXF Export",
        footer_title="Rack Calculator — Engineering Tool",
        footer_dept="Piping Department · JESA",
        dn_sizes=DN_SIZES, flange_ratings=FLANGE_RATINGS,
        rating_labels=RATING_LABELS,
        pipes=pipes, result=result, diagram=diagram,
        options=options,
        profiles_for_js=_PROFILES_JS,
        error=None,
    )


@app.route('/rack-calculator/dxf', methods=['POST'])
def rack_calculate_dxf():
    dns = request.form.getlist('dn')
    ratings = request.form.getlist('rating')
    insulations = request.form.getlist('insulation')

    try:
        expansion_pct = int(request.form.get('expansion_pct', 20))
    except ValueError:
        expansion_pct = 20

    profile_family = request.form.get('profile_family', 'HEA').strip()
    profile_size = request.form.get('profile_size', '300').strip()

    spare_space_location = request.form.get('spare_space_location', 'right').strip()
    if spare_space_location not in ('right', 'center'):
        spare_space_location = 'right'

    if profile_family.lower() == 'custom':
        try:
            steel_column_mm = int(request.form.get('steel_column_mm', 330))
        except (ValueError, TypeError):
            steel_column_mm = 330
        dxf_profile_label = f"CUSTOM {steel_column_mm} mm"
    else:
        try:
            steel_column_mm = get_profile_width(profile_family, profile_size)
            dxf_profile_label = f"{profile_family} {profile_size}"
        except ValueError:
            steel_column_mm = 300
            dxf_profile_label = "HEA 300"

    pipes = []
    for dn, rating, ins in zip(dns, ratings, insulations):
        try:
            pipes.append({'dn': int(dn), 'rating': _normalize_rating(rating), 'insulation': int(ins)})
        except (ValueError, TypeError):
            abort(400, description="Invalid rack input.")

    try:
        result = calculate_rack(pipes, expansion_pct=expansion_pct, steel_column_mm=steel_column_mm)
        dxf_bytes = generate_dxf(
            pipes,
            result,
            spare_space_location=spare_space_location,
            metadata={
                "profile_label": dxf_profile_label,
                "column_label": dxf_profile_label,
            },
        )
    except (ValueError, KeyError) as e:
        abort(400, description=str(e))

    filename = f"rack-section-{result['rack_width']}mm.dxf"
    return Response(
        dxf_bytes,
        mimetype="application/dxf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    app.run(debug=debug, port=port, host="0.0.0.0")
