#!/usr/bin/env bash
# =============================================================
# EECE 5554 - PA1 environment and assignment verification
#
# Usage:   ./verify_pa1.sh <your-northeastern-username> [workspace-path]
# Example: ./verify_pa1.sh li.xi
#          ./verify_pa1.sh li.xi ~/EECE5554/PA1/ros2_ws
#
# Default workspace: $HOME/EECE5554/PA1/ros2_ws
#
# This script checks your ROS 2 Jazzy install, builds your workspace,
# runs your talker and listener, and writes the results to
# <username>_pa1.txt next to your workspace. Commit that file.
#
# It takes about two minutes. Do not run other ROS nodes at the same time.
# =============================================================

set -u

NUUSER="${1:-}"
if [ -z "$NUUSER" ]; then
    echo "Usage: ./verify_pa1.sh <your-northeastern-username> [workspace-path]"
    exit 1
fi

WS="${2:-$HOME/EECE5554/PA1/ros2_ws}"
WS="$(cd "$WS" 2>/dev/null && pwd || echo "$WS")"
PA1_DIR="$(dirname "$WS")"
OUT="${PA1_DIR}/${NUUSER}_pa1.txt"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

: > "$OUT"
log() { echo "$@" | tee -a "$OUT"; }
section() { log ""; log "=============================================="; log "$1"; log "=============================================="; }

# Machine-readable results, printed as a block at the end
declare -A RESULT
mark() { RESULT["$1"]="$2"; }

log "EECE 5554 PA1 VERIFICATION REPORT"
log "Northeastern username: ${NUUSER}"
log "Generated: $(date)"
log "Workspace: ${WS}"

# -------------------------------------------------------------
section "1. OPERATING SYSTEM"
if command -v lsb_release >/dev/null 2>&1; then
    lsb_release -ds 2>/dev/null | tee -a "$OUT"
else
    grep PRETTY_NAME /etc/os-release | tee -a "$OUT"
fi
log "arch: $(uname -m)"
if grep -q "24.04" /etc/os-release 2>/dev/null; then mark os PASS; else mark os FAIL; fi

# -------------------------------------------------------------
section "2. ROS 2 JAZZY INSTALL"
if [ -f /opt/ros/jazzy/setup.bash ]; then
    log "/opt/ros/jazzy/setup.bash: FOUND"
    # shellcheck disable=SC1091
    set +u
    source /opt/ros/jazzy/setup.bash
    set -u
    log "ROS_DISTRO   : ${ROS_DISTRO:-unset}"
    log "ROS_VERSION  : ${ROS_VERSION:-unset}"
    log "AMENT_PREFIX : $(echo "${AMENT_PREFIX_PATH:-unset}" | cut -c1-60)"
    if command -v ros2 >/dev/null 2>&1; then
        log "ros2 CLI     : available"
        log "installed ROS packages: $(ros2 pkg list 2>/dev/null | wc -l)"
        mark ros PASS
    else
        log "ros2 CLI     : NOT FOUND after sourcing"
        mark ros FAIL
    fi
else
    log "/opt/ros/jazzy/setup.bash NOT FOUND."
    log "ROS 2 Jazzy is not installed. See Step 1 of the instructions."
    mark ros FAIL
fi

if grep -qs "source /opt/ros/jazzy/setup.bash" "$HOME/.bashrc"; then
    log ".bashrc sources ROS automatically: YES"
    mark bashrc PASS
else
    log ".bashrc sources ROS automatically: NO"
    log "  Recommended:  echo 'source /opt/ros/jazzy/setup.bash' >> ~/.bashrc"
    mark bashrc FAIL
fi

section "3. BUILD TOOLS"
for tool in colcon rosdep git python3; do
    if command -v "$tool" >/dev/null 2>&1; then
        log "$(printf '%-8s' "$tool"): $("$tool" --version 2>&1 | head -n 1)"
    else
        log "$(printf '%-8s' "$tool"): NOT INSTALLED"
    fi
done
if command -v colcon >/dev/null 2>&1; then mark colcon PASS; else mark colcon FAIL; fi

# -------------------------------------------------------------
section "4. WORKSPACE LAYOUT"
if [ ! -d "$WS/src" ]; then
    log "No src directory at ${WS}/src"
    log "Pass the correct path as the second argument, for example:"
    log "  ./verify_pa1.sh ${NUUSER} ~/EECE5554/PA1/ros2_ws"
    mark workspace FAIL
    PKG=""
