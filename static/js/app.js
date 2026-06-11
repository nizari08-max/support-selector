/* ==========================================================================
   JESA Piping Support Selector — Frontend Logic
   ========================================================================== */

"use strict";

// ── NPS configuration ────────────────────────────────────────────────────────
const NPS_SIZES = [
  { label: "½",    value: 0.5  },
  { label: "¾",    value: 0.75 },
  { label: "1",    value: 1.0  },
  { label: "1½",   value: 1.5  },
  { label: "2",    value: 2.0  },
  { label: "3",    value: 3.0  },
  { label: "4",    value: 4.0  },
  { label: "6",    value: 6.0  },
  { label: "8",    value: 8.0  },
  { label: "10",   value: 10.0 },
  { label: "12",   value: 12.0 },
  { label: "14",   value: 14.0 },
  { label: "16",   value: 16.0 },
  { label: "18",   value: 18.0 },
  { label: "20",   value: 20.0 },
  { label: "22",   value: 22.0 },
  { label: "24",   value: 24.0 },
  { label: "26",   value: 26.0 },
  { label: "28",   value: 28.0 },
  { label: "30",   value: 30.0 },
  { label: "32",   value: 32.0 },
  { label: "36",   value: 36.0 },
  { label: "40",   value: 40.0 },
  { label: "42",   value: 42.0 },
  { label: "48",   value: 48.0 },
  { label: "80",   value: 80.0 },
];

// ── DN → NPS mapping (ISO 6708 / ASME B36.10M) ───────────────────────────────
const DN_TO_NPS = {
   15: 0.5,   20: 0.75,   25: 1.0,   32: 1.25,   40: 1.5,
   50: 2.0,   65: 2.5,    80: 3.0,  100: 4.0,   125: 5.0,
  150: 6.0,  200: 8.0,   250: 10.0, 300: 12.0,  350: 14.0,
  400: 16.0, 450: 18.0,  500: 20.0, 550: 22.0,  600: 24.0,
  650: 26.0, 700: 28.0,  750: 30.0, 800: 32.0,  900: 36.0,
 1000: 40.0, 1050: 42.0, 1200: 48.0,
};

// NPS fraction labels for sizes not in the grid (1¼", 2½", 5")
const NPS_EXTRA_LABELS = { 1.25: "1¼", 2.5: "2½", 5.0: "5" };

// ── Illustration labels ───────────────────────────────────────────────────────
const ILLUS_LABELS = {
  direct_rest:   "Direct Rest — End Elevation",
  bearing_plate: "Bearing Plate (BP) — End Elevation",
  wear_pad:      "Wear Pad Assembly (WA) — End Elevation",
  pipe_shoe:     "Pipe Shoe (SH) — End Elevation",
  shoe_clamp:    "Shoe Clamp / Saddle (SC) — End Elevation",
  guide:         "Guide Support (GL) — End Elevation",
  line_stop:     "Line Stop Support (LS) — End Elevation",
  hold_down:     "Hold Down Support (GH) — End Elevation",
  frp_clamp:          "FRP Clamp Shoe (CF) — End Elevation",
  flange_frame:       "Flange Frame Support (FF) — End Elevation",
  frp_flange_holder:  "FRP Flanged Valve Holder (FF71) — End Elevation",
  vertical_lug:       "Vertical Pipe Lug Support (WL) - Side Elevation",
  rc71:               "FRP Riser Clamp Rest (RC71) - Elevation",
  rc72:               "FRP Riser Clamp Rest + Guide + Hold Down (RC72) - Elevation",
  rc73:               "FRP Riser Clamp All Around Guide (RC73) - Elevation",
  not_applicable:     "Not Applicable",
};

// ── MPMS material → selector dropdown mapping ─────────────────────────────────
// The span calculator backend uses "AS" for Alloy Steel; the selector dropdown
// option value is "SA". All other material codes are identical between the two.
const SPAN_MATERIAL_TO_SELECTOR = { AS: "SA" };

// ── Material class readable names ─────────────────────────────────────────────
const MATERIAL_NAMES = {
  CS:  "Carbon Steel (CS)",
  LT:  "Low Temp CS (LT)",
  SS:  "Stainless Steel (SS)",
  DS:  "Duplex SS (DS)",
  SD:  "Super Duplex SS (SD)",
  SA:  "Alloy Steel (SA)",
  AL:  "Aluminum (AL)",
  AY:  "Aluminum Alloy (AY)",
  CN:  "Copper-Nickel (CN)",
  FRP: "Fiberglass (FRP)",
};

// ── State ─────────────────────────────────────────────────────────────────────
let state = {
  nps:              null,
  material:         "",
  pwht:             false,
  insulation:       "uninsulated",
  fn:               null,
  pipingClass:      "",
  pipingClassEntry: null,   // resolved entry from /api/resolve-class
  refinements:      {},
  pendingQuestions: [],
  pipeOrientation: "horizontal",
  verticalRestraint: null,
  frpVerticalSupport: null,
  // Flange support state (REST only)
  isFlange:    false,
  flangeClass: null,  // int: 150 | 300 | 600 | 900 | 1500 | 2500 (ignored for FRP)
};

// ── Initialise ────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  buildNPSGrid();
  bindToggleGroup("pwhtGroup",      v => { state.pwht = (v === "true"); clearRefinements(); });
  bindToggleGroup("insulationGroup",v => { state.insulation = v; clearRefinements(); });
  bindToggleGroup("orientationGroup", v => {
    state.pipeOrientation = v;
    clearRefinements();
    updateOrientationUI();
  });
  bindToggleGroup("verticalRestraintGroup", v => {
    state.verticalRestraint = v;
    clearRefinements();
  });
  bindToggleGroup("frpVerticalSupportGroup", v => {
    state.frpVerticalSupport = v;
    clearRefinements();
  });
  bindFunctionButtons();
  document.getElementById("materialSelect").addEventListener("change", e => {
    state.material = e.target.value;
    clearRefinements();
    _updateFlangeClassVisibility();
    updateOrientationUI();
  });
  document.getElementById("dnInput").addEventListener("input", handleDNInput);
  document.getElementById("pipingClassInput").addEventListener("input", handlePipingClassInput);
  bindFlangeControls();
  updateOrientationUI();
});

// ── DN converter ─────────────────────────────────────────────────────────────
function handleDNInput(e) {
  const raw = e.target.value.trim();
  const resultEl = document.getElementById("dnResult");
  if (!raw) {
    resultEl.textContent = "";
    resultEl.className = "dn-result";
    return;
  }
  const dn = parseInt(raw, 10);
  if (isNaN(dn) || dn <= 0) {
    resultEl.textContent = "Enter a positive integer.";
    resultEl.className = "dn-result dn-error";
    return;
  }
  const npsValue = DN_TO_NPS[dn];
  if (npsValue === undefined) {
    resultEl.textContent = `DN ${dn} not found. Please select NPS manually.`;
    resultEl.className = "dn-result dn-error";
    return;
  }
  const npsEntry = NPS_SIZES.find(s => s.value === npsValue);
  if (!npsEntry) {
    const lbl = NPS_EXTRA_LABELS[npsValue] || npsValue;
    resultEl.textContent = `DN ${dn} = NPS ${lbl}" — not available in this grid`;
    resultEl.className = "dn-result dn-warn";
    return;
  }
  const buttons = document.querySelectorAll(".nps-btn");
  buttons.forEach(btn => {
    if (btn.textContent.trim() === npsEntry.label) {
      selectNPS(npsValue, btn, npsEntry.label);
    }
  });
  resultEl.textContent = `DN ${dn} = NPS ${npsEntry.label}"`;
  resultEl.className = "dn-result dn-ok";
}

