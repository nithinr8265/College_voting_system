"""
app.py — College Online Voting System (SWC Election Platform)
Main Flask application: all student + admin routes.
"""
import base64
import datetime
import os

import bcrypt
from dotenv import load_dotenv
from flask import (Flask, flash, jsonify, redirect, render_template,
                   request, session, url_for)
from flask_mail import Mail

import db
from face_service import verify_face
from mail_service import generate_otp, send_otp_email
from validators import (validate_student_form, validate_candidate_form, validate_settings_form, valid_otp, valid_email, valid_roll_number, is_empty, valid_image_extension, valid_file_size)

load_dotenv()

app = Flask(__name__)
from datetime import timedelta

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "swc_super_secret_key_2026"
)

app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

app.permanent_session_lifetime = timedelta(minutes=30)

# ── Flask-Mail (Gmail SMTP) ────────────────────────────────────────────
app.config["MAIL_SERVER"]   = "smtp.gmail.com"
app.config["MAIL_PORT"]     = 587
app.config["MAIL_USE_TLS"]  = True
app.config["MAIL_USERNAME"] = os.environ.get("GMAIL_ADDRESS")
app.config["MAIL_PASSWORD"] = os.environ.get("GMAIL_APP_PASSWORD")

mail = Mail(app)


# ══════════════════════════ HELPERS ════════════════════════════════════

def _get_academic_year() -> int:
    """Return the current academic year (starts July each year)."""
    now = datetime.datetime.now()
    return now.year if now.month >= 7 else now.year - 1


MASTER_DEPARTMENTS = {
    # Exactly as stored in DB (match the dropdown option values)
    "MA", "MSC", "MBA", "MCA", 
    # Legacy / alternate spellings already in DB from old form
    "Msc", "M.Sc", "M.A",
}

def get_program_years(department: str) -> int:
    """Return number of voting-eligible years based on degree type.
    Master's / PG programs → 2 years.
    Bachelor's / UG programs → 3 years.
    """
    if not department:
        return 3
    dept_clean = department.strip()
    # Case-insensitive check against known master's programs
    for m in MASTER_DEPARTMENTS:
        if dept_clean.lower() == m.lower():
            return 2
    return 3


def is_eligible_to_vote(student: dict) -> bool:
    """
    Eligibility rule:
      - Master's/PG degree (MA, MSC, MBA, MCA, …) = 2 years.
      - Bachelor's/UG degree (all others)                 = 3 years.
      - admission_year : calendar year student was first admitted.
      - entry_year     : 1 = normal first year,
                         2 = lateral entry (2nd year),
                         3 = lateral entry (3rd year — UG only).
      - last_eligible_academic_year = admission_year + (program_years - entry_year)
      - Student can vote only if current_academic_year <= last_eligible_year.

    UG examples (3-year degree):
      1st yr entry 2022 → eligible 2022, 2023, 2024  (last = 2024)
      2nd yr entry 2022 → eligible 2022, 2023         (last = 2023)
      3rd yr entry 2022 → eligible 2022 only           (last = 2022)

    PG examples (2-year degree):
      1st yr entry 2022 → eligible 2022, 2023         (last = 2023)
      2nd yr entry 2022 → eligible 2022 only           (last = 2022)
    """
    admission_year = student.get("admission_year")
    entry_year     = student.get("entry_year", 1) or 1
    department     = student.get("department", "") or ""

    if not admission_year:
        return True  # No year data → assume eligible

    program_years = get_program_years(department)
    last_eligible = int(admission_year) + (program_years - int(entry_year))
    current_ay    = _get_academic_year()
    return current_ay <= last_eligible


def _require_student(fn):
    """Decorator: redirect to login if student not in session."""
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "student_roll" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("index"))
        return fn(*args, **kwargs)
    return wrapper


def _require_admin(fn):
    """Decorator: redirect to admin login if admin not in session."""
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            flash("Admin login required.", "error")
            return redirect(url_for("admin_login"))
        return fn(*args, **kwargs)
    return wrapper


