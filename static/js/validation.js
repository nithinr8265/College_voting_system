/**
 * validation.js — Full client-side form validation for SWC Election Platform
 * Covers: signup, login, OTP, admin login, student/candidate CRUD forms.
 * Works alongside HTML5 required attributes (does NOT replace server-side checks).
 */

"use strict";

/* ══════════════════════════════════════════════════════════════════
   CORE VALIDATOR UTILITIES
   ══════════════════════════════════════════════════════════════════ */

const V = {
  /* Show an error message below a field */
  showError(field, msg) {
    field.classList.remove("is-valid");
    field.classList.add("is-invalid");
    let errEl = field.parentElement.querySelector(".field-error");
    if (!errEl) {
      errEl = document.createElement("span");
      errEl.className = "field-error";
      field.parentElement.appendChild(errEl);
    }
    errEl.innerHTML = `⚠ ${msg}`;
    errEl.classList.add("visible");
  },

  /* Clear error, show green tick */
  showSuccess(field) {
    field.classList.remove("is-invalid");
    field.classList.add("is-valid");
    const errEl = field.parentElement.querySelector(".field-error");
    if (errEl) errEl.classList.remove("visible");
  },

  /* Clear all states */
  clearState(field) {
    field.classList.remove("is-valid", "is-invalid");
    const errEl = field.parentElement.querySelector(".field-error");
    if (errEl) errEl.classList.remove("visible");
  },

  /* ── Individual rules ─────────────────────────────────────────── */
  isEmpty:     (v) => !v || v.trim() === "",
  isEmail:     (v) => /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v.trim()),
  isPhone:     (v) => /^[6-9]\d{9}$/.test(v.trim()),
  isNumeric:   (v) => /^\d+$/.test(v.trim()),
  minLen:      (v, n) => v.trim().length >= n,
  maxLen:      (v, n) => v.trim().length <= n,
  isAlphaSpace:(v) => /^[a-zA-Z\s'-]+$/.test(v.trim()),
  isRollNo:    (v) => /^[A-Za-z0-9]{3,20}$/.test(v.trim()),
  isYear:      (v) => /^\d{4}$/.test(v.trim()) && +v >= 2000 && +v <= new Date().getFullYear() + 1,
  isOTP:       (v) => /^\d{6}$/.test(v.trim()),
  isImageFile: (file) => file && ["image/jpeg", "image/png", "image/jpg", "image/webp"].includes(file.type),
  isFileSizeOK:(file, maxMB = 5) => file && file.size <= maxMB * 1024 * 1024,

  /* Validate one field and return true if valid */
  check(field, rules) {
    const val = field.value;
    for (const [ruleFn, msg] of rules) {
      if (!ruleFn(val, field)) {
        V.showError(field, msg);
        return false;
      }
    }
    V.showSuccess(field);
    return true;
  },

  /* Attach live validation on blur + input */
  live(field, rules) {
    const run = () => V.check(field, rules);
    field.addEventListener("blur",  run);
    field.addEventListener("input", () => {
      if (field.classList.contains("is-invalid")) run();
    });
  },
};

/* ══════════════════════════════════════════════════════════════════
   SHARED RULE SETS
   ══════════════════════════════════════════════════════════════════ */

const RULES = {
  rollNumber: [
    [(v) => !V.isEmpty(v),       "Roll number is required."],
    [(v) => V.isRollNo(v),       "Roll number must be 3–20 alphanumeric characters (e.g. CS22001)."],
  ],
  fullName: [
    [(v) => !V.isEmpty(v),       "Full name is required."],
    [(v) => V.minLen(v, 2),      "Name must be at least 2 characters."],
    [(v) => V.maxLen(v, 80),     "Name must not exceed 80 characters."],
    [(v) => V.isAlphaSpace(v),   "Name can only contain letters, spaces, hyphens, or apostrophes."],
  ],
  email: [
    [(v) => !V.isEmpty(v),       "Email address is required."],
    [(v) => V.isEmail(v),        "Please enter a valid email address (e.g. name@college.edu)."],
  ],
  department: [
    [(v) => !V.isEmpty(v),       "Please select a department."],
  ],
  admissionYear: [
    [(v) => !V.isEmpty(v),       "Admission year is required."],
    [(v) => V.isYear(v),         `Please select a valid admission year (2000–${new Date().getFullYear()}).`],
  ],
  otp: [
    [(v) => !V.isEmpty(v),       "OTP is required."],
    [(v) => V.isOTP(v),          "OTP must be exactly 6 digits."],
  ],
  password: [
    [(v) => !V.isEmpty(v),       "Password is required."],
    [(v) => V.minLen(v, 6),      "Password must be at least 6 characters."],
  ],
  manifesto: [
    [(v) => V.maxLen(v, 1000),   "Manifesto must not exceed 1000 characters."],
  ],
};