else
    log "src contents:"
    ls -1 "$WS/src" | tee -a "$OUT"
    PKG_XML="$(find "$WS/src" -maxdepth 3 -name package.xml | head -n 1)"
    if [ -n "$PKG_XML" ]; then
        PKG="$(basename "$(dirname "$PKG_XML")")"
        log "package found: ${PKG}"
        log "--- package.xml name and dependencies ---"
        grep -E "<(name|depend|exec_depend)>" "$PKG_XML" | sed 's/^[[:space:]]*//' | tee -a "$OUT"
        mark workspace PASS
    else
        log "No package.xml found under src. Create your package first."
        PKG=""
        mark workspace FAIL
    fi
fi

# -------------------------------------------------------------
section "5. COLCON BUILD"
BUILD_OK=0
if [ -n "${PKG}" ] && command -v colcon >/dev/null 2>&1; then
    log "Running: colcon build --symlink-install"
    ( cd "$WS" && colcon build --symlink-install ) > "$TMP/build.log" 2>&1
    BUILD_RC=$?
    tail -n 8 "$TMP/build.log" | tee -a "$OUT"
    if [ $BUILD_RC -eq 0 ]; then
        log "build result: SUCCESS"
        BUILD_OK=1
        mark build PASS
    else
        log "build result: FAILED (exit ${BUILD_RC})"
        log "--- first errors ---"
        grep -iE "error|Traceback|SyntaxError" "$TMP/build.log" | head -n 10 | tee -a "$OUT"
        mark build FAIL
    fi
else
    log "Skipped: no package or colcon not installed."
    mark build FAIL
fi

# -------------------------------------------------------------
section "6. EXECUTABLES REGISTERED"
TALKER=""
LISTENER=""
if [ "$BUILD_OK" -eq 1 ]; then
    # shellcheck disable=SC1091
    set +u
    source "$WS/install/setup.bash" 2>/dev/null
    set -u
    EXES="$(ros2 pkg executables "$PKG" 2>/dev/null)"
    if [ -n "$EXES" ]; then
        echo "$EXES" | tee -a "$OUT"
        TALKER="$(echo "$EXES" | awk '{print $2}' | grep -i -m1 'talk\|pub')"
        LISTENER="$(echo "$EXES" | awk '{print $2}' | grep -i -m1 'listen\|sub')"
        [ -z "$TALKER" ] && TALKER="$(echo "$EXES" | awk 'NR==1{print $2}')"
        [ -z "$LISTENER" ] && LISTENER="$(echo "$EXES" | awk 'NR==2{print $2}')"
        log "talker executable  : ${TALKER:-none}"
        log "listener executable: ${LISTENER:-none}"
        if [ -n "$TALKER" ] && [ -n "$LISTENER" ]; then mark executables PASS; else mark executables FAIL; fi
    else
        log "ros2 pkg executables ${PKG} returned nothing."
        log "Check the console_scripts entry points in setup.py."
        mark executables FAIL
    fi
else
    log "Skipped: build did not succeed."
    mark executables FAIL
fi