def _parse_election_dt(value) -> "datetime.datetime | None":
    """Parse a datetime-local string (YYYY-MM-DDTHH:MM or YYYY-MM-DD) into a datetime.
    Returns None if value is empty or unparseable."""
    if not value:
        return None
    s = str(value).strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(s[:19], fmt)
        except ValueError:
            pass
    # last try: date only (10 chars)
    try:
        return datetime.datetime.strptime(s[:10], "%Y-%m-%d")
    except ValueError:
        return None


def _compute_election_active(settings) -> bool:
    """Returns True if the election is currently active, respecting schedule over manual toggle."""
    if not settings:
        return False
    now = datetime.datetime.now()
    start_dt = _parse_election_dt(settings.get("start_date"))
    end_dt   = _parse_election_dt(settings.get("end_date"))
    if start_dt and end_dt:
        return start_dt <= now <= end_dt
    return bool(settings.get("is_active"))


# Canonical order positions appear in voting steps and admin view
POSITIONS_ORDER = ["President", "Vice President", "Secretary", "Treasurer"]


# ══════════════════════════ STUDENT ROUTES ═════════════════════════════

@app.route("/")
def index():
    return render_template("login.html")


# ── SIGNUP ─────────────────────────────────────────────────────────────
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        roll_number    = request.form.get("roll_number", "").strip()
        name           = request.form.get("name", "").strip()
        email          = request.form.get("email", "").strip().lower()
        department     = request.form.get("department", "").strip()
        year           = request.form.get("year", "1")
        admission_year = request.form.get("admission_year", "").strip()
        entry_year     = request.form.get("entry_year", "1")
        photo          = request.files.get("photo")

        # ── Server-side validation ──────────────────────────────────
        errors = validate_student_form({
            "roll_number":    roll_number,
            "name":           name,
            "email":          email,
            "department":     department,
            "admission_year": admission_year,
            "entry_year":     entry_year,
            "year":           year,
        }, require_roll=True)

        if not photo or not photo.filename:
            errors.append("Profile photo is required for face recognition.")
        elif photo.filename and not valid_image_extension(photo.filename):
            errors.append("Photo must be a JPG, PNG, or WEBP image.")
        elif not valid_file_size(photo, max_mb=5):
            errors.append("Photo file must be smaller than 5 MB.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("signup.html",
                                   form=request.form,
                                   current_year=datetime.datetime.now().year)

        # ── Duplicate check ─────────────────────────────────────────
        if db.get_student_by_roll(roll_number):
            flash("A student with this roll number already exists.", "error")
            return render_template("signup.html",
                                   form=request.form,
                                   current_year=datetime.datetime.now().year)

        if db.get_student_by_email(email):
            flash("This email is already registered.", "error")
            return render_template("signup.html",
                                   form=request.form,
                                   current_year=datetime.datetime.now().year)

        # ── Photo → base64 ─────────────────────────────────────────
        photo_data = base64.b64encode(photo.read()).decode("utf-8")

        student_data = {
            "roll_number":    roll_number,
            "name":           name,
            "email":          email,
            "department":     department,
            "year":           int(year),
            "admission_year": int(admission_year),
            "entry_year":     int(entry_year),
            "photo_base64":   photo_data,
            "has_voted":      False,
            "is_approved":    False,   # Admin must approve before login
        }

        try:
            db.add_student(student_data)
            flash(
                "✅ Registration submitted! Your account is pending admin approval. "
                "You will be able to log in once approved.",
                "success",
            )
            return redirect(url_for("index"))
        except Exception as exc:
            flash(f"Registration failed: {exc}", "error")

    return render_template("signup.html",
                           form={},
                           current_year=datetime.datetime.now().year)


