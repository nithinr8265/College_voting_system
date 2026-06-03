"""
validators.py — Server-side validation helpers for SWC Election Platform.
Used in app.py to validate all form inputs before DB operations.
"""

import re
import datetime
from typing import Optional


# ── Field validators ────────────────────────────────────────────────

def is_empty(value: Optional[str]) -> bool:
    return not value or value.strip() == ""


def valid_roll_number(value: str) -> bool:
    """3–20 alphanumeric characters, no spaces or special characters."""
    if not value or not value.strip():
        return False
    return bool(re.match(r"^[A-Za-z0-9]{3,20}$", value.strip()))


# Maps each department to the prefix(es) the roll number must start with (uppercase)
DEPT_PREFIX_MAP = {
    "BCA":                      ["BCA"],
    "BSC":                      ["BSC"],
    "BCOM":                     ["BCOM"],
    "BA":                       ["BA"],
    "COMPUTER SCIENCE":         ["CS"],
    "INFORMATION TECHNOLOGY":   ["IT"],
    "ELECTRONICS & COMMUNICATION": ["EC"],
    "ELECTRICAL ENGINEERING":   ["EE"],
    "MECHANICAL ENGINEERING":   ["ME"],
    "CIVIL ENGINEERING":        ["CE"],
    "CHEMICAL ENGINEERING":     ["CHE"],
    "BIOTECHNOLOGY":            ["BT"],
    "PHYSICS":                  ["PHY"],
    "MATHEMATICS":              ["MAT"],
    "MA":                       ["MA"],
    "MSC":                      ["MSC"],
    "MBA":                      ["MBA"],
    "MCA":                      ["MCA"],
    "M.TECH":                   ["MTECH"],
    "ME":                       ["MEE"],
}


def valid_roll_for_dept(roll: str, dept: str) -> tuple[bool, str]:
    """
    Check roll number prefix matches department.
    Returns (ok, expected_prefix_hint).
    """
    if not roll or not dept:
        return True, ""
    key = dept.strip().upper()
    prefixes = DEPT_PREFIX_MAP.get(key)
    if not prefixes:
        return True, ""          # unknown dept — skip prefix check
    roll_upper = roll.strip().upper()
    for p in prefixes:
        if roll_upper.startswith(p):
            return True, ""
    hint = "/".join(prefixes)
    return False, hint


def valid_name(value: str) -> bool:
    """2–80 chars, letters/spaces/hyphens/apostrophes only."""
    v = value.strip()
    return 2 <= len(v) <= 80 and bool(re.match(r"^[A-Za-z\s'\-]+$", v))


