#!/usr/bin/env bash
# setup.sh - ONE command that checks and installs everything on Linux/macOS.
#
# Mirrors setup.ps1 for POSIX: it finds CPython 3.11, creates an isolated .venv
# beside the repo, installs Unchained with its pinned DFIR dependencies, and
# proves the toolchain imports. It reads no evidence, asks for no API key, and
# calls OpenAI zero times.
#
#   ./setup.sh            install + verify everything
#   ./setup.sh --check    re-verify an existing install (no install, no tests)
#
# Then start a whole case with one command:  ./unchained.sh
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$REPO_DIR/.venv"
PY="$VENV/bin/python3"

c_cyan="\033[36m"; c_green="\033[32m"; c_yellow="\033[33m"; c_gray="\033[90m"; c_reset="\033[0m"
say()  { printf "%b%s%b\n" "$1" "$2" "$c_reset"; }

banner() {
    printf "\n%b" "$c_cyan"
    echo "+========================================================================+"
    echo "|                               UNCHAINED                                |"
    echo "|       Autonomous Digital Forensics & Incident Response - GPT-5.6       |"
    echo "|       Point me at one case. I will show you what is safe to run.       |"
    echo "+========================================================================+"
    printf "%b\n" "$c_reset"
}

report_docker() {
    if command -v docker >/dev/null 2>&1; then
        say "$c_green" "      Docker detected - the isolated, offline container path is available too:"
        say "$c_gray"  "        docker compose run --rm offline   (no key, no evidence, no network)"
    else
        say "$c_gray" "      Docker not found (optional). For a fully isolated run install Docker:"
        say "$c_gray" "        https://www.docker.com/products/docker-desktop/"
    fi
}

# --- locate a CPython 3.11 interpreter -------------------------------------
find_py311() {
    for cand in python3.11 python3 python; do
        if command -v "$cand" >/dev/null 2>&1; then
            if "$cand" -c 'import sys; raise SystemExit(0 if sys.version_info[:2]==(3,11) else 1)' 2>/dev/null; then
                command -v "$cand"; return 0
            fi
        fi
    done
    return 1
}

banner

if [ "${1:-}" = "--check" ]; then
    say "$c_cyan" "[check] Verifying the existing environment (no install, no tests)"
    problems=0
    if [ ! -x "$PY" ]; then
        say "$c_yellow" "  - No isolated environment at $VENV - run ./setup.sh once."; problems=1
    else
        if ! "$PY" -m pip check >/dev/null 2>&1; then
            say "$c_yellow" "  - Dependency integrity check failed - run ./setup.sh to repair."; problems=1
        fi
        if ! "$PY" -c "import unchained" >/dev/null 2>&1; then
            say "$c_yellow" "  - The 'unchained' package does not import - run ./setup.sh to repair."; problems=1
        fi
    fi
    report_docker
    if [ "$problems" -ne 0 ]; then say "$c_yellow" "NOT READY"; exit 1; fi
    say "$c_green" "READY - toolchain healthy. Start a whole case with one command:  ./unchained.sh"
    exit 0
fi

PY311="$(find_py311 || true)"
if [ -z "$PY311" ]; then
    say "$c_yellow" "CPython 3.11 was not found. Install it, then rerun ./setup.sh:"
    say "$c_gray"   "  Debian/Ubuntu:  sudo apt install python3.11 python3.11-venv"
    say "$c_gray"   "  macOS (brew):   brew install python@3.11"
    exit 1
fi

say "$c_cyan" "[1/4] Creating an isolated environment: $VENV"
if [ ! -x "$PY" ]; then "$PY311" -m venv "$VENV"; fi

say "$c_cyan" "[2/4] Upgrading pip and build front-end"
"$PY" -m pip install --upgrade pip >/dev/null

say "$c_cyan" "[3/4] Installing Unchained and its pinned DFIR dependencies"
"$PY" -m pip install -e ".[dev]"
"$PY" -m pip check

say "$c_cyan" "[4/4] Proving the toolchain imports"
"$PY" -c "import unchained, openai, volatility3; print('      PASS  unchained + openai + volatility3 import cleanly')"

echo
report_docker
echo
say "$c_green" "READY"
echo
say "$c_cyan"  "+-- ONE COMMAND. IT WALKS YOU THROUGH THE REST. -------------------------+"
say "$c_gray"  "| Profiles one case locally (\$0, no key, no OpenAI), shows a verified     |"
say "$c_gray"  "| card, asks the depth, and only then stops for your explicit launch      |"
say "$c_gray"  "| phrase. No flags, no environment variables.                            |"
say "$c_cyan"  "+------------------------------------------------------------------------+"
echo
say "$c_green" "  ./unchained.sh"
echo
say "$c_gray"  "Re-verify anytime without reinstalling:  ./setup.sh --check"