# ── LOGIN ──────────────────────────────────────────────────────────────
@app.route("/login", methods=["POST"])
def login():
    roll_number = request.form.get("roll_number", "").strip()
    email       = request.form.get("email", "").strip().lower()

    student = db.get_student_by_roll_and_email(roll_number, email)

    if not student:
        flash("Student not found. Please check your roll number and email.", "error")
        return render_template("login.html")

    if not student.get("is_approved"):
        flash("Your account is awaiting admin approval. Please try again later.", "error")
        return render_template("login.html")

    if not is_eligible_to_vote(student):
        entry_yr  = student.get("entry_year", 1) or 1
        adm_yr    = student.get("admission_year", "N/A")
        dept      = student.get("department", "") or ""
        prog_yrs  = get_program_years(dept)
        last      = int(adm_yr) + (prog_yrs - int(entry_yr)) if adm_yr != "N/A" else "N/A"
        flash(
            f"You are no longer eligible to vote. "
            f"Your {prog_yrs}-year voting period ended at academic year {last}.",
            "error",
        )
        return render_template("login.html")

    otp = generate_otp()
    session.permanent        = True          # honour permanent_session_lifetime (30 min)
    session["otp"]           = otp
    session["otp_time"]      = datetime.datetime.now().isoformat()
    session["student_roll"]  = roll_number
    session["student_name"]  = student["name"]
    session["student_email"] = email
    session["face_verified"] = False

    try:
        send_otp_email(app, mail, email, otp, student["name"])
        return redirect(url_for("otp_page"))
    except Exception as exc:
        session.clear()
        flash(f"Failed to send OTP email: {exc}", "error")
        return render_template("login.html")


# ── OTP ────────────────────────────────────────────────────────────────
@app.route("/otp")
def otp_page():
    print("OTP PAGE SESSION:", dict(session))

    return render_template(
        "otp.html",
        email=session.get("student_email", "")
    )


@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    entered = request.form.get("otp", "").strip()

    print("VERIFY SESSION:", dict(session))

    if "otp" not in session:
        flash("Session expired. Please log in again.", "error")
        return redirect(url_for("index"))

    stored = session.get("otp")

    if entered != stored:
        flash("Invalid OTP. Please try again.", "error")
        return render_template(
            "otp.html",
            email=session.get("student_email", "")
        )

    # Remove OTP after successful verification
    session.pop("otp", None)
    session.pop("otp_time", None)

    session.modified = True

    return redirect(url_for("dashboard"))


@app.route("/resend-otp", methods=["POST"])
def resend_otp():
    if "student_roll" not in session:
        return redirect(url_for("index"))

    otp = generate_otp()
    session["otp"]      = otp
    session["otp_time"] = datetime.datetime.now().isoformat()

    try:
        send_otp_email(app, mail, session["student_email"], otp, session["student_name"])
        flash("New OTP sent to your email.", "success")
    except Exception as exc:
        flash(f"Failed to send OTP: {exc}", "error")

    return redirect(url_for("otp_page"))


# ── DASHBOARD ──────────────────────────────────────────────────────────
@app.route("/dashboard")
@_require_student
def dashboard():
    student              = db.get_student_by_roll(session["student_roll"])
    candidates_by_pos    = db.get_candidates_by_position()
    settings             = db.get_election_settings()
    election_active      = _compute_election_active(settings)
    return render_template("dashboard.html",
                           student=student,
                           candidates_by_position=candidates_by_pos,
                           settings=settings,
                           election_active=election_active)


# ── FACE VERIFY ────────────────────────────────────────────────────────
@app.route("/face-verify")
@_require_student
def face_verify_page():
    student = db.get_student_by_roll(session["student_roll"])
    if student and student.get("has_voted"):
        flash("You have already voted.", "info")
        return redirect(url_for("thankyou"))
    return render_template("face_verify.html")


@app.route("/verify-face", methods=["POST"])
@_require_student
def verify_face_route():
    data       = request.get_json(silent=True) or {}
    live_image = data.get("image", "")

    if not live_image:
        return jsonify({"match": False, "error": "No image received."})

    student = db.get_student_by_roll(session["student_roll"])
    if not student or not student.get("photo_base64"):
        return jsonify({"match": False,
                        "error": "No reference photo found. Contact admin."})

    matched = verify_face(live_image, student["photo_base64"])

    if matched:
        session["face_verified"] = True

    return jsonify({"match": matched})


