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
  frp_clamp:     "FRP Clamp Shoe (CF) — End Elevation",
  not_applicable:"Not Applicable",
};

// ── MPMS Piping Class mapping ─────────────────────────────────────────────────
// Metallic + FRP classes only. Source: Master Piping Material Specification.
const MPMS_CLASSES = {
  BA1:  { material: "CS",  rating: "150 Lb.", desc: "Carbon Steel Galvanized" },
  BA2:  { material: "CS",  rating: "150 Lb.", desc: "Carbon Steel Galvanized" },
  BB1:  { material: "CS",  rating: "150 Lb.", desc: "Carbon Steel" },
  BB1U: { material: "CS",  rating: "150 Lb.", desc: "Carbon Steel + PE Coating" },
  BB2:  { material: "CS",  rating: "150 Lb.", desc: "Carbon Steel + PE Coating" },
  BB3:  { material: "CS",  rating: "150 Lb.", desc: "Carbon Steel" },
  BB4:  { material: "CS",  rating: "150 Lb.", desc: "Carbon Steel" },
  BB5:  { material: "CS",  rating: "150 Lb.", desc: "Impact Tested Carbon Steel" },
  BB6:  { material: "CS",  rating: "150 Lb.", desc: "Carbon Steel" },
  BD1:  { material: "SS",  rating: "150 Lb.", desc: "316/316L Stainless Steel" },
  BD2:  { material: "SS",  rating: "150 Lb.", desc: "316/316L Stainless Steel" },
  BD2U: { material: "SS",  rating: "150 Lb.", desc: "316/316L SS + PE Coated" },
  BG1:  { material: "SS",  rating: "150 Lb.", desc: "904L Stainless Steel" },
  BG2:  { material: "SS",  rating: "150 Lb.", desc: "904L Stainless Steel" },
  BK1:  { material: "FRP", rating: "150 Lb.", desc: "Fiberglass Reinforced Pipe" },
  BK2:  { material: "FRP", rating: "150 Lb.", desc: "Fiberglass Reinforced Pipe" },
  BK3:  { material: "FRP", rating: "150 Lb.", desc: "Fiberglass Reinforced Pipe" },
  BK4:  { material: "FRP", rating: "150 Lb.", desc: "Fiberglass Reinforced Pipe" },
  BP1:  { material: "CS",  rating: "150 Lb.", desc: "Carbon Steel Jacketed" },
  BS1:  { material: "SS",  rating: "150 Lb.", desc: "Duplex Stainless Steel S32205" },
  BS2:  { material: "SS",  rating: "150 Lb.", desc: "Duplex S32750" },
  BS3:  { material: "SS",  rating: "150 Lb.", desc: "Duplex S32205" },
  BV1:  { material: "FRP", rating: "150 Lb.", desc: "Dual Laminate PP/FRP" },
  CB1:  { material: "CS",  rating: "300 Lb.", desc: "Carbon Steel" },
  CB2:  { material: "CS",  rating: "300 Lb.", desc: "Impact Tested Carbon Steel" },
  CB3:  { material: "CS",  rating: "300 Lb.", desc: "Carbon Steel" },
  CD1:  { material: "SS",  rating: "300 Lb.", desc: "316/316L Stainless Steel" },
  CD2:  { material: "SS",  rating: "300 Lb.", desc: "316/316L Stainless Steel" },
  CG1:  { material: "SS",  rating: "300 Lb.", desc: "904L Stainless Steel" },
  CG2:  { material: "SS",  rating: "300 Lb.", desc: "904L Stainless Steel" },
  CJ1:  { material: "CS",  rating: "300 Lb.", desc: "1-1/4 Cr-1/2 Mo Chrome Moly" },
  CK3:  { material: "FRP", rating: "300 Lb.", desc: "Fiberglass Reinforced Pipe" },
  CP1:  { material: "CS",  rating: "300 Lb.", desc: "Carbon Steel" },
  CS1:  { material: "SS",  rating: "300 Lb.", desc: "Duplex Stainless Steel S32205" },
  ES2:  { material: "SS",  rating: "600 Lb.", desc: "Super Duplex S32750" },
  FB1:  { material: "CS",  rating: "900/1500 Lb.", desc: "Carbon Steel" },
  FJ1:  { material: "CS",  rating: "900/1500 Lb.", desc: "1-1/4 Cr-1/2 Mo Chrome Moly" },
  GC1:  { material: "SS",  rating: "1500 Lb.", desc: "Stainless Steel SS304H" },
  GD1:  { material: "SS",  rating: "1500 Lb.", desc: "316/316L Stainless Steel" },
  GD2:  { material: "SS",  rating: "1500 Lb.", desc: "316/316L Stainless Steel" },
  KD1:  { material: "SS",  rating: "N/A",      desc: "316/316L Stainless Steel" },
};

// Non-metallic / non-FRP excluded classes — show warning, no auto-fill.
const MPMS_EXCLUDED = {
  BH1: "HDPE",
  BH2: "HDPE",
  BL5: "Rubber Lined Carbon Steel",
  BN1: "PTFE Lined Carbon Steel",
  BR1: "CPVC",
  BT1: "Reinforced Flexible Rubber",
  BX1: "Polypropylene",
  BX2: "Polypropylene",
  BX3: "Polypropylene",
  BY1: "PVC",
  BY3: "PVC",
  BZ1: "PVDF",
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
  nps:         null,
  material:    "",
  pwht:        false,
  insulation:  "uninsulated",
  fn:          null,
  pipingClass: "",
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
  document.getElementById("dnInput").addEventListener("input", handleDNInput);
  document.getElementById("pipingClassInput").addEventListener("input", handlePipingClassInput);
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
function handlePipingClassInput(e) {
  const raw       = e.target.value.trim().toUpperCase();
  const feedback  = document.getElementById("pcFeedback");
  state.pipingClass = raw;

  if (!raw) {
    feedback.textContent = "";
    feedback.className   = "pc-feedback";
    return;
  }

  const excluded = MPMS_EXCLUDED[raw];
  if (excluded) {
    feedback.textContent =
      `Class ${raw} is a non-metallic pipe class (${excluded}). ` +
      `This app covers metallic and FRP pipes only. ` +
      `Please consult the appropriate support standard.`;
    feedback.className = "pc-feedback pc-excluded";
    return;
  }

  const entry = MPMS_CLASSES[raw];
  if (!entry) {
    feedback.textContent = "Class code not found. Please select material manually.";
    feedback.className   = "pc-feedback pc-unknown";
    return;
  }

  // Auto-fill material dropdown
  const sel  = document.getElementById("materialSelect");
  sel.value  = entry.material;
  state.material = entry.material;

  feedback.textContent = `${raw} → ${entry.desc} | ${entry.rating} ✓`;
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
        nps:          state.nps,
        material:     state.material,
        pwht:         state.pwht,
        insulation:   state.insulation,
        function:     state.fn,
        piping_class: state.pipingClass || null,
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
  if (state.pipingClass && MPMS_CLASSES[state.pipingClass]) {
    const pc = MPMS_CLASSES[state.pipingClass];
    pills.push({ key: "Piping Class", val: `${state.pipingClass} — ${pc.desc}` });
  }
  pills.forEach(({ key, val }) => {
    const pill = document.createElement("span");
    pill.className = "summary-pill";
    pill.innerHTML = `<strong>${key}:</strong> ${val}`;
    summaryEl.appendChild(pill);
  });

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
