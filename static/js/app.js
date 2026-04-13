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
];

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
  frp_clamp:     "FRP Clamp Shoe (CF) — End Elevation",
  not_applicable:"Not Applicable",
};

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
  nps:        null,
  material:   "",
  pwht:       false,
  insulation: "uninsulated",
  fn:         null,
};

// ── Initialise ────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  buildNPSGrid();
  bindToggleGroup("pwhtGroup",      v => { state.pwht = (v === "true"); });
  bindToggleGroup("insulationGroup",v => { state.insulation = v; });
  bindFunctionButtons();
  document.getElementById("materialSelect").addEventListener("change", e => {
    state.material = e.target.value;
  });
});

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
    });
  });
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
        nps:       state.nps,
        material:  state.material,
        pwht:      state.pwht,
        insulation: state.insulation,
        function:  state.fn,
      }),
    });
    const data = await res.json();

    if (!data.success)      { showError(data.error); return; }
    if (!data.is_applicable){ showNA(); return; }
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
  if (!state.fn) {
    shake("functionGrid" in document ? "functionGrid" : "submitBtn");
    document.querySelectorAll(".fn-btn").forEach(b => b.classList.add("shake"));
    setTimeout(() => document.querySelectorAll(".fn-btn").forEach(b => b.classList.remove("shake")), 500);
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

const PANELS = ["emptyState","resultContent","naState","errorState"];

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
  const summaryEl = document.getElementById("inputSummary");
  summaryEl.innerHTML = "";
  const npsLabel = NPS_SIZES.find(n => n.value === state.nps)?.label || state.nps;
  const pills = [
    { key: "NPS",        val: `${npsLabel}"` },
    { key: "Material",   val: MATERIAL_NAMES[state.material] || state.material },
    { key: "PWHT",       val: state.pwht ? "Required" : "Not Required" },
    { key: "Insulation", val: state.insulation === "hot_insulated" ? "Hot Insulated" : "Uninsulated" },
    { key: "Function",   val: state.fn.replace("_"," ").replace(/\b\w/g,c=>c.toUpperCase()) },
  ];
  pills.forEach(({ key, val }) => {
    const pill = document.createElement("span");
    pill.className = "summary-pill";
    pill.innerHTML = `<strong>${key}:</strong> ${val}`;
    summaryEl.appendChild(pill);
  });

  // -- Drawing references --
  const chipsEl = document.getElementById("drawingChips");
  chipsEl.innerHTML = "";
  if (data.drawings && data.drawings.length > 0) {
    data.drawings.forEach(dwg => {
      const chip = document.createElement("span");
      chip.className = "dwg-chip";
      chip.textContent = dwg;
      chipsEl.appendChild(chip);
    });
  } else {
    const chip = document.createElement("span");
    chip.className = "dwg-chip-none";
    chip.textContent = "No dedicated drawing — direct structural contact";
    chipsEl.appendChild(chip);
  }
  document.getElementById("drawingsCard").style.display = "";

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
}

function showNA() {
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
    state.fn.replace("_"," ").replace(/\b\w/g, c => c.toUpperCase()),
  ];
  pills.forEach(text => {
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
  hideAll(PANELS);
  showAll(["emptyState"]);
}
