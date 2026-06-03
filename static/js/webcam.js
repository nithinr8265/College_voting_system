/**
 * webcam.js — Webcam capture + face verification for SWC Election Platform
 * Handles camera access, live preview, snapshot, and /verify-face API call.
 */

(function () {
  "use strict";

  /* ── DOM REFS ──────────────────────────────────────────────────── */
  const video        = document.getElementById("video");
  const canvas       = document.getElementById("canvas");
  const captureBtn   = document.getElementById("captureBtn");
  const captureBtnTxt= document.getElementById("captureBtnText");
  const captureSpinner = document.getElementById("captureSpinner");
  const statusBox    = document.getElementById("statusBox");
  const camError     = document.getElementById("camError");
  const camErrorMsg  = document.getElementById("camErrorMsg");
  const webcamWrapper= document.getElementById("webcamWrapper");

  let stream         = null;
  let attempts       = 0;
  const MAX_ATTEMPTS = 5;

  /* ── INIT CAMERA ───────────────────────────────────────────────── */
  async function initCamera() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      showCamError("Your browser does not support camera access. Please use Chrome or Firefox.");
      return;
    }

    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width:       { ideal: 640 },
          height:      { ideal: 480 },
          facingMode:  "user",       // front camera on mobile
        },
        audio: false,
      });

      video.srcObject = stream;
      await video.play();

      // Enable capture button once stream is live
      captureBtn.disabled = false;
      showStatus("", "");  // clear any placeholder

    } catch (err) {
      console.error("[webcam] Camera error:", err.name, err.message);

      if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
        showCamError(
          "Camera permission denied. Please allow camera access in your browser settings and reload the page."
        );
      } else if (err.name === "NotFoundError" || err.name === "DevicesNotFoundError") {
        showCamError(
          "No camera found on this device. Please connect a webcam and reload."
        );
      } else if (err.name === "NotReadableError" || err.name === "TrackStartError") {
        showCamError(
          "Camera is in use by another application. Please close it and reload."
        );
      } else {
        showCamError(`Camera error: ${err.message}. Please reload and try again.`);
      }
    }
  }

  /* ── CAPTURE & VERIFY ──────────────────────────────────────────── */
  async function captureAndVerify() {
    if (!stream) {
      showStatus("Camera not active. Please reload the page.", "error");
      return;
    }

    attempts++;

    // Draw current video frame onto canvas
    canvas.width  = video.videoWidth  || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Convert to base64 JPEG (quality 0.85)
    const base64Image = canvas.toDataURL("image/jpeg", 0.85);

    // Show loading state
    setLoading(true);
    showStatus("🔍 Verifying your face, please wait…", "");

    try {
      const response = await fetch("/verify-face", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ image: base64Image }),
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const data = await response.json();

      if (data.match === true) {
        // ✅ Face matched
        showStatus("✅ Face verified successfully! Redirecting to ballot…", "success");
        stopCamera();

        // Brief delay so user sees success message
        setTimeout(() => {
          window.location.href = "/ballot";
        }, 1200);

      } else {
        // ❌ Face did not match
        const remaining = MAX_ATTEMPTS - attempts;

        if (remaining <= 0) {
          showStatus(
            "❌ Face verification failed after multiple attempts. Please contact the admin.",
            "error"
          );
          captureBtn.disabled = true;
          stopCamera();
        } else {
          const reason = data.error
            ? `Reason: ${data.error}`
            : "Make sure you are in good light and looking directly at the camera.";

          showStatus(
            `❌ Face not matched. ${reason} — ${remaining} attempt${remaining > 1 ? "s" : ""} remaining.`,
            "error"
          );
          setLoading(false);
        }
      }

    } catch (err) {
      console.error("[webcam] Verification error:", err);
      showStatus(
        `⚠️ Network error during verification: ${err.message}. Please try again.`,
        "error"
      );
      setLoading(false);
    }
  }

  /* ── HELPERS ───────────────────────────────────────────────────── */
  function showCamError(msg) {
    if (webcamWrapper) webcamWrapper.style.display = "none";
    if (camError)      camError.style.display      = "block";
    if (camErrorMsg)   camErrorMsg.textContent      = msg;
    if (captureBtn)    captureBtn.disabled          = true;
  }

  function showStatus(msg, type) {
    if (!statusBox) return;
    statusBox.style.display = msg ? "block" : "none";
    statusBox.textContent   = msg;
    statusBox.className     = "verify-status";
    if (type === "success") statusBox.classList.add("success");
    if (type === "error")   statusBox.classList.add("error");
  }

  function setLoading(loading) {
    if (!captureBtn || !captureBtnTxt || !captureSpinner) return;
    captureBtn.disabled          = loading;
    captureBtnTxt.style.display  = loading ? "none"   : "inline";
    captureSpinner.style.display = loading ? "inline-block" : "none";
  }

  function stopCamera() {
    if (stream) {
      stream.getTracks().forEach(t => t.stop());
      stream = null;
    }
  }

  /* ── EVENT LISTENERS ───────────────────────────────────────────── */
  if (captureBtn) {
    captureBtn.addEventListener("click", captureAndVerify);
  }

  // Stop camera when user leaves the page
  window.addEventListener("beforeunload", stopCamera);
  window.addEventListener("pagehide",     stopCamera);

  /* ── BOOT ──────────────────────────────────────────────────────── */
  // Start camera as soon as DOM is ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initCamera);
  } else {
    initCamera();
  }

})();