def valid_email(value: str) -> bool:
    """Basic RFC-style email check."""
    return bool(re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$", value.strip()))


def valid_year(value, min_year: int = 2000) -> bool:
    """Must be a 4-digit year between min_year and next calendar year."""
    try:
        y = int(value)
        return min_year <= y <= datetime.datetime.now().year + 1
    except (ValueError, TypeError):
        return False


def valid_entry_year(value) -> bool:
    """Entry year must be 1, 2, or 3."""
    try:
        return int(value) in (1, 2, 3)
    except (ValueError, TypeError):
        return False


def valid_study_year(value) -> bool:
    """Current study year must be 1–4."""
    try:
        return int(value) in (1, 2, 3, 4)
    except (ValueError, TypeError):
        return False


def valid_otp(value: str) -> bool:
    """OTP must be exactly 6 digits."""
    return bool(re.match(r"^\d{6}$", value.strip()))


def valid_position(value: str) -> bool:
    allowed = {
        "President", "Vice President", "Secretary",
        "Treasurer", "Sports Secretary", "Cultural Secretary",
    }
    return value.strip() in allowed


def valid_image_extension(filename: str) -> bool:
    allowed = {".jpg", ".jpeg", ".png", ".webp"}
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in allowed


def valid_file_size(file_storage, max_mb: float = 5.0) -> bool:
    """Check uploaded file size without seeking (reads into memory check)."""
    try:
        file_storage.stream.seek(0, 2)          # seek to end
        size = file_storage.stream.tell()
        file_storage.stream.seek(0)              # rewind
        return size <= max_mb * 1024 * 1024
    except Exception:
        return True   # allow if cannot check


# ── Aggregate form validators ────────────────────────────────────────

def validate_student_form(form_data: dict, require_roll: bool = True) -> list[str]:
    """
    Validate student add/edit form fields.
    Returns a list of error strings (empty = valid).
    """
    errors = []

    roll  = form_data.get("roll_number", "")
    name  = form_data.get("name", "")
    email = form_data.get("email", "")
    dept  = form_data.get("department", "")
    adm_yr= form_data.get("admission_year", "")
    ent_yr= form_data.get("entry_year", "")
    yr    = form_data.get("year", "")

    if require_roll:
        if is_empty(roll):
            errors.append("Roll number is required.")
        elif not valid_roll_number(roll):
            errors.append("Roll number must be 3–20 alphanumeric characters.")
        else:
            ok, hint = valid_roll_for_dept(roll, dept)
            if not ok:
                errors.append(
                    f"Roll number for {dept} must start with '{hint}' "
                    f"(e.g. {hint}001). Got: '{roll}'."
                )

    if is_empty(name):
        errors.append("Full name is required.")
    elif not valid_name(name):
        errors.append("Name must be 2–80 characters (letters, spaces, hyphens, apostrophes only).")

    if is_empty(email):
        errors.append("Email address is required.")
    elif not valid_email(email):
        errors.append("Please enter a valid email address.")

    if is_empty(dept):
        errors.append("Department is required.")

    if is_empty(str(adm_yr)):
        errors.append("Admission year is required.")
    elif not valid_year(adm_yr):
        errors.append("Please enter a valid admission year (2000 – present).")

    if not is_empty(str(ent_yr)) and not valid_entry_year(ent_yr):
        errors.append("Entry year must be 1 (normal), 2 (lateral 2nd yr), or 3 (lateral 3rd yr).")

    if not is_empty(str(yr)) and not valid_study_year(yr):
        errors.append("Current year of study must be 1–4.")

    return errors


def validate_candidate_form(form_data: dict) -> list[str]:
    """Validate candidate add/edit form. Returns list of error strings."""
    errors = []

    name     = form_data.get("name", "")
    position = form_data.get("position", "")
    manifesto= form_data.get("manifesto", "")

    if is_empty(name):
        errors.append("Candidate name is required.")
    elif not valid_name(name):
        errors.append("Name must be 2–80 characters (letters only).")

    if is_empty(position):
        errors.append("Position is required.")
    elif not valid_position(position):
        errors.append(f"'{position}' is not a valid position.")

    if manifesto and len(manifesto) > 1000:
        errors.append("Manifesto must not exceed 1000 characters.")

    return errors


def validate_settings_form(form_data: dict) -> list[str]:
    """Validate election settings dates/datetimes."""
    errors = []

    start  = form_data.get("start_date")
    end    = form_data.get("end_date")
    result = form_data.get("result_date")

    def parse_dt(d):
        """Parse YYYY-MM-DDTHH:MM, YYYY-MM-DDTHH:MM:SS, or YYYY-MM-DD."""
        if not d:
            return None
        s = str(d).strip()
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
            try:
                return datetime.datetime.strptime(s[:len(fmt)], fmt)
            except ValueError:
                pass
        return None

    def parse_date(d):
        try:
            return datetime.date.fromisoformat(str(d)[:10]) if d else None
        except ValueError:
            return None

    sd = parse_dt(start)
    ed = parse_dt(end)
    rd = parse_dt(result)

    if sd and ed and ed <= sd:
        errors.append("Election end date/time must be after the start date/time.")

    if ed and rd:
        if rd <= ed:
            errors.append(
                "Result announcement date/time must be after the election end date/time. "
                "For example, if voting ends at 4:00 PM, results can be announced at 6:00 PM on the same day."
            )

    return errors