/* ══════════════════════════════════════════════════════════════════
   FORM: STUDENT SIGNUP  (/signup)
   ══════════════════════════════════════════════════════════════════ */
function initSignupValidation() {
  const form = document.getElementById("signupForm");
  if (!form) return;

  const fields = {
    roll_number:    form.querySelector("#roll_number"),
    name:           form.querySelector("#name"),
    email:          form.querySelector("#email"),
    department:     form.querySelector("#department"),
    admission_year: form.querySelector("#admission_year"),
    entry_year:     form.querySelector("#entry_year"),
    photo:          form.querySelector("#photo"),
  };

  /* Attach live validators */
  if (fields.roll_number)    V.live(fields.roll_number,    RULES.rollNumber);
  if (fields.name)           V.live(fields.name,           RULES.fullName);
  if (fields.email)          V.live(fields.email,          RULES.email);
  if (fields.department)     V.live(fields.department,     RULES.department);
  if (fields.admission_year) V.live(fields.admission_year, RULES.admissionYear);

  /* Photo file validation */
  if (fields.photo) {
    fields.photo.addEventListener("change", function () {
      const file = this.files[0];
      if (!file) {
        V.showError(this, "Please select a photo.");
        return;
      }
      if (!V.isImageFile(file)) {
        V.showError(this, "Only JPG, PNG, or WEBP images are accepted.");
        this.value = "";
        return;
      }
      if (!V.isFileSizeOK(file, 5)) {
        V.showError(this, "Photo must be smaller than 5 MB.");
        this.value = "";
        return;
      }
      V.showSuccess(this);
    });
  }

  /* Submit validation */
  form.addEventListener("submit", function (e) {
    let valid = true;

    if (fields.roll_number && !V.check(fields.roll_number, RULES.rollNumber))       valid = false;
    if (fields.name        && !V.check(fields.name,        RULES.fullName))          valid = false;
    if (fields.email       && !V.check(fields.email,       RULES.email))             valid = false;
    if (fields.department  && !V.check(fields.department,  RULES.department))        valid = false;
    if (fields.admission_year && !V.check(fields.admission_year, RULES.admissionYear)) valid = false;

    /* Photo required */
    if (fields.photo) {
      const file = fields.photo.files[0];
      if (!file) {
        V.showError(fields.photo, "A face photo is required for identity verification.");
        valid = false;
      } else if (!V.isImageFile(file)) {
        V.showError(fields.photo, "Only JPG, PNG, or WEBP images are accepted.");
        valid = false;
      } else if (!V.isFileSizeOK(file, 5)) {
        V.showError(fields.photo, "Photo must be smaller than 5 MB.");
        valid = false;
      }
    }

    if (!valid) {
      e.preventDefault();
      /* Scroll to first error */
      const firstErr = form.querySelector(".is-invalid");
      if (firstErr) firstErr.scrollIntoView({ behavior: "smooth", block: "center" });
      showFormBanner(form, "⚠ Please fix the highlighted errors before submitting.", "error");
    } else {
      setSubmitLoading(form, "Submitting Registration…");
    }
  });
}

/* ══════════════════════════════════════════════════════════════════
   FORM: STUDENT LOGIN  (/)
   ══════════════════════════════════════════════════════════════════ */