# ── BALLOT ENTRY — redirects to step 0 ────────────────────────────────
@app.route("/ballot")
@_require_student
def ballot():
    if not session.get("face_verified"):
        flash("Face verification required before voting.", "error")
        return redirect(url_for("face_verify_page"))

    student = db.get_student_by_roll(session["student_roll"])
    if student and student.get("has_voted"):
        flash("You have already cast your vote.", "info")
        return redirect(url_for("thankyou"))

    settings = db.get_election_settings()
    if not _compute_election_active(settings):
        if not settings:
            flash("Election settings not configured yet.", "error")
        else:
            now = datetime.datetime.now()
            start_dt = _parse_election_dt(settings.get("start_date"))
            end_dt   = _parse_election_dt(settings.get("end_date"))
            if start_dt and end_dt and now < start_dt:
                flash(f"Voting has not started yet. Opens on {start_dt.strftime('%d %b %Y at %I:%M %p')}.", "error")
            else:
                flash("Voting is currently not active. Please check back later.", "error")
        return redirect(url_for("dashboard"))

    candidates_by_pos = db.get_candidates_by_position()
    if not candidates_by_pos:
        flash("No candidates have been added yet.", "error")
        return redirect(url_for("dashboard"))

    # Reset pending votes and start from position 0
    session["pending_votes"] = {}
    return redirect(url_for("ballot_step", step=0))


# ── BALLOT STEP — one position per page ────────────────────────────────
@app.route("/ballot/step/<int:step>", methods=["GET", "POST"])
@_require_student
def ballot_step(step):
    if not session.get("face_verified"):
        flash("Face verification required before voting.", "error")
        return redirect(url_for("face_verify_page"))

    try:
        student = db.get_student_by_roll(session["student_roll"])
    except Exception:
        flash("Connection error. Please try again.", "error")
        return redirect(url_for("ballot_step", step=step))

    if not student:
        flash("Unable to connect to database. Please try again.")
        return redirect(url_for("login"))
    
    if student and student.get("has_voted"):
        return redirect(url_for("thankyou"))

    # Make sure election is still active
    settings = db.get_election_settings()
    if not _compute_election_active(settings):
        flash("Voting has closed.", "error")
        return redirect(url_for("dashboard"))

    candidates_by_pos = db.get_candidates_by_position()
    # Build ordered list of positions (known order first, then any extras)
    positions = [p for p in POSITIONS_ORDER if p in candidates_by_pos]
    for p in candidates_by_pos:
        if p not in positions:
            positions.append(p)

    if not positions or step >= len(positions):
        # All positions done — commit votes
        return redirect(url_for("submit_all_votes"))

    current_position = positions[step]
    candidates       = candidates_by_pos[current_position]
    is_last          = (step == len(positions) - 1)
    total            = len(positions)

    if request.method == "POST":
        candidate_id = request.form.get("candidate_id", "").strip()
        if not candidate_id:
            flash(f"Please select a candidate for {current_position}.", "error")
            return redirect(url_for("ballot_step", step=step))

        # Store in session (session dicts need reassignment to trigger save)
        pending = dict(session.get("pending_votes", {}))
        pending[current_position] = candidate_id
        session["pending_votes"] = pending

        if is_last:
            return redirect(url_for("submit_all_votes"))
        return redirect(url_for("ballot_step", step=step + 1))

    # Build detail dict so the confirmation modal can show real candidate names
    pending = session.get("pending_votes", {})
    pending_votes_detail = {}
    for pos, cid in pending.items():
        c = db.get_candidate_by_id(cid)
        if c:
            pending_votes_detail[pos] = {"name": c.get("name", "Unknown")}

    return render_template("ballot_step.html",
                        position=current_position,
                        candidates=candidates,
                        step=step,
                        total_steps=total,
                        is_last=is_last,
                        student=student,
                        pending_votes=pending,
                        pending_votes_detail=pending_votes_detail)