// ── Piping class lookup ───────────────────────────────────────────────────────
async function handlePipingClassInput(e) {
  const raw       = e.target.value.trim().toUpperCase();
  const feedback  = document.getElementById("pcFeedback");
  state.pipingClass      = raw;
  state.pipingClassEntry = null;

  if (!raw) {
    feedback.textContent = "";
    feedback.className   = "pc-feedback";
    return;
  }

  feedback.textContent = "…";
  feedback.className   = "pc-feedback";

  let data;
  try {
    const res = await fetch(`/api/resolve-class/${encodeURIComponent(raw)}`);
    data = await res.json();
  } catch (_) {
    feedback.textContent = "Lookup unavailable. Please select material manually.";
    feedback.className   = "pc-feedback pc-unknown";
    return;
  }

  // Guard: user may have typed something new while the request was in flight
  if (state.pipingClass !== raw) return;

  if (!data.found) {
    feedback.textContent = "Class code not found. Please select material manually.";
    feedback.className   = "pc-feedback pc-unknown";
    return;
  }

  if (data.excluded) {
    feedback.textContent =
      `Class ${raw} is not covered by this standard. ${data.reason}`;
    feedback.className = "pc-feedback pc-excluded";
    return;
  }

  // Map span-material code to selector dropdown value (AS → SA for Alloy Steel)
  const selectorMaterial = SPAN_MATERIAL_TO_SELECTOR[data.material] || data.material;

  // Auto-fill material dropdown
  const sel  = document.getElementById("materialSelect");
  sel.value  = selectorMaterial;
  state.material         = selectorMaterial;
  state.pipingClassEntry = data;
  clearRefinements();
  _updateFlangeClassVisibility();

  // Trigger the AUTO badge on the material field wrapper
  const wrapper = document.getElementById("materialSelectWrapper");
  if (wrapper) wrapper.dataset.auto = "true";

  feedback.textContent = `${raw} → ${data.desc} | ${data.rating} ✓`;
  feedback.className   = "pc-feedback pc-ok";
}

// ── NPS grid ──────────────────────────────────────────────────────────────────
function buildNPSGrid() {
  const grid = document.getElementById("npsGrid");
  NPS_SIZES.forEach(({ label, value }) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "nps-btn";
    btn.textContent = label;
    btn.title = `NPS ${label}"`;
    btn.addEventListener("click", () => selectNPS(value, btn, label));
    grid.appendChild(btn);
  });
}

function selectNPS(value, btn, label) {
  document.querySelectorAll(".nps-btn").forEach(b => b.classList.remove("selected"));
  btn.classList.add("selected");
  state.nps = value;
  clearRefinements();
  const badge = document.getElementById("npsDisplay");
  badge.textContent = `NPS ${label}"`;
  badge.style.display = "inline-flex";
}

// ── Generic toggle group binder ───────────────────────────────────────────────
function bindToggleGroup(groupId, onChange) {
  document.querySelectorAll(`#${groupId} .toggle-btn`).forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(`#${groupId} .toggle-btn`).forEach(b =>
        b.classList.remove("active")
      );
      btn.classList.add("active");
      onChange(btn.dataset.value);
    });
  });
}

// ── Function buttons ──────────────────────────────────────────────────────────
function bindFunctionButtons() {
  document.querySelectorAll(".fn-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".fn-btn").forEach(b => b.classList.remove("selected"));
      btn.classList.add("selected");
      state.fn = btn.dataset.value;
      clearRefinements();
      // Show flange section only when REST is selected
      const flangeSection = document.getElementById("flangeSection");
      if (flangeSection) {
        flangeSection.style.display = (state.fn === "rest") ? "" : "none";
        if (state.fn !== "rest") {
          _resetFlangeState();
        }
      }
    });
  });
}

// ── Flange section controls ───────────────────────────────────────────────────
function updateOrientationUI() {
  const isVertical = state.pipeOrientation === "vertical";
  const isFrpVertical = isVertical && _isFrpSelected();
  const verticalDetails = document.getElementById("verticalDetails");
  const frpVerticalDetails = document.getElementById("frpVerticalDetails");
  const functionSection = document.getElementById("functionSection");
  const flangeSection = document.getElementById("flangeSection");

  if (verticalDetails) verticalDetails.style.display = (isVertical && !isFrpVertical) ? "" : "none";
  if (frpVerticalDetails) frpVerticalDetails.style.display = isFrpVertical ? "" : "none";
  if (functionSection) functionSection.style.display = isVertical ? "none" : "";

  if (isVertical) {
    _resetFlangeState();
    if (flangeSection) flangeSection.style.display = "none";
    if (isFrpVertical) {
      state.verticalRestraint = null;
      document.querySelectorAll("#verticalRestraintGroup .toggle-btn").forEach(b => b.classList.remove("active"));
    } else {
      state.frpVerticalSupport = null;
      document.querySelectorAll("#frpVerticalSupportGroup .toggle-btn").forEach(b => b.classList.remove("active"));
    }
  } else if (flangeSection) {
    state.frpVerticalSupport = null;
    document.querySelectorAll("#frpVerticalSupportGroup .toggle-btn").forEach(b => b.classList.remove("active"));
    flangeSection.style.display = (state.fn === "rest") ? "" : "none";
  }
}