function initLoginValidation() {
  const form = document.querySelector('form[action*="login"]');
  if (!form || document.getElementById("signupForm")) return; /* avoid conflict with signup */

  const rollField  = form.querySelector("#roll_number");
  const emailField = form.querySelector("#email");

  if (rollField)  V.live(rollField,  RULES.rollNumber);
  if (emailField) V.live(emailField, RULES.email);

  form.addEventListener("submit", function (e) {
    let valid = true;
    if (rollField  && !V.check(rollField,  RULES.rollNumber)) valid = false;
    if (emailField && !V.check(emailField, RULES.email))      valid = false;

    if (!valid) {
      e.preventDefault();
      const firstErr = form.querySelector(".is-invalid");
      if (firstErr) firstErr.scrollIntoView({ behavior: "smooth", block: "center" });
    } else {
      setSubmitLoading(form, "Sending OTP…");
    }
  });
}

/* ══════════════════════════════════════════════════════════════════
   FORM: OTP VERIFICATION  (/otp)
   ══════════════════════════════════════════════════════════════════ */
function initOTPValidation() {
  const form     = document.getElementById("otpForm");
  const otpField = document.getElementById("otp");
  if (!form || !otpField) return;

  /* Digits-only enforcer */
  otpField.addEventListener("input", function () {
    this.value = this.value.replace(/\D/g, "").slice(0, 6);
    if (this.value.length === 6) V.showSuccess(this);
    else if (this.value.length > 0) V.clearState(this);
  });

  otpField.addEventListener("blur", () => V.check(otpField, RULES.otp));

  form.addEventListener("submit", function (e) {
    if (!V.check(otpField, RULES.otp)) {
      e.preventDefault();
      otpField.focus();
    } else {
      setSubmitLoading(form, "Verifying…");
    }
  });
}

/* ══════════════════════════════════════════════════════════════════
   FORM: ADMIN LOGIN  (/admin/login)
   ══════════════════════════════════════════════════════════════════ */
function initAdminLoginValidation() {
  const form = document.querySelector('form[action*="admin/login"]');
  if (!form) return;

  const userField = form.querySelector("#username");
  const passField = form.querySelector("#password");

  if (userField) {
    V.live(userField, [
      [(v) => !V.isEmpty(v), "Username is required."],
      [(v) => V.minLen(v, 3), "Username must be at least 3 characters."],
    ]);
  }
  if (passField) {
    V.live(passField, RULES.password);
  }

  form.addEventListener("submit", function (e) {
    let valid = true;
    if (userField && !V.check(userField, [
      [(v) => !V.isEmpty(v), "Username is required."],
      [(v) => V.minLen(v, 3), "Username must be at least 3 characters."],
    ])) valid = false;
    if (passField && !V.check(passField, RULES.password)) valid = false;

    if (!valid) {
      e.preventDefault();
    } else {
      setSubmitLoading(form, "Logging in…");
    }
  });
}

/* ══════════════════════════════════════════════════════════════════
   FORM: ADMIN ADD/EDIT STUDENT MODALS
   ══════════════════════════════════════════════════════════════════ */
function initAdminStudentValidation() {
  /* ── Add Student ────────────────────────────────────────────── */
  const addForm = document.querySelector('form[action*="students/add"]');
  if (addForm) {
    attachStudentRules(addForm, true);
  }

  /* ── Edit Student ───────────────────────────────────────────── */
  const editForm = document.querySelector('form[action*="students/edit"]');
  if (editForm) {
    attachStudentRules(editForm, false);
  }
}

function attachStudentRules(form, requirePhoto) {
  const f = {
    roll:     form.querySelector('[name="roll_number"]'),
    name:     form.querySelector('[name="name"]'),
    email:    form.querySelector('[name="email"]'),
    dept:     form.querySelector('[name="department"]'),
    admYear:  form.querySelector('[name="admission_year"]'),
    photo:    form.querySelector('[name="photo"]'),
  };

  if (f.roll)    V.live(f.roll,   RULES.rollNumber);
  if (f.name)    V.live(f.name,   RULES.fullName);
  if (f.email)   V.live(f.email,  RULES.email);
  if (f.dept)    V.live(f.dept,   RULES.department);
  if (f.admYear) V.live(f.admYear,RULES.admissionYear);

  if (f.photo) {
    f.photo.addEventListener("change", function () {
      const file = this.files[0];
      if (!file) return;
      if (!V.isImageFile(file)) {
        V.showError(this, "Only JPG, PNG, or WEBP images are accepted.");
        this.value = "";
      } else if (!V.isFileSizeOK(file, 5)) {
        V.showError(this, "Photo must be smaller than 5 MB.");
        this.value = "";
      } else {
        V.showSuccess(this);
      }
    });
  }

  form.addEventListener("submit", function (e) {
    let valid = true;
    if (f.roll    && !V.check(f.roll,    RULES.rollNumber))    valid = false;
    if (f.name    && !V.check(f.name,    RULES.fullName))      valid = false;
    if (f.email   && !V.check(f.email,   RULES.email))         valid = false;
    if (f.dept    && !V.check(f.dept,    RULES.department))    valid = false;
    if (f.admYear && !V.check(f.admYear, RULES.admissionYear)) valid = false;

    if (requirePhoto && f.photo && !f.photo.files[0]) {
      V.showError(f.photo, "A face photo is required.");
      valid = false;
    }

    if (!valid) {
      e.preventDefault();
      const firstErr = form.querySelector(".is-invalid");
      if (firstErr) firstErr.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  });
}

/* ══════════════════════════════════════════════════════════════════
   FORM: ADMIN ADD/EDIT CANDIDATE MODALS
   ══════════════════════════════════════════════════════════════════ */
function initAdminCandidateValidation() {
  const addForm  = document.querySelector('form[action*="candidates/add"]');
  const editForm = document.querySelector('form[action*="candidates/edit"]');

  [addForm, editForm].forEach((form) => {
    if (!form) return;

    const f = {
      name:     form.querySelector('[name="name"]'),
      position: form.querySelector('[name="position"]'),
      manifesto:form.querySelector('[name="manifesto"]'),
      photo:    form.querySelector('[name="photo"]'),
    };

    if (f.name)     V.live(f.name,     RULES.fullName);
    if (f.position) V.live(f.position, [[(v) => !V.isEmpty(v), "Please select a position."]]);
    if (f.manifesto)V.live(f.manifesto, RULES.manifesto);

    if (f.photo) {
      f.photo.addEventListener("change", function () {
        const file = this.files[0];
        if (!file) return;
        if (!V.isImageFile(file)) {
          V.showError(this, "Only JPG, PNG, or WEBP images are accepted.");
          this.value = "";
        } else if (!V.isFileSizeOK(file, 5)) {
          V.showError(this, "Photo must be smaller than 5 MB.");
          this.value = "";
        } else {
          V.showSuccess(this);
        }
      });
    }

    /* Manifesto char counter */
    if (f.manifesto) {
      addCharCounter(f.manifesto, 1000);
    }

    form.addEventListener("submit", function (e) {
      let valid = true;
      if (f.name     && !V.check(f.name,     RULES.fullName))  valid = false;
      if (f.position && !V.check(f.position, [[(v) => !V.isEmpty(v), "Please select a position."]])) valid = false;
      if (f.manifesto && !V.check(f.manifesto, RULES.manifesto)) valid = false;

      if (!valid) {
        e.preventDefault();
        const firstErr = form.querySelector(".is-invalid");
        if (firstErr) firstErr.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    });
  });
}

/* ══════════════════════════════════════════════════════════════════
   FORM: ADMIN ELECTION SETTINGS
   ══════════════════════════════════════════════════════════════════ */
function initSettingsValidation() {
  const form = document.getElementById("settingsForm");
  if (!form) return;

  const startDate  = form.querySelector("#start_date");
  const endDate    = form.querySelector("#end_date");
  const resultDate = form.querySelector("#result_date");

  form.addEventListener("submit", function (e) {
    let valid = true;

    /* If both dates provided, end must be after start */
    if (startDate && endDate && startDate.value && endDate.value) {
      if (new Date(endDate.value) <= new Date(startDate.value)) {
        V.showError(endDate, "End date must be after the start date.");
        valid = false;
      } else {
        V.showSuccess(endDate);
      }
    }

    /* Result date must be on or after end date */
    if (endDate && resultDate && endDate.value && resultDate.value) {
      if (new Date(resultDate.value) < new Date(endDate.value)) {
        V.showError(resultDate, "Result date must be on or after the election end date.");
        valid = false;
      } else {
        V.showSuccess(resultDate);
      }
    }

    if (!valid) {
      e.preventDefault();
      showFormBanner(form, "⚠ Please fix the date errors before saving.", "error");
    }
  });
}

/* ══════════════════════════════════════════════════════════════════
   BALLOT VALIDATION (extra checks beyond vote.js)
   ══════════════════════════════════════════════════════════════════ */
function initBallotValidation() {
  const form = document.getElementById("ballotForm");
  if (!form) return;

  /* Highlight un-selected sections on scroll */
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const section = entry.target;
        const name = section.querySelector("input[type=radio]")?.name;
        if (!name) return;
        const checked = form.querySelector(`input[name="${name}"]:checked`);
        section.style.opacity = "1";
        if (!checked) {
          section.querySelector(".ballot-position-header")?.classList.add("needs-selection");
        }
      });
    },
    { threshold: 0.3 }
  );

  form.querySelectorAll(".ballot-section").forEach((sec) => observer.observe(sec));
}