# ── SUBMIT ALL VOTES (final commit after all steps) ────────────────────
@app.route("/submit-all-votes")
@_require_student
def submit_all_votes():
    if not session.get("face_verified"):
        return redirect(url_for("face_verify_page"))

    student = db.get_student_by_roll(session["student_roll"])
    if student and student.get("has_voted"):
        return redirect(url_for("thankyou"))

    votes = session.get("pending_votes", {})
    if not votes:
        flash("No votes recorded. Please restart the voting process.", "error")
        return redirect(url_for("ballot"))

    for position, candidate_id in votes.items():
        db.insert_vote(student["id"], candidate_id, position)
        db.increment_vote_count(candidate_id)

    db.set_student_voted(session["student_roll"], datetime.datetime.now().isoformat())
    session["face_verified"]  = False
    session["vote_submitted"] = True
    session.pop("pending_votes", None)

    return redirect(url_for("thankyou"))


# ── SUBMIT VOTE ────────────────────────────────────────────────────────
@app.route("/submit-vote", methods=["POST"])
@_require_student
def submit_vote():
    if not session.get("face_verified"):
        return redirect(url_for("face_verify_page"))

    student = db.get_student_by_roll(session["student_roll"])
    if student and student.get("has_voted"):
        return "Already voted.", 403

    # Gather votes: form fields named "candidate_<Position>"
    votes: dict = {}
    for key, value in request.form.items():
        if key.startswith("candidate_"):
            position = key[len("candidate_"):]
            votes[position] = value

    if not votes:
        flash("Please select a candidate for each position.", "error")
        return redirect(url_for("ballot"))

    # Persist each vote
    for position, candidate_id in votes.items():
        db.insert_vote(student["id"], candidate_id, position)
        db.increment_vote_count(candidate_id)

    db.set_student_voted(session["student_roll"],
                         datetime.datetime.now().isoformat())

    session["face_verified"]  = False
    session["vote_submitted"] = True

    return redirect(url_for("thankyou"))


# ── THANK YOU ──────────────────────────────────────────────────────────
@app.route("/thankyou")
@_require_student
def thankyou():
    return render_template("thankyou.html",
                           student_name=session.get("student_name", "Student"))


# ── RESULTS ────────────────────────────────────────────────────────────
@app.route("/results")
def results():
    settings = db.get_election_settings()

    if not settings:
        return render_template("results.html",
                               available=False,
                               message="Election settings not configured.")

    # Results only visible once the admin explicitly publishes them
    if not settings.get("results_published"):
        result_date = settings.get("result_date")
        if result_date:
            try:
                rd = datetime.date.fromisoformat(str(result_date)[:10])
                msg = f"Results will be announced on {rd.strftime('%B %d, %Y')}."
            except Exception:
                msg = "Results have not been published yet. Please check back later."
        else:
            msg = "Results have not been published yet. Please check back later."
        return render_template("results.html", available=False, message=msg)

    candidates = db.get_all_candidates()
    by_position: dict = {}
    for c in candidates:
        by_position.setdefault(c["position"], []).append(c)

    for pos in by_position:
        by_position[pos].sort(key=lambda x: x.get("vote_count") or 0, reverse=True)
        if by_position[pos]:
            by_position[pos][0]["is_winner"] = True

    return render_template("results.html",
                           available=True,
                           results_by_position=by_position)


# ── LOGOUT ─────────────────────────────────────────────────────────────
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


# ══════════════════════════ ADMIN ROUTES ═══════════════════════════════

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        admin = db.get_admin_by_username(username)
        if admin and bcrypt.checkpw(password.encode(), admin["password_hash"].encode()):
            session["admin_logged_in"] = True
            session["admin_username"]  = username
            return redirect(url_for("admin_dashboard"))

        flash("Invalid username or password.", "error")

    return render_template("admin/login.html")


@app.route("/admin/dashboard")
@_require_admin
def admin_dashboard():
    total_students = db.get_total_students()
    voted_count    = db.get_voted_count()
    pending_count  = db.get_pending_count()
    turnout        = round(voted_count / total_students * 100, 1) if total_students else 0
    settings       = db.get_election_settings()
    candidates     = db.get_all_candidates()
    return render_template("admin/dashboard.html",
                           total_students=total_students,
                           voted_count=voted_count,
                           pending_count=pending_count,
                           turnout=turnout,
                           settings=settings,
                           candidates=candidates,
                           election_active=_compute_election_active(settings))


