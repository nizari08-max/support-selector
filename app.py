"""
app.py  —  JESA Piping Support Selector  (Web Application)
Run:  python app.py   then open  http://localhost:5000
"""
import os
import sys
import re

from flask import Flask, render_template, request, jsonify

# Allow imports from the same directory as app.py
sys.path.insert(0, os.path.dirname(__file__))

from selector import select_support  # noqa: E402

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
            "success":       True,
            "support_code":  result.support_code,
            "drawings":      result.drawings,
            "notes":         result.note_texts,
            "is_applicable": result.is_applicable(),
            "image_key":     get_image_key(result.support_code),
            "size_range":    result.size_range,
        })
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Unexpected error: {e}"}), 500


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    app.run(debug=debug, port=port, host="0.0.0.0")