/* ══════════════════════════════════════════════════════════════════
   HELPERS
   ══════════════════════════════════════════════════════════════════ */

/* Show/update a banner above the submit button */
function showFormBanner(form, msg, type) {
  let banner = form.querySelector(".form-submit-banner");
  if (!banner) {
    banner = document.createElement("div");
    banner.className = "form-submit-banner";
    banner.style.cssText = `
      padding:.75rem 1rem;border-radius:8px;font-size:.85rem;font-weight:600;
      margin-bottom:1rem;display:flex;align-items:center;gap:8px;
    `;
    const submitBtn = form.querySelector('[type="submit"]');
    if (submitBtn) form.insertBefore(banner, submitBtn);
    else form.appendChild(banner);
  }
  if (type === "error") {
    banner.style.background = "#ffebee";
    banner.style.color      = "#c62828";
    banner.style.border     = "1px solid #c62828";
  } else {
    banner.style.background = "#e8f5e9";
    banner.style.color      = "#2e7d32";
    banner.style.border     = "1px solid #2e7d32";
  }
  banner.textContent = msg;
  banner.scrollIntoView({ behavior: "smooth", block: "center" });

  setTimeout(() => { if (banner.parentElement) banner.remove(); }, 6000);
}

/* Disable submit button + show spinner text while form submits */
function setSubmitLoading(form, label) {
  const btn = form.querySelector('[type="submit"]');
  if (!btn) return;
  btn.disabled     = true;
  btn.dataset.orig = btn.innerHTML;
  btn.innerHTML    = `
    <span style="display:inline-block;width:16px;height:16px;border:2.5px solid rgba(255,255,255,.4);
    border-top-color:#fff;border-radius:50%;animation:spin .7s linear infinite;
    vertical-align:middle;margin-right:6px;"></span>${label}
  `;
  /* Restore after 10s in case of server error */
  setTimeout(() => {
    btn.disabled  = false;
    btn.innerHTML = btn.dataset.orig || btn.innerHTML;
  }, 10000);
}

/* Add character counter below a textarea */
function addCharCounter(textarea, max) {
  const counter = document.createElement("div");
  counter.className = "char-counter";

  function update() {
    const len = textarea.value.length;
    counter.textContent = `${len} / ${max}`;
    counter.className = "char-counter";
    if (len > max * 0.9) counter.classList.add("near-limit");
    if (len > max)       counter.classList.add("over-limit");
  }

  textarea.addEventListener("input", update);
  textarea.parentElement.appendChild(counter);
  update();
}

/* ══════════════════════════════════════════════════════════════════
   GLOBAL UI ENHANCEMENTS
   ══════════════════════════════════════════════════════════════════ */

