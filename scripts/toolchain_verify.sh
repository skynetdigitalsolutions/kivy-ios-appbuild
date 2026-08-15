#!/bin/bash
# toolchain_verify.sh — Single-gate kivy-ios toolchain verification.
#
# Replaces the four cascading rebuild steps in the original workflow.
# Runs ONE check; rebuilds ONCE if anything is wrong; then sets
# TOOLCHAIN_OK=true in GITHUB_ENV so subsequent steps can gate on it.
#
# Exit codes:
#   0 — toolchain is valid (or was successfully rebuilt)
#   1 — toolchain could not be built after a full retry

set -euo pipefail

echo "========================================"
echo "  Toolchain Verification (single gate)  "
echo "========================================"

# ── Helper: returns "ok" if the toolchain is fully functional ─────────────────
_check_toolchain() {
  # 1. dist/python3 and dist/kivy directories must exist
  [[ -d "dist/python3" ]] || { echo "  ✗ dist/python3 missing"; return 1; }
  [[ -d "dist/kivy"   ]] || { echo "  ✗ dist/kivy missing";    return 1; }

  # 2. dist/ must not be empty
  [[ -n "$(ls -A dist/)" ]] || { echo "  ✗ dist/ is empty"; return 1; }

  # 3. hostpython3 pip binary must exist
  if [[ -d "dist/hostpython3" ]]; then
    if [[ ! -f "dist/hostpython3/bin/pip3" && ! -f "dist/hostpython3/bin/pip" ]]; then
      echo "  ✗ hostpython3 pip binary missing"
      return 1
    fi
  fi

  # 4. toolchain pip must be callable
  if ! toolchain pip --version &>/dev/null; then
    echo "  ✗ toolchain pip not functional"
    return 1
  fi

  echo "  ✓ All checks passed"
  return 0
}

# ── Helper: full clean rebuild ────────────────────────────────────────────────
_rebuild() {
  echo ">>> Cleaning stale artifacts…"
  rm -rf dist/ build/ ~/.cache/kivy-ios

  echo ">>> Building toolchain (hostpython3 + python3 + kivy + ffmpeg)…"
  # Try with ffmpeg first; fall back without it if ffmpeg recipe fails
  toolchain build hostpython3 python3 kivy ffmpeg \
    || toolchain build hostpython3 python3 kivy
}

# ── Main logic ────────────────────────────────────────────────────────────────
if _check_toolchain; then
  echo ""
  echo "Toolchain is healthy — skipping rebuild."
else
  echo ""
  echo "Toolchain check failed — rebuilding from source…"
  _rebuild

  echo ""
  echo "Re-verifying after rebuild…"
  if ! _check_toolchain; then
    echo ""
    echo "ERROR: Toolchain is still invalid after a full rebuild."
    echo "--- toolchain recipes output ---"
    toolchain recipes || true
    echo "--- dist/ contents ---"
    ls -la dist/ || true
    exit 1
  fi
fi

echo ""
echo "TOOLCHAIN_OK=true" >> "$GITHUB_ENV"
echo "========================================"
echo "  Toolchain verification complete ✓     "
echo "========================================"
