#!/usr/bin/env bash
# =============================================================
# EECE 5554 - PA0 environment verification
#
# Usage:   ./verify_pa0.sh <your-northeastern-username>
# Example: ./verify_pa0.sh li.xi
#
# This script collects proof that your Ubuntu 24.04 environment
# is installed and working, and writes it to <username>.txt
# Commit that file to EECE5554/PA0/ in your private repository.
# =============================================================

set -u

NUUSER="${1:-}"
if [ -z "$NUUSER" ]; then
    echo "Usage: ./verify_pa0.sh <your-northeastern-username>"
    echo "Example: ./verify_pa0.sh li.xi"
    exit 1
fi

OUT="${NUUSER}.txt"
: > "$OUT"

log() { echo "$@" | tee -a "$OUT"; }
section() { log ""; log "=============================================="; log "$1"; log "=============================================="; }

log "EECE 5554 PA0 VERIFICATION REPORT"
log "Northeastern username: ${NUUSER}"
log "Generated: $(date)"
log "Hostname: $(hostname)"

# -------------------------------------------------------------
section "1. OPERATING SYSTEM (must be Ubuntu 24.04)"
if command -v lsb_release >/dev/null 2>&1; then
    lsb_release -a 2>/dev/null | tee -a "$OUT"
else
    log "lsb_release not found, falling back to /etc/os-release"
    cat /etc/os-release | tee -a "$OUT"
fi

section "2. CPU ARCHITECTURE"
log "uname -m  : $(uname -m)"
log "kernel    : $(uname -r)"
log "Expected  : x86_64 on Intel/AMD hardware, aarch64 on Apple Silicon"

section "3. RESOURCES (RAM, CPU cores, free disk)"
log "CPU cores : $(nproc)"
log "--- free -h ---"
free -h | tee -a "$OUT"
log "--- df -h / ---"
df -h / | tee -a "$OUT"
log "Minimum for this course: 4 cores, 8 GB RAM, 40 GB disk with 20 GB free"

section "4. ADMINISTRATOR AND DEVICE GROUPS"
log "user      : $(whoami)"
log "groups    : $(id -nG)"
if id -nG | tr ' ' '\n' | grep -qx "sudo"; then
    log "sudo group: PRESENT"
else
    log "sudo group: MISSING  <-- you will not be able to install software."
    log "            On a VM, reinstall with 'Skip Unattended Installation' checked."
fi
if id -nG | tr ' ' '\n' | grep -qx "dialout"; then
    log "dialout   : PRESENT (required for USB sensors later in this course)"
else
    log "dialout   : MISSING  <-- fix now with:  sudo usermod -aG dialout \$USER"
    log "            Then log out and log back in, and re-run this script."
fi

section "5. NETWORK"
if getent hosts archive.ubuntu.com >/dev/null 2>&1; then
    log "DNS resolution of archive.ubuntu.com: OK"
else
    log "DNS resolution of archive.ubuntu.com: FAILED"
fi
log "--- ping -c 3 archive.ubuntu.com ---"
if command -v ping >/dev/null 2>&1; then
    ping -c 3 -W 3 archive.ubuntu.com 2>&1 | tail -n 3 | tee -a "$OUT"
else
    log "ping not installed (sudo apt install iputils-ping)"
fi
log "(Some campus networks block ping. The curl test below is the reliable one.)"
if command -v curl >/dev/null 2>&1; then
    log "--- curl -sI https://archive.ubuntu.com (first line) ---"
    curl -sI --max-time 10 https://archive.ubuntu.com | head -n 1 | tee -a "$OUT"
else
    log "curl not installed. Install with: sudo apt install curl"
fi

section "6. PACKAGE MANAGER"
log "Run this yourself and confirm it completes without errors:"
log "    sudo apt update && sudo apt upgrade"
log "--- apt-cache policy (first 6 lines) ---"
apt-cache policy 2>/dev/null | head -n 6 | tee -a "$OUT"

section "7. USB (critical for later labs)"
if ! command -v lsusb >/dev/null 2>&1; then
    log "lsusb not found. Install it with: sudo apt install usbutils"
    log "Then re-run this script."
else
    BEFORE=$(lsusb)
    log "--- USB devices BEFORE plugging anything in ---"
    echo "$BEFORE" | tee -a "$OUT"
    echo ""
    echo ">>> Plug in ANY USB device now (flash drive, mouse, phone, keyboard)."
    echo ">>> On a virtual machine you must also attach it to the VM from the"
    echo ">>> Devices > USB menu (VirtualBox) or the USB icon (UTM)."
    read -r -p ">>> Press Enter when the device is attached... " _
    sleep 2
    AFTER=$(lsusb)
    log "--- USB devices AFTER plugging in ---"
    echo "$AFTER" | tee -a "$OUT"
    log "--- Newly detected device(s) ---"
    DIFF=$(comm -13 <(echo "$BEFORE" | sort) <(echo "$AFTER" | sort))
    if [ -z "$DIFF" ]; then
        log "NONE DETECTED. USB passthrough is not working yet."
        log "See Appendix C of the instructions before submitting."
    else
        echo "$DIFF" | tee -a "$OUT"
        log "USB passthrough: OK"
    fi
fi

section "8. GIT"
if command -v git >/dev/null 2>&1; then
    log "$(git --version)"
    log "user.name : $(git config --global user.name 2>/dev/null)"
    log "user.email: $(git config --global user.email 2>/dev/null)"
else
    log "git NOT installed. Install with: sudo apt install git"
fi

# -------------------------------------------------------------
section "9. STUDENT STATEMENT"
cat >> "$OUT" <<'EOS'

Fill in the four items below by editing this file in a text editor.

INSTALL ROUTE (dual-boot / VirtualBox / UTM / other):
    

WHY YOU CHOSE IT (one sentence):
    

ONE RISK OR LIMITATION OF THAT ROUTE (one sentence):
    

STATUS: I confirm that (a) Ubuntu 24.04 is installed and working, and
(b) Git is installed and I am ready to use Git and GitHub.
If anything above failed, describe the exact error message and your plan
to fix it here instead:
    

EOS

echo ""
echo "=============================================="
echo "Done. Report written to: $(pwd)/${OUT}"
echo "Next steps:"
echo "  1. Open ${OUT} and complete Section 9."
echo "  2. Move it into your EECE5554/PA0/ folder."
echo "  3. git add, git commit, git push."
echo "=============================================="