# -------------------------------------------------------------
section "7. TALKER AND LISTENER RUN TEST"
PUBLISHED=""
HEARD=""
if [ -n "$TALKER" ] && [ -n "$LISTENER" ]; then
    log "Starting ${PKG} ${TALKER} ..."
    ( ros2 run "$PKG" "$TALKER" > "$TMP/talker.log" 2>&1 ) &
    TPID=$!
    sleep 4

    log "--- ros2 topic list ---"
    ros2 topic list 2>/dev/null | tee -a "$OUT"

    if ros2 topic list 2>/dev/null | grep -qx "/chatter"; then
        log "topic /chatter: PRESENT"
        mark topic PASS
        log "--- ros2 topic info /chatter ---"
        ros2 topic info /chatter 2>/dev/null | tee -a "$OUT"
        log "--- one message from /chatter ---"
        timeout 10 ros2 topic echo /chatter --once > "$TMP/echo.log" 2>&1
        cat "$TMP/echo.log" | tee -a "$OUT"
        PUBLISHED="$(grep -m1 '^data:' "$TMP/echo.log" | sed -e 's/^data:[[:space:]]*//' -e "s/^'//" -e "s/'$//")"
    else
        log "topic /chatter: NOT FOUND. Your publisher must publish to /chatter."
        mark topic FAIL
    fi

    log "Starting ${PKG} ${LISTENER} ..."
    ( ros2 run "$PKG" "$LISTENER" > "$TMP/listener.log" 2>&1 ) &
    LPID=$!
    sleep 6
    kill "$TPID" "$LPID" 2>/dev/null
    wait "$TPID" "$LPID" 2>/dev/null
    pkill -f "ros2 run ${PKG}" 2>/dev/null

    log "--- listener output (first 6 lines) ---"
    head -n 6 "$TMP/listener.log" | tee -a "$OUT"

    HEARD_LINE="$(grep -m1 -i 'I heard' "$TMP/listener.log")"
    HEARD="$(echo "$HEARD_LINE" | sed -e 's/.*[Ii] heard[:]*[[:space:]]*//' -e 's/^"//' -e 's/"$//')"

    log ""
    log "published string : ${PUBLISHED:-<none captured>}"
    log "listener heard   : ${HEARD:-<none captured>}"

    if [ -n "$HEARD_LINE" ]; then mark listener PASS; else mark listener FAIL; fi

    if [ -z "$PUBLISHED" ]; then
        mark string_default UNKNOWN
    elif echo "$PUBLISHED" | grep -qi "hello world"; then
        log "CHECK: the published string is still Hello World. The assignment"
        log "       requires a different string."
        mark string_default FAIL
    else
        mark string_default PASS
    fi

    if [ -n "$PUBLISHED" ] && [ -n "$HEARD" ]; then
        if [ "$PUBLISHED" = "$HEARD" ]; then
            log "CHECK: the listener echoed the message unchanged. The assignment"
            log "       requires the subscriber to modify the string."
            mark string_modified FAIL
        else
            log "CHECK: the listener modified the string. OK"
            mark string_modified PASS
        fi
    else
        mark string_modified UNKNOWN
    fi
else
    log "Skipped: executables not available."
    mark topic FAIL
    mark listener FAIL
    mark string_default FAIL
    mark string_modified FAIL
fi

# -------------------------------------------------------------
section "8. TURTLESIM SCREENSHOT"
SHOT="$(find "$PA1_DIR" -maxdepth 1 -iname "*_turtle.png" | head -n 1)"
if [ -n "$SHOT" ]; then
    log "found: $(basename "$SHOT") ($(du -h "$SHOT" | cut -f1))"
    mark screenshot PASS
else
    log "No file matching *_turtle.png in ${PA1_DIR}"
    log "Save your turtlesim doodle as LASTNAME_turtle.png in the PA1 folder."
    mark screenshot FAIL
fi

# -------------------------------------------------------------
section "9. GIT HYGIENE"
if [ -d "$WS/build" ] || [ -d "$WS/install" ] || [ -d "$WS/log" ]; then
    log "build/install/log directories exist locally, which is normal."
fi
if git -C "$PA1_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    TRACKED_JUNK="$(git -C "$PA1_DIR" ls-files | grep -cE '(^|/)(build|install|log)/' || true)"
    log "tracked files inside build/install/log: ${TRACKED_JUNK}"
    if [ "${TRACKED_JUNK}" -eq 0 ]; then
        mark gitignore PASS
    else
        log "Add these to .gitignore and run: git rm -r --cached <dir>"
        mark gitignore FAIL
    fi
else
    log "Not inside a git repository."
    mark gitignore FAIL
fi

# -------------------------------------------------------------
section "10. MACHINE-READABLE SUMMARY"
for k in os ros bashrc colcon workspace build executables topic listener \
         string_default string_modified screenshot gitignore; do
    log "RESULT ${k}=${RESULT[$k]:-UNKNOWN}"
done

# -------------------------------------------------------------
section "11. STUDENT STATEMENT"
cat >> "$OUT" <<'EOS'

Complete the items below by editing this file in a text editor.

WHAT YOUR TALKER PUBLISHES (the exact string):
    

HOW YOUR LISTENER MODIFIES IT (one sentence):
    

ONE THING THAT DID NOT WORK THE FIRST TIME, AND HOW YOU FIXED IT:
    

STATUS: I confirm that ROS 2 Jazzy is installed, my workspace builds, and my
talker and listener run. If anything above failed, paste the exact error
message and your plan to fix it here instead:
    

EOS

echo ""
echo "=============================================="
echo "Done. Report written to: ${OUT}"
echo "Next steps:"
echo "  1. Open the report and complete Section 11."
echo "  2. Confirm your PA1 folder also has LASTNAME_turtle.png and README.md."
echo "  3. git add, git commit, git push."
echo "=============================================="