function _isFrpSelected() {
  return (state.material || "").toUpperCase() === "FRP";
}

function _updateFlangeClassVisibility() {
  const fcs = document.getElementById("flangeClassSection");
  const fri = document.getElementById("frpFlangeInfo");
  const isFrp = _isFrpSelected();
  if (fcs) fcs.style.display = isFrp ? "none" : "";
  if (fri) fri.style.display = isFrp ? "" : "none";
  if (isFrp) {
    state.flangeClass = null;
    document.querySelectorAll("#flangeClassGroup .toggle-btn").forEach(b => b.classList.remove("active"));
  }
}

function _resetFlangeState() {
  state.isFlange    = false;
  state.flangeClass = null;
  document.querySelectorAll("#flangeToggleGroup .toggle-btn").forEach((b, i) => {
    b.classList.toggle("active", i === 0);
  });
  const fd = document.getElementById("flangeDetails");
  if (fd) fd.style.display = "none";
}

function bindFlangeControls() {
  // "Support at a flange?" toggle
  document.querySelectorAll("#flangeToggleGroup .toggle-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#flangeToggleGroup .toggle-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      state.isFlange = (btn.dataset.value === "true");
      clearRefinements();
      const fd = document.getElementById("flangeDetails");
      if (fd) fd.style.display = state.isFlange ? "" : "none";
      if (!state.isFlange) {
        state.flangeClass = null;
        document.querySelectorAll("#flangeClassGroup .toggle-btn").forEach(b => b.classList.remove("active"));
      }
      _updateFlangeClassVisibility();
    });
  });

  // Pressure class buttons (CL 150 / 300 / 600 / 900 / 1500 / 2500)
  document.querySelectorAll("#flangeClassGroup .toggle-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#flangeClassGroup .toggle-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      state.flangeClass = parseInt(btn.dataset.value, 10);
      clearRefinements();
    });
  });
}

function clearRefinements() {
  state.refinements = {};
  state.pendingQuestions = [];
}

// ── Main selection ────────────────────────────────────────────────────────────
async function runSelection() {
  // Validate
  if (!validateInputs()) return;

  const btn   = document.getElementById("submitBtn");
  const label = document.getElementById("submitLabel");
  const arrow = document.querySelector(".submit-arrow");
  const spin  = document.getElementById("spinner");

  btn.disabled = true;
  label.textContent = "Selecting…";
  arrow.style.display = "none";
  spin.style.display  = "block";

  try {
    const res  = await fetch("/api/select", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({
        nps:              state.nps,
        material:         state.material,
        pwht:             state.pwht,
        insulation:       state.insulation,
        function:         state.pipeOrientation === "vertical" ? "rest" : state.fn,
        pipe_orientation: state.pipeOrientation,
        vertical_restraint: state.pipeOrientation === "vertical" ? state.verticalRestraint : null,
        frp_vertical_support: state.pipeOrientation === "vertical" ? state.frpVerticalSupport : null,
        piping_class:     state.pipingClass || null,
        refinements:      state.refinements || {},
        is_flange:    state.pipeOrientation === "vertical" ? false : state.isFlange,
        flange_class: state.flangeClass,
      }),
    });
    const data = await res.json();

    if (!data.success)      { showError(data.error); return; }
    if (!data.is_applicable){ showNA(data); return; }
    if (data.status === "needs_refinement") { showRefinement(data); return; }
    showResult(data);

  } catch (err) {
    showError("Connection error. Make sure the server is running on localhost:5000.");
  } finally {
    btn.disabled = false;
    label.textContent = "SELECT SUPPORT";
    arrow.style.display = "block";
    spin.style.display  = "none";
  }
}

