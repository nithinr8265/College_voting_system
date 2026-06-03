"""
db.py — All Supabase database operations for the College Voting System
"""
from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

_url: str = os.environ.get("SUPABASE_URL", "")
_key: str = os.environ.get("SUPABASE_KEY", "")
supabase: Client = create_client(_url, _key)


# ─────────────────────────── STUDENT QUERIES ───────────────────────────

def get_student_by_roll_and_email(roll_number: str, email: str):
    res = (supabase.table("students")
           .select("*")
           .eq("roll_number", roll_number)
           .eq("email", email)
           .execute())
    return res.data[0] if res.data else None


def get_student_by_roll(roll_number: str):
    res = (supabase.table("students")
           .select("*")
           .eq("roll_number", roll_number)
           .execute())
    return res.data[0] if res.data else None


def get_student_by_email(email: str):
    res = (supabase.table("students")
           .select("*")
           .eq("email", email)
           .execute())
    return res.data[0] if res.data else None


def get_student_by_id(student_id: str):
    res = (supabase.table("students")
           .select("*")
           .eq("id", student_id)
           .execute())
    return res.data[0] if res.data else None


def get_all_students():
    res = (supabase.table("students")
           .select("*")
           .order("created_at", desc=True)
           .execute())
    return res.data or []


def get_approved_students():
    res = (supabase.table("students")
           .select("*")
           .eq("is_approved", True)
           .order("name")
           .execute())
    return res.data or []


def get_pending_students():
    res = (supabase.table("students")
           .select("*")
           .eq("is_approved", False)
           .order("created_at", desc=True)
           .execute())
    return res.data or []


def add_student(data: dict):
    res = supabase.table("students").insert(data).execute()
    return res.data


def update_student(student_id: str, data: dict):
    res = (supabase.table("students")
           .update(data)
           .eq("id", student_id)
           .execute())
    return res.data


def delete_student(student_id: str):
    # First delete related votes
    supabase.table("votes").delete().eq("student_id", student_id).execute()
    res = supabase.table("students").delete().eq("id", student_id).execute()
    return res.data


def set_student_voted(roll_number: str, voted_at: str):
    res = (supabase.table("students")
           .update({"has_voted": True, "voted_at": voted_at})
           .eq("roll_number", roll_number)
           .execute())
    return res.data


def reset_all_votes():
    

    supabase.table("votes")\
        .delete()\
        .not_.is_("id", "null")\
        .execute()

    supabase.table("students")\
        .update({
            "has_voted": False,
            "voted_at": None
        })\
        .not_.is_("id", "null")\
        .execute()

    supabase.table("candidates")\
        .update({
            "vote_count": 0
        })\
        .not_.is_("id", "null")\
        .execute()


def approve_student(student_id: str):
    res = (supabase.table("students")
           .update({"is_approved": True})
           .eq("id", student_id)
           .execute())
    return res.data


def reject_student(student_id: str):
    res = supabase.table("students").delete().eq("id", student_id).execute()
    return res.data


def get_total_students() -> int:
    res = (supabase.table("students")
           .select("id", count="exact")
           .eq("is_approved", True)
           .execute())
    return res.count or 0


def get_voted_count() -> int:
    res = (supabase.table("students")
           .select("id", count="exact")
           .eq("has_voted", True)
           .eq("is_approved", True)
           .execute())
    return res.count or 0


def get_pending_count() -> int:
    res = (supabase.table("students")
           .select("id", count="exact")
           .eq("is_approved", False)
           .execute())
    return res.count or 0


# ─────────────────────────── CANDIDATE QUERIES ─────────────────────────

def get_all_candidates():
    res = supabase.table("candidates").select("*").order("position").execute()
    return res.data or []


def get_candidates_by_position() -> dict:
    candidates = get_all_candidates()
    grouped: dict = {}
    for c in candidates:
        pos = c.get("position", "Unknown")
        grouped.setdefault(pos, []).append(c)
    return grouped


def get_candidate_by_id(candidate_id: str):
    res = (supabase.table("candidates")
           .select("*")
           .eq("id", candidate_id)
           .execute())
    return res.data[0] if res.data else None


def add_candidate(data: dict):
    res = supabase.table("candidates").insert(data).execute()
    return res.data

def get_candidate_by_student_and_position(roll_number: str, position: str):
    res = (supabase.table("candidates")
           .select("id, name, position")
           .eq("roll_number", roll_number)
           .eq("position", position)
           .execute())
    return res.data[0] if res.data else None    


def update_candidate(candidate_id: str, data: dict):
    res = (supabase.table("candidates")
           .update(data)
           .eq("id", candidate_id)
           .execute())
    return res.data


def delete_candidate(candidate_id: str):
    supabase.table("votes").delete().eq("candidate_id", candidate_id).execute()
    res = supabase.table("candidates").delete().eq("id", candidate_id).execute()
    return res.data


def increment_vote_count(candidate_id: str):
    res = (supabase.table("candidates")
           .select("vote_count")
           .eq("id", candidate_id)
           .execute())
    if res.data:
        current = res.data[0].get("vote_count") or 0
        supabase.table("candidates").update(
            {"vote_count": current + 1}
        ).eq("id", candidate_id).execute()


# ─────────────────────────── VOTE QUERIES ──────────────────────────────

def insert_vote(student_id: str, candidate_id: str, position: str):
    data = {
        "student_id": student_id,
        "candidate_id": candidate_id,
        "position": position,
    }
    res = supabase.table("votes").insert(data).execute()
    return res.data


# ─────────────────────────── ELECTION SETTINGS ─────────────────────────

def get_election_settings():
    res = (supabase.table("election_settings")
           .select("*")
           .eq("id", 1)
           .execute())
    return res.data[0] if res.data else None


def update_election_settings(data: dict):
    res = (supabase.table("election_settings")
           .update(data)
           .eq("id", 1)
           .execute())
    return res.data


# ─────────────────────────── ADMIN QUERIES ─────────────────────────────

def get_admin_by_username(username: str):
    res = (supabase.table("admins")
           .select("*")
           .eq("username", username)
           .execute())
    return res.data[0] if res.data else None

#____________________clear candidates____________________
def clear_all_candidates():

    # Delete votes first
    supabase.table("votes")\
        .delete()\
        .not_.is_("id", "null")\
        .execute()

    # Delete candidates
    supabase.table("candidates")\
        .delete()\
        .not_.is_("id", "null")\
        .execute()