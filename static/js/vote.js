/**
 * vote.js — Ballot page: confirmation modal + vote summary for SWC Election Platform
 * Intercepts form submit, shows a summary of selections, then submits on confirm.
 */

(function () {
  "use strict";

  /* ── DOM REFS ──────────────────────────────────────────────────── */
  const castVoteBtn   = document.getElementById("castVoteBtn");
  const confirmModal  = document.getElementById("confirmModal");
  const confirmVoteBtn= document.getElementById("confirmVoteBtn");
  const cancelVoteBtn = document.getElementById("cancelVoteBtn");
  const voteSummary   = document.getElementById("voteSummary");
  const ballotForm    = document.getElementById("ballotForm");

  if (!castVoteBtn || !confirmModal || !ballotForm) return; // not on ballot page

  /* ── POSITION ICON MAP ─────────────────────────────────────────── */
  const positionIcons = {
    "President":         "👑",
    "Vice President":    "🎖️",
    "Secretary":         "📋",
    "Treasurer":         "💰",
    "Sports Secretary":  "⚽",
    "Cultural Secretary":"🎭",
  };

  /* ── COLLECT SELECTIONS ────────────────────────────────────────── */
  function getSelections() {
    const selections = [];
    const radios = ballotForm.querySelectorAll('input[type="radio"]:checked');

    radios.forEach(radio => {
      // name format: "candidate_<Position>"
      const position = radio.name.replace("candidate_", "");
      const label    = ballotForm.querySelector(`label[for="${radio.id}"]`);
      const nameEl   = label ? label.querySelector(".ballot-name") : null;
      const deptEl   = label ? label.querySelector(".ballot-dept") : null;

      selections.push({
        position,
        candidateName: nameEl ? nameEl.textContent.trim() : radio.value,
        department:    deptEl ? deptEl.textContent.trim() : "",
      });
    });

    return selections;
  }

  /* ── VALIDATE: ALL POSITIONS SELECTED ─────────────────────────── */
  function validateAllSelected() {
    // Find all radio groups (each position has a unique name)
    const names  = new Set();
    const checked = new Set();

    ballotForm.querySelectorAll('input[type="radio"]').forEach(r => {
      names.add(r.name);
      if (r.checked) checked.add(r.name);
    });

    const missing = [...names].filter(n => !checked.has(n));
    return { valid: missing.length === 0, missing };
  }

  /* ── RENDER VOTE SUMMARY ───────────────────────────────────────── */
  function renderSummary(selections) {
    if (!voteSummary) return;

    if (selections.length === 0) {
      voteSummary.innerHTML = "<p style='color:var(--text-muted);'>No selections detected.</p>";
      return;
    }

    voteSummary.innerHTML = selections
      .map(s => {
        const icon = positionIcons[s.position] || "🏅";
        return `
          <div class="vote-summary-item">
            <span><strong>${icon} ${s.position}</strong></span>
            <span>
              <strong>${s.candidateName}</strong>
              ${s.department ? `<span style="color:var(--text-muted);font-size:0.78rem;"> — ${s.department}</span>` : ""}
            </span>
          </div>
        `;
      })
      .join("");
  }

  /* ── OPEN MODAL ────────────────────────────────────────────────── */
  castVoteBtn.addEventListener("click", function () {
    const { valid, missing } = validateAllSelected();

    if (!valid) {
      // Highlight missing positions
      missing.forEach(name => {
        const group = ballotForm.querySelector(`input[name="${name}"]`);
        if (group) {
          const section = group.closest(".ballot-section");
          if (section) {
            section.style.outline = "2px solid var(--danger)";
            section.style.borderRadius = "12px";
            setTimeout(() => { section.style.outline = ""; }, 3000);
            section.scrollIntoView({ behavior: "smooth", block: "center" });
          }
        }
      });

      showInlineError(
        `⚠️ Please select a candidate for all ${missing.length} remaining position${missing.length > 1 ? "s" : ""}.`
      );
      return;
    }

    clearInlineError();
    const selections = getSelections();
    renderSummary(selections);
    openModal();
  });

  /* ── CONFIRM VOTE → SUBMIT FORM ────────────────────────────────── */
  confirmVoteBtn.addEventListener("click", function () {
    confirmVoteBtn.disabled  = true;
    confirmVoteBtn.innerHTML = '<span style="display:inline-block;width:16px;height:16px;border:3px solid rgba(255,255,255,0.4);border-top-color:#fff;border-radius:50%;animation:spin 0.7s linear infinite;vertical-align:middle;margin-right:6px;"></span> Submitting…';

    // Inject spin keyframes if not already present
    if (!document.getElementById("spinStyle")) {
      const s = document.createElement("style");
      s.id = "spinStyle";
      s.textContent = "@keyframes spin { to { transform: rotate(360deg); } }";
      document.head.appendChild(s);
    }

    closeModal();
    ballotForm.submit();
  });

  /* ── CANCEL ────────────────────────────────────────────────────── */
  cancelVoteBtn.addEventListener("click", closeModal);

  // Close on backdrop click
  confirmModal.addEventListener("click", function (e) {
    if (e.target === confirmModal) closeModal();
  });

  // Close on Escape key
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeModal();
  });

  /* ── VISUAL FEEDBACK ON RADIO SELECT ──────────────────────────── */
  ballotForm.querySelectorAll('input[type="radio"].ballot-radio').forEach(radio => {
    radio.addEventListener("change", function () {
      // When a candidate is selected, briefly animate the card
      const label = ballotForm.querySelector(`label[for="${this.id}"]`);
      if (!label) return;
      const inner = label.querySelector(".ballot-candidate-inner");
      if (!inner) return;
      inner.style.transform = "scale(1.02)";
      setTimeout(() => { inner.style.transform = ""; }, 200);

      // Deselect highlight from siblings in same position group
      ballotForm
        .querySelectorAll(`input[name="${this.name}"]`)
        .forEach(r => {
          const l = ballotForm.querySelector(`label[for="${r.id}"]`);
          if (!l) return;
          // CSS handles the styling via :checked, this is just for animation
        });
    });
  });

  /* ── HELPERS ───────────────────────────────────────────────────── */
  function openModal() {
    confirmModal.style.display = "flex";
    document.body.style.overflow = "hidden";
  }

  function closeModal() {
    confirmModal.style.display = "none";
    document.body.style.overflow = "";
    if (confirmVoteBtn) {
      confirmVoteBtn.disabled  = false;
      confirmVoteBtn.innerHTML = "✅ Yes, Cast My Vote";
    }
  }

  function showInlineError(msg) {
    let errEl = document.getElementById("ballotInlineError");
    if (!errEl) {
      errEl = document.createElement("div");
      errEl.id        = "ballotInlineError";
      errEl.className = "ballot-warning";
      errEl.style.cssText = "margin-top:1rem; background:#ffebee; border-color:var(--danger); color:var(--danger);";
      const submitArea = document.querySelector(".ballot-submit-area");
      if (submitArea) submitArea.insertAdjacentElement("beforebegin", errEl);
    }
    errEl.textContent   = msg;
    errEl.style.display = "block";
    errEl.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  function clearInlineError() {
    const errEl = document.getElementById("ballotInlineError");
    if (errEl) errEl.style.display = "none";
  }

})();