# ── STUDENTS CRUD ──────────────────────────────────────────────────────
@app.route("/admin/students")
@_require_admin
def admin_students():
    students = db.get_all_students()
    now_ay   = _get_academic_year()
    for s in students:
        s["eligible"] = is_eligible_to_vote(s)
    return render_template("admin/students.html",
                           students=students,
                           current_year=datetime.datetime.now().year,
                           current_academic_year=now_ay)


@app.route("/admin/students/add", methods=["POST"])
@_require_admin
def admin_add_student():
    roll_number    = request.form.get("roll_number", "").strip()
    name           = request.form.get("name", "").strip()
    email          = request.form.get("email", "").strip().lower()
    department     = request.form.get("department", "").strip()
    year           = request.form.get("year", "1")
    admission_year = request.form.get("admission_year", "").strip()
    entry_year     = request.form.get("entry_year", "1")
    photo          = request.files.get("photo")

    photo_data = None
    if photo and photo.filename:
        photo_data = base64.b64encode(photo.read()).decode("utf-8")

    errors = validate_student_form({
        "roll_number":    roll_number,
        "name":           name,
        "email":          email,
        "department":     department,
        "admission_year": admission_year,
        "entry_year":     entry_year,
        "year":           year,
    }, require_roll=True)

    if photo and photo.filename:
        if not valid_image_extension(photo.filename):
            errors.append("Photo must be JPG, PNG, or WEBP.")
        elif not valid_file_size(photo, 5):
            errors.append("Photo must be smaller than 5 MB.")

    if errors:
        for e in errors:
            flash(e, "error")
        return redirect(url_for("admin_students"))

    student_data = {
        "roll_number":    roll_number,
        "name":           name,
        "email":          email.lower(),
        "department":     department,
        "year":           int(year) if year else 1,
        "admission_year": int(admission_year) if admission_year else datetime.datetime.now().year,
        "entry_year":     int(entry_year) if entry_year else 1,
        "photo_base64":   photo_data,
        "has_voted":      False,
        "is_approved":    True,
    }

    try:
        db.add_student(student_data)
        flash("Student added and approved successfully.", "success")
    except Exception as exc:
        flash(f"Error: {exc}", "error")

    return redirect(url_for("admin_students"))


@app.route("/admin/students/approve/<student_id>", methods=["POST"])
@_require_admin
def admin_approve_student(student_id):
    db.approve_student(student_id)
    flash("Student approved. They can now log in.", "success")
    return redirect(url_for("admin_students"))


@app.route("/admin/students/reject/<student_id>", methods=["POST"])
@_require_admin
def admin_reject_student(student_id):
    db.reject_student(student_id)
    flash("Student registration rejected and removed.", "info")
    return redirect(url_for("admin_students"))


@app.route("/admin/students/edit", methods=["POST"])
@_require_admin
def admin_edit_student():
    student_id     = request.form.get("student_id")
    name           = request.form.get("name", "").strip()
    email          = request.form.get("email", "").strip().lower()
    department     = request.form.get("department", "").strip()
    year           = request.form.get("year", "1")
    admission_year = request.form.get("admission_year", "").strip()
    entry_year     = request.form.get("entry_year", "1")
    photo          = request.files.get("photo")

    update_data = {
        "name":           name,
        "email":          email,
        "department":     department,
        "year":           int(year) if year else 1,
        "admission_year": int(admission_year) if admission_year else None,
        "entry_year":     int(entry_year) if entry_year else 1,
    }

    if photo and photo.filename:
        update_data["photo_base64"] = base64.b64encode(photo.read()).decode("utf-8")

    try:
        db.update_student(student_id, update_data)
        flash("Student updated successfully.", "success")
    except Exception as exc:
        flash(f"Error: {exc}", "error")

    return redirect(url_for("admin_students"))


@app.route("/admin/students/delete", methods=["POST"])
@_require_admin
def admin_delete_student():
    student_id = request.form.get("student_id")
    try:
        db.delete_student(student_id)
        flash("Student deleted.", "success")
    except Exception as exc:
        flash(f"Error: {exc}", "error")
    return redirect(url_for("admin_students"))