/* Prevent double-submit on all forms */
function preventDoubleSubmit() {
  document.querySelectorAll("form").forEach((form) => {
    let submitted = false;
    form.addEventListener("submit", function (e) {
      if (submitted) {
        e.preventDefault();
        return;
      }
      submitted = true;
      /* Reset after 12s */
      setTimeout(() => { submitted = false; }, 12000);
    });
  });
}

/* File input: show selected file name */
function enhanceFileInputs() {
  document.querySelectorAll('input[type="file"]').forEach((input) => {
    if (input.id === "photo") return; /* handled by signup preview */
    input.addEventListener("change", function () {
      const file = this.files[0];
      if (!file) return;
      let label = this.parentElement.querySelector(".file-name-label");
      if (!label) {
        label = document.createElement("span");
        label.className = "file-name-label";
        label.style.cssText = "font-size:.76rem;color:var(--success);margin-top:4px;display:block;";
        this.parentElement.appendChild(label);
      }
      label.textContent = `✅ Selected: ${file.name} (${(file.size / 1024).toFixed(0)} KB)`;
    });
  });
}

/* Smooth scroll to first flash message */
function scrollToFlash() {
  const flash = document.querySelector(".flash-container .flash");
  if (flash) {
    setTimeout(() => flash.scrollIntoView({ behavior: "smooth", block: "center" }), 150);
  }
}

/* Touch: add active state to buttons on mobile */
function enhanceTouchTargets() {
  document.querySelectorAll(".btn, .ballot-candidate-inner, .sidebar-link").forEach((el) => {
    el.addEventListener("touchstart", () => el.classList.add("touch-active"), { passive: true });
    el.addEventListener("touchend",   () => setTimeout(() => el.classList.remove("touch-active"), 150));
  });
}

/* Confirm before destructive actions */
function attachDeleteConfirms() {
  document.querySelectorAll('button[type="submit"].btn-danger').forEach((btn) => {
    if (btn.closest("form")?.action?.includes("delete") || btn.closest("form")?.action?.includes("reject")) {
      btn.addEventListener("click", function (e) {
        if (!confirm("⚠️ Are you sure? This action cannot be undone.")) {
          e.preventDefault();
        }
      });
    }
  });
}

/* Auto-format roll number to uppercase */
function autoFormatRollNumber() {
  document.querySelectorAll('[name="roll_number"], #roll_number').forEach((input) => {
    input.addEventListener("input", function () {
      const pos = this.selectionStart;
      this.value = this.value.toUpperCase().replace(/[^A-Z0-9]/g, "");
      try { this.setSelectionRange(pos, pos); } catch (_) {}
    });
  });
}

/* Navbar active link highlight */
function highlightNavLink() {
  const path = window.location.pathname;
  document.querySelectorAll(".nav-links a").forEach((link) => {
    if (link.getAttribute("href") === path) {
      link.style.background = "rgba(255,255,255,0.18)";
      link.style.color      = "#fff";
    }
  });
}

/* ══════════════════════════════════════════════════════════════════
   BOOTSTRAP — run on DOM ready
   ══════════════════════════════════════════════════════════════════ */
document.addEventListener("DOMContentLoaded", function () {
  /* Form-specific validators */
  initSignupValidation();
  initLoginValidation();
  initOTPValidation();
  initAdminLoginValidation();
  initAdminStudentValidation();
  initAdminCandidateValidation();
  initSettingsValidation();
  initBallotValidation();

  /* Global enhancements */
  preventDoubleSubmit();
  enhanceFileInputs();
  scrollToFlash();
  enhanceTouchTargets();
  attachDeleteConfirms();
  autoFormatRollNumber();
  highlightNavLink();

  /* Inject spin keyframe for loading buttons */
  if (!document.getElementById("__swcSpinStyle")) {
    const style = document.createElement("style");
    style.id = "__swcSpinStyle";
    style.textContent = "@keyframes spin{to{transform:rotate(360deg)}}";
    document.head.appendChild(style);
  }
});