// ── Validation ────────────────────────────────────────────────────────────────
function validateInputs() {
  let ok = true;

  if (state.nps === null) {
    shake("npsGrid");
    ok = false;
  }
  const sel = document.getElementById("materialSelect");
  if (!state.material) {
    sel.classList.add("error");
    setTimeout(() => sel.classList.remove("error"), 2000);
    shake("materialSelect");
    ok = false;
  }
  if (state.pipeOrientation !== "vertical" && !state.fn) {
    shake("functionGrid");
    document.querySelectorAll(".fn-btn").forEach(b => b.classList.add("shake"));
    setTimeout(() => document.querySelectorAll(".fn-btn").forEach(b => b.classList.remove("shake")), 500);
    ok = false;
  }
  if (state.pipeOrientation === "vertical" && _isFrpSelected() && !state.frpVerticalSupport) {
    shake("frpVerticalDetails");
    document.querySelectorAll("#frpVerticalSupportGroup .toggle-btn").forEach(b => b.classList.add("shake"));
    setTimeout(() => document.querySelectorAll("#frpVerticalSupportGroup .toggle-btn").forEach(b => b.classList.remove("shake")), 500);
    ok = false;
  }
  if (state.pipeOrientation === "vertical" && !_isFrpSelected() && !state.verticalRestraint) {
    shake("verticalDetails");
    document.querySelectorAll("#verticalRestraintGroup .toggle-btn").forEach(b => b.classList.add("shake"));
    setTimeout(() => document.querySelectorAll("#verticalRestraintGroup .toggle-btn").forEach(b => b.classList.remove("shake")), 500);
    ok = false;
  }
  // Flange: require pressure class for metallic materials (FRP uses FF71, no class needed)
  if (state.pipeOrientation !== "vertical" && state.isFlange && !_isFrpSelected() && !state.flangeClass) {
    document.querySelectorAll("#flangeClassGroup .toggle-btn").forEach(b => {
      b.classList.add("shake");
      setTimeout(() => b.classList.remove("shake"), 500);
    });
    const fcs = document.getElementById("flangeClassSection");
    if (fcs) { fcs.classList.add("shake"); setTimeout(() => fcs.classList.remove("shake"), 500); }
    ok = false;
  }
  return ok;
}

function shake(id) {
  const el = document.getElementById(id);
  if (!el) return;
  el.classList.add("shake");
  setTimeout(() => el.classList.remove("shake"), 500);
}

// ── Display helpers ────────────────────────────────────────────────────────────
function showAll(ids)  { ids.forEach(id => { const e = document.getElementById(id); if(e) e.style.display = ""; }); }
function hideAll(ids)  { ids.forEach(id => { const e = document.getElementById(id); if(e) e.style.display = "none"; }); }

const PANELS = ["emptyState","refinementState","resultContent","naState","errorState"];

function buildSummaryPills(targetId) {
  const summaryEl = document.getElementById(targetId);
  summaryEl.innerHTML = "";
  const npsLabel = NPS_SIZES.find(n => n.value === state.nps)?.label || state.nps;
  const pills = [
    { key: "NPS",        val: `${npsLabel}"` },
    { key: "Material",   val: MATERIAL_NAMES[state.material] || state.material },
    { key: "PWHT",       val: state.pwht ? "Required" : "Not Required" },
    { key: "Insulation", val: state.insulation === "hot_insulated" ? "Hot Insulated" : "Uninsulated" },
    { key: "Orientation", val: state.pipeOrientation === "vertical" ? "Vertical" : "Horizontal" },
  ];
  if (state.pipeOrientation === "vertical") {
    pills.push({
      key: _isFrpSelected() ? "Riser Clamp" : "Restraint",
      val: _verticalSelectionLabel(),
    });
  } else {
    pills.push({
      key: "Function",
      val: state.fn.replace("_"," ").replace(/\b\w/g,c=>c.toUpperCase()),
    });
  }
  if (state.pipingClass && state.pipingClassEntry) {
    const pc = state.pipingClassEntry;
    pills.push({ key: "Piping Class", val: `${state.pipingClass} — ${pc.desc}` });
  }
  pills.forEach(({ key, val }) => {
    const pill = document.createElement("span");
    pill.className = "summary-pill";
    pill.innerHTML = `<strong>${key}:</strong> ${val}`;
    summaryEl.appendChild(pill);
  });
}

function _verticalSelectionLabel() {
  if (_isFrpSelected()) {
    if (state.frpVerticalSupport === "rest_guide_hold_down") return "Rest + Guide + Hold Down";
    if (state.frpVerticalSupport === "all_around_guide") return "All Around Guide";
    return "Rest";
  }
  return state.verticalRestraint === "fixed" ? "Fixed" : "Sliding / Shear";
}