# ── CANDIDATES CRUD ────────────────────────────────────────────────────
@app.route("/admin/candidates")
@_require_admin
def admin_candidates():
    candidates          = db.get_all_candidates()
    approved_students   = db.get_approved_students()
    # Group candidates by position in canonical order
    raw_by_pos = {}
    for c in candidates:
        raw_by_pos.setdefault(c["position"], []).append(c)
    candidates_by_position = {p: raw_by_pos[p] for p in POSITIONS_ORDER if p in raw_by_pos}
    for p, cs in raw_by_pos.items():        # any extra positions
        if p not in candidates_by_position:
            candidates_by_position[p] = cs
    return render_template("admin/candidates.html",
                           candidates=candidates,
                           candidates_by_position=candidates_by_position,
                           students=approved_students)


@app.route("/admin/candidates/add", methods=["POST"])
@_require_admin
def admin_add_candidate():
    student_id  = request.form.get("student_id", "").strip()
    name        = request.form.get("name", "").strip()
    roll_number = request.form.get("roll_number", "").strip()
    department  = request.form.get("department", "").strip()
    position    = request.form.get("position", "").strip()
    manifesto   = request.form.get("manifesto", "").strip()
    photo       = request.files.get("photo")

    photo_data = None

    # If admin selected an existing student, auto-fill from their record
    if student_id:
        stu = db.get_student_by_id(student_id)
        if stu:
            if not name:        name        = stu["name"]
            if not roll_number: roll_number = stu["roll_number"]
            if not department:  department  = stu.get("department", "")
            if not photo or not photo.filename:
                photo_data = stu.get("photo_base64")

    if photo and photo.filename:
        photo_data = base64.b64encode(photo.read()).decode("utf-8")

    candidate_data = {
        "name":        name,
        "roll_number": roll_number,
        "department":  department,
        "position":    position,
        "manifesto":   manifesto,
        "photo_base64": photo_data,
        "vote_count":  0,
    }

# Block if no student was selected from the dropdown
    if not student_id:
        flash("Please select a registered student from the list.", "error")
        return redirect(url_for("admin_candidates"))

    # Block if same student is already a candidate for same position
    if roll_number:
        existing = db.get_candidate_by_student_and_position(roll_number, position)
        if existing:
            flash(f"This student is already registered as a candidate for {position}.", "error")
            return redirect(url_for("admin_candidates"))

    try:
        db.add_candidate(candidate_data)
        flash("Candidate added successfully.", "success")
    except Exception as exc:
        flash(f"Error: {exc}", "error")

    return redirect(url_for("admin_candidates"))


@app.route("/admin/candidates/edit", methods=["POST"])
@_require_admin
def admin_edit_candidate():
    candidate_id = request.form.get("candidate_id")
    name         = request.form.get("name", "").strip()
    roll_number  = request.form.get("roll_number", "").strip()
    department   = request.form.get("department", "").strip()
    position     = request.form.get("position", "").strip()
    manifesto    = request.form.get("manifesto", "").strip()
    photo        = request.files.get("photo")

    update_data = {
        "name":        name,
        "roll_number": roll_number,
        "department":  department,
        "position":    position,
        "manifesto":   manifesto,
    }

    if photo and photo.filename:
        update_data["photo_base64"] = base64.b64encode(photo.read()).decode("utf-8")

    try:
        db.update_candidate(candidate_id, update_data)
        flash("Candidate updated.", "success")
    except Exception as exc:
        flash(f"Error: {exc}", "error")

    return redirect(url_for("admin_candidates"))


@app.route("/admin/candidates/delete", methods=["POST"])
@_require_admin
def admin_delete_candidate():
    candidate_id = request.form.get("candidate_id")
    try:
        db.delete_candidate(candidate_id)
        flash("Candidate deleted.", "success")
    except Exception as exc:
        flash(f"Error: {exc}", "error")
    return redirect(url_for("admin_candidates"))


