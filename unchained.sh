#!/usr/bin/env bash
# unchained.sh - one command that walks you through a whole case on Linux/macOS.
#
# Finds the isolated toolchain ./setup.sh created, then hands off to the
# self-driving `sentinel` flow (welcome -> one question -> verified card ->
# depth -> explicit launch -> live run -> verify/view). No flags, no env vars.
#
# First time here?  Run  ./setup.sh  once, then  ./unchained.sh  to start.
# Extra arguments pass straight through (e.g. ./unchained.sh verify <bundle>).
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$REPO_DIR/.venv"

# Prefer the repo .venv setup.sh created; fall back to an already-activated venv
# (VIRTUAL_ENV) or a `sentinel` already on PATH, so a fresh shell just works.
if [ -x "$VENV/bin/sentinel" ]; then
    LAUNCHER="$VENV/bin/sentinel"
elif [ -n "${VIRTUAL_ENV:-}" ] && [ -x "$VIRTUAL_ENV/bin/sentinel" ]; then
    LAUNCHER="$VIRTUAL_ENV/bin/sentinel"
elif command -v sentinel >/dev/null 2>&1; then
    LAUNCHER="sentinel"
else
    echo ""
    echo "Unchained is not installed yet. One command sets it up:"
    echo "  ./setup.sh"
    echo "Then run  ./unchained.sh  again to start your first case."
    echo ""
    echo "Prefer full isolation? The offline container needs no install and no key:"
    echo "  docker compose run --rm offline"
    exit 2
fi

# No arguments = the self-driving guided flow. Extra args pass through verbatim.
exec "$LAUNCHER" "$@"
