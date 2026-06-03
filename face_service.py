"""
face_service.py — Face recognition using the face_recognition library (dlib backend).
Compares a live webcam capture against the student's stored photo in the database.
"""
import base64
import io
import face_recognition
from PIL import Image


def _decode_image(b64_string: str):
    """Decode a base64 image string to a face_recognition-compatible numpy array."""
    # Strip data-URL prefix if present (e.g., "data:image/jpeg;base64,...")
    if "," in b64_string:
        b64_string = b64_string.split(",", 1)[1]

    image_bytes = base64.b64decode(b64_string)
    pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # Ensure image is reasonably sized for face detection (max 800px wide)
    max_width = 800
    if pil_image.width > max_width:
        ratio = max_width / pil_image.width
        new_size = (max_width, int(pil_image.height * ratio))
        pil_image = pil_image.resize(new_size, Image.LANCZOS)

    import numpy as np
    return np.array(pil_image)


def verify_face(live_base64: str, stored_base64: str, tolerance: float = 0.55) -> bool:
    """
    Compare a live webcam image against a stored student photo.

    Args:
        live_base64:   Base64 JPEG from the student's webcam (may include data-URL prefix).
        stored_base64: Plain base64 string stored in the DB (no prefix).
        tolerance:     Lower = stricter match. 0.5 is default; 0.55 is slightly lenient.

    Returns:
        True if faces match, False otherwise (including if no face is detected).
    """
    try:
        # ── Live image ─────────────────────────────────────────────────
        live_img = _decode_image(live_base64)
        live_encodings = face_recognition.face_encodings(live_img)

        if not live_encodings:
            print("[face_service] No face detected in live webcam image.")
            return False

        # ── Stored image ───────────────────────────────────────────────
        stored_img = _decode_image(stored_base64)
        stored_encodings = face_recognition.face_encodings(stored_img)

        if not stored_encodings:
            print("[face_service] No face detected in stored student photo.")
            return False

        # ── Compare ────────────────────────────────────────────────────
        results = face_recognition.compare_faces(
            [stored_encodings[0]],
            live_encodings[0],
            tolerance=tolerance,
        )
        distance = face_recognition.face_distance([stored_encodings[0]], live_encodings[0])
        print(f"[face_service] Match: {results[0]}, Distance: {distance[0]:.4f}")

        return bool(results[0])

    except Exception as exc:
        print(f"[face_service] Error during face recognition: {exc}")
        return False