# ── SETTINGS ───────────────────────────────────────────────────────────
@app.route("/admin/settings", methods=["GET", "POST"])
@_require_admin
def admin_settings():
    if request.method == "POST":
        # datetime-local inputs give "YYYY-MM-DDTHH:MM" — store as-is (ISO string)
        start_raw  = request.form.get("start_date") or None
        end_raw    = request.form.get("end_date") or None
        result_raw = request.form.get("result_date") or None

        errs = validate_settings_form({
            "start_date":  start_raw,
            "end_date":    end_raw,
            "result_date": result_raw,
        })
        if errs:
            for e in errs:
                flash(e, "error")
            return redirect(url_for("admin_settings"))

        settings_data = {
            "start_date":        start_raw,
            "end_date":          end_raw,
            "result_date":       result_raw,
            "is_active":         "is_active" in request.form,
            # Saving new dates resets the published flag so admin must re-publish
            "results_published": False,
        }
        try:
            db.update_election_settings(settings_data)
            flash("Election settings saved. ⚠️ Results have been unpublished — please republish after the election ends.", "success")
        except Exception as exc:
            flash(f"Error: {exc}", "error")
        return redirect(url_for("admin_settings"))

    settings = db.get_election_settings()

    # Compute whether the election has ended so we show the Publish button
    election_ended = False
    now = datetime.datetime.now()
    if settings:
        end_dt = _parse_election_dt(settings.get("end_date"))
        if end_dt and now > end_dt:
            election_ended = True

    return render_template("admin/settings.html",
                           settings=settings,
                           election_active=_compute_election_active(settings),
                           election_ended=election_ended)

# ______Reset votes__________
@app.route("/admin/reset-votes", methods=["POST"])
@_require_admin
def admin_reset_votes():

    settings = db.get_election_settings()

    from datetime import datetime

    end_date = settings.get("end_date")

    if end_date:
        if isinstance(end_date, str):
            end_date = datetime.strptime(
                end_date[:10],
                "%Y-%m-%d"
            ).date()

        if datetime.now().date() <= end_date:
            flash(
                "Votes can only be reset after election end date.",
                "danger"
            )
            return redirect(url_for("admin_settings"))

    db.reset_all_votes()

    flash(
        "All votes have been reset successfully.",
        "success"
    )

    return redirect(url_for("admin_settings"))

#__________clear candidates__________
@app.route("/admin/clear-candidates", methods=["POST"])
@_require_admin
def admin_clear_candidates():

    settings = db.get_election_settings()

    from datetime import datetime

    end_date = settings.get("end_date")

    if end_date:
        if isinstance(end_date, str):
            end_date = datetime.strptime(
                end_date[:10],
                "%Y-%m-%d"
            ).date()

        if datetime.now().date() <= end_date:
            flash(
                "Candidates can only be cleared after election end date.",
                "danger"
            )
            return redirect(url_for("admin_settings"))

    db.clear_all_candidates()

    flash(
        "All candidates removed successfully.",
        "success"
    )

    return redirect(url_for("admin_settings"))

# ── PUBLISH RESULTS ────────────────────────────────────────────────────
@app.route("/admin/publish-results", methods=["POST"])
@_require_admin
def admin_publish_results():
    """Admin publishes or unpublishes results."""
    unpublish = request.form.get("unpublish") == "1"
    try:
        db.update_election_settings({"results_published": not unpublish})
        if unpublish:
            flash("🔒 Results unpublished. Students can no longer see them.", "info")
        else:
            flash("✅ Results published! Students can now view the election results.", "success")
    except Exception as exc:
        flash(f"Error: {exc}", "error")
    return redirect(url_for("admin_settings"))


# ── MONITOR ────────────────────────────────────────────────────────────
@app.route("/admin/monitor")
@_require_admin
def admin_monitor():
    students    = db.get_approved_students()
    voted_count = sum(1 for s in students if s.get("has_voted"))
    total       = len(students)
    return render_template("admin/monitor.html",
                           students=students,
                           voted_count=voted_count,
                           total=total)


# ── ADMIN LOGOUT ───────────────────────────────────────────────────────
@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    session.pop("admin_username", None)
    flash("Admin logged out.", "info")
    return redirect(url_for("admin_login"))


# ══════════════════════════ ENTRY POINT ════════════════════════════════

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