function showRefinement(data) {
  hideAll(PANELS);
  showAll(["refinementState"]);

  state.pendingQuestions = data.refinement_questions || [];
  buildSummaryPills("refinementSummary");

  const box = document.getElementById("refinementQuestions");
  box.innerHTML = "";

  state.pendingQuestions.forEach(question => {
    const field = document.createElement("div");
    field.className = "refinement-field";

    const label = document.createElement("label");
    label.className = "section-label refinement-label";
    label.textContent = question.label;
    field.appendChild(label);

    if (question.reason) {
      const reason = document.createElement("p");
      reason.className = "field-hint refinement-reason";
      reason.textContent = question.reason;
      field.appendChild(reason);
    }

    if (question.type === "choice") {
      const row = document.createElement("div");
      row.className = "toggle-row refinement-choice";
      (question.options || []).forEach(option => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "toggle-btn refinement-option";
        btn.dataset.questionId = question.id;
        btn.dataset.value = option.value;
        btn.textContent = option.label;
        if (String(state.refinements[question.id]) === String(option.value)) {
          btn.classList.add("active");
        }
        btn.addEventListener("click", () => {
          row.querySelectorAll(".toggle-btn").forEach(b => b.classList.remove("active"));
          btn.classList.add("active");
          state.refinements[question.id] = option.value;
        });
        row.appendChild(btn);
      });
      field.appendChild(row);
    } else if (question.type === "number") {
      const wrap = document.createElement("div");
      wrap.className = "refinement-number-wrap";
      const input = document.createElement("input");
      input.type = "number";
      input.className = "pc-input refinement-number";
      input.dataset.questionId = question.id;
      input.placeholder = question.unit || "";
      if (question.min !== undefined) input.min = question.min;
      if (question.step !== undefined) input.step = question.step;
      if (state.refinements[question.id] !== undefined) {
        input.value = state.refinements[question.id];
      }
      input.addEventListener("input", () => {
        state.refinements[question.id] = input.value;
      });
      wrap.appendChild(input);
      if (question.unit) {
        const unit = document.createElement("span");
        unit.className = "pc-prefix refinement-unit";
        unit.textContent = question.unit;
        wrap.appendChild(unit);
      }
      field.appendChild(wrap);
    }

    box.appendChild(field);
  });
}

function submitRefinements() {
  let ok = true;
  state.pendingQuestions.forEach(question => {
    const value = state.refinements[question.id];
    if (question.required && (value === undefined || value === null || value === "")) {
      ok = false;
      document.querySelectorAll(`[data-question-id="${question.id}"]`).forEach(el => {
        el.classList.add("shake");
        setTimeout(() => el.classList.remove("shake"), 500);
      });
    }
  });
  if (!ok) return;
  runSelection();
}

function showResult(data) {
  hideAll(PANELS);
  showAll(["resultContent"]);

  // -- Illustration --
  const img = document.getElementById("supportImg");
  img.style.opacity = "0";
  img.style.transform = "scale(0.96)";
  img.src = `/static/images/supports/${data.image_key || "not_applicable"}.svg`;
  img.alt = ILLUS_LABELS[data.image_key] || data.image_key;
  img.onload = () => {
    requestAnimationFrame(() => {
      img.style.transition = "opacity 0.4s ease, transform 0.4s ease";
      img.style.opacity    = "1";
      img.style.transform  = "scale(1)";
    });
  };
  document.getElementById("illusMeta").textContent =
    ILLUS_LABELS[data.image_key] || "";

  // -- Badge --
  document.getElementById("resultBadge").textContent = "APPLICABLE";

  // -- Support code title --
  document.getElementById("resultCode").textContent = data.support_code;

  // -- Input summary pills --
  buildSummaryPills("inputSummary");

  // -- Drawing references --
  const chipsEl = document.getElementById("drawingChips");
  chipsEl.innerHTML = "";
  const labeled = data.drawings_labeled || (data.drawings || []).map(r => ({ code: "", ref: r }));
  if (labeled.length > 0) {
    labeled.forEach(({ code, ref }) => {
      const chip = document.createElement("a");
      chip.className = "dwg-chip dwg-chip-link";
      if (code) {
        chip.innerHTML =
          `<span class="chip-code-label">${code}</span>` +
          `<span class="chip-ref-text">${ref}</span>`;
      } else {
        chip.innerHTML = `<span class="chip-ref-text">${ref}</span>`;
      }
      const npsParam = state.nps !== null ? `?nps=${state.nps}` : "";
      chip.href = `/api/drawing/${encodeURIComponent(ref)}${npsParam}`;
      chip.target = "_blank";
      chip.rel = "noopener noreferrer";
      chip.title = `${code ? code + " — " : ""}${ref}  (NPS ${state.nps || "?"}") — click to open drawing`;
      chipsEl.appendChild(chip);
    });
  } else {
    const chip = document.createElement("span");
    chip.className = "dwg-chip-none";
    chip.textContent = "No dedicated drawing — direct structural contact";
    chipsEl.appendChild(chip);
  }
  document.getElementById("drawingsCard").style.display = "";

  const relatedCard = document.getElementById("relatedDrawingsCard");
  const relatedChips = document.getElementById("relatedDrawingChips");
  const related = data.related_drawings_labeled ||
    (data.related_drawings || []).map(r => ({ code: "", ref: r }));
  if (relatedCard && relatedChips) {
    relatedChips.innerHTML = "";
    if (related.length > 0) {
      related.forEach(({ code, ref }) => {
        const chip = document.createElement("a");
        chip.className = "dwg-chip dwg-chip-link";
        if (code) {
          chip.innerHTML =
            `<span class="chip-code-label">${code}</span>` +
            `<span class="chip-ref-text">${ref}</span>`;
        } else {
          chip.innerHTML = `<span class="chip-ref-text">${ref}</span>`;
        }
        const npsParam = state.nps !== null ? `?nps=${state.nps}` : "";
        chip.href = `/api/drawing/${encodeURIComponent(ref)}${npsParam}`;
        chip.target = "_blank";
        chip.rel = "noopener noreferrer";
        chip.title = `${code ? code + " - " : ""}${ref}  (NPS ${state.nps || "?"}") - click to open drawing`;
        relatedChips.appendChild(chip);
      });
      relatedCard.style.display = "";
    } else {
      relatedCard.style.display = "none";
    }
  }

  // -- Engineering notes --
  const notesEl = document.getElementById("notesList");
  notesEl.innerHTML = "";
  if (data.notes && data.notes.length > 0) {
    data.notes.forEach(note => {
      const div = document.createElement("div");
      div.className = "note-item";
      div.textContent = note;
      notesEl.appendChild(div);
    });
    document.getElementById("notesCard").style.display = "";
  } else {
    document.getElementById("notesCard").style.display = "none";
  }

  if (data.applied_refinements && data.applied_refinements.length > 0) {
    data.applied_refinements.forEach(item => {
      const div = document.createElement("div");
      div.className = "note-item refinement-applied";
      div.textContent = `${item.label}: ${item.result}`;
      notesEl.appendChild(div);
    });
    document.getElementById("notesCard").style.display = "";
  }

  if (data.refinement_warnings && data.refinement_warnings.length > 0) {
    data.refinement_warnings.forEach(warning => {
      const div = document.createElement("div");
      div.className = "note-item refinement-warning";
      div.textContent = warning;
      notesEl.appendChild(div);
    });
    document.getElementById("notesCard").style.display = "";
  }
}

function showNA(data) {
  hideAll(PANELS);
  showAll(["naState"]);

  // Show the input combo that led to N/A
  const paramsEl = document.getElementById("naParams");
  paramsEl.innerHTML = "";
  const npsLabel = NPS_SIZES.find(n => n.value === state.nps)?.label || state.nps;
  const pills = [
    `NPS ${npsLabel}"`,
    MATERIAL_NAMES[state.material] || state.material,
    state.insulation === "hot_insulated" ? "Hot Insulated" : "Uninsulated",
    state.pipeOrientation === "vertical" ? "Vertical" : state.fn.replace("_"," ").replace(/\b\w/g, c => c.toUpperCase()),
  ];
  if (state.pipeOrientation === "vertical" && (state.verticalRestraint || state.frpVerticalSupport)) {
    pills.push(_verticalSelectionLabel());
  }
  pills.forEach(text => {
    const p = document.createElement("span");
    p.className = "summary-pill";
    p.textContent = text;
    paramsEl.appendChild(p);
  });

  (data?.refinement_warnings || []).forEach(text => {
    const p = document.createElement("span");
    p.className = "summary-pill";
    p.textContent = text;
    paramsEl.appendChild(p);
  });
}

function showError(msg) {
  hideAll(PANELS);
  showAll(["errorState"]);
  document.getElementById("errorMsg").textContent = msg;
}

function resetToEmpty() {
  clearRefinements();
  hideAll(PANELS);
  showAll(["emptyState"]);
}
