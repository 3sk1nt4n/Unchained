#!/usr/bin/env bash
# Unchained one-line bootstrap for Linux and macOS (Docker lane).
#   curl -fsSL https://raw.githubusercontent.com/3sk1nt4n/Unchained/main/get.sh | bash
# Clones the repo, builds the hardened offline container, optionally stores
# your OpenAI key with hidden input for the live Luna canary, and opens the
# guided onboarding. It never echoes, logs, or uploads the key, and never
# reads evidence.

set -euo pipefail

CYAN=$'\033[38;5;45m'
VIOLET=$'\033[38;5;141m'
GREEN=$'\033[38;5;78m'
AMBER=$'\033[38;5;214m'
GRAY=$'\033[38;5;245m'
BOLD=$'\033[1m'
RESET=$'\033[0m'
if [ ! -t 1 ] || [ -n "${NO_COLOR:-}" ]; then
  CYAN="" VIOLET="" GREEN="" AMBER="" GRAY="" BOLD="" RESET=""
fi

step() { printf '%s[%s]%s %s\n' "$CYAN" "$1" "$RESET" "$2"; }
note() { printf '      %s%s%s\n' "$GRAY" "$1" "$RESET"; }

printf '\n%s+========================================================================+%s\n' "$CYAN" "$RESET"
printf '%s|                               UNCHAINED                                |%s\n' "$BOLD" "$RESET"
printf '%s|                Unchained reasoning. Chained evidence.                  |%s\n' "$VIOLET" "$RESET"
printf '%s|    One command: build the hardened container, walk into your case.    |%s\n' "$GRAY" "$RESET"
printf '%s+========================================================================+%s\n\n' "$CYAN" "$RESET"
printf '%sThis bootstrap never reads evidence and never sends anything to OpenAI.%s\n' "$AMBER" "$RESET"
printf '%sThe offline lane has no network at all; the paid Sol lane is Windows-native.%s\n\n' "$AMBER" "$RESET"

for tool in git docker; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    printf 'Required tool %s was not found. Install Git and Docker (with Compose), then rerun.\n' "$tool" >&2
    exit 1
  fi
done

step "1/4" "Getting the repository"
if [ -f "./compose.yaml" ] && [ -f "./setup.ps1" ]; then
  REPO="$(pwd)"
  note "Using the current checkout: $REPO"
else
  REPO="$HOME/Unchained"
  if [ ! -f "$REPO/compose.yaml" ]; then
    git clone https://github.com/3sk1nt4n/Unchained.git "$REPO"
  else
    note "Reusing the existing checkout: $REPO"
  fi
fi
cd "$REPO"

step "2/4" "Building the hardened offline image (no key, no network at runtime)"
docker compose build

step "3/4" "Optional: store your OpenAI key for the live Luna canary (hidden input)"
note "The key is written to a private local file (chmod 600) and referenced through"
note "OPENAI_API_KEY_FILE. It is never echoed, never committed, never logged."
note "Press Enter on an empty prompt to skip and stay fully offline."
KEY=""
if [ -t 0 ]; then
  printf '      Paste key (input stays hidden): '
  read -rs KEY || KEY=""
  printf '\n'
else
  note "Non-interactive shell detected; skipping key capture."
fi
if [ -n "$KEY" ]; then
  KEY_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/sentinel-unchained"
  KEY_FILE="$KEY_DIR/openai_api_key"
  mkdir -p "$KEY_DIR"
  umask 177
  printf '%s\n' "$KEY" > "$KEY_FILE"
  chmod 600 "$KEY_FILE"
  KEY=""
  printf '      %sSaved to %s (chmod 600).%s\n' "$GREEN" "$KEY_FILE" "$RESET"
  note "Run the cheap live canary any time with:"
  note "  OPENAI_API_KEY_FILE=$KEY_FILE docker compose --profile live run --rm live-smoke"
else
  printf '      %sSkipped. Everything below stays local and free.%s\n' "$GREEN" "$RESET"
fi

step "4/4" "Opening the guided onboarding (zero-key, zero-spend welcome)"
docker compose run --rm offline

printf '\n%sNext moves:%s\n' "$CYAN" "$RESET"
printf '  docker compose run --rm offline profile /evidence --json     synthetic fixture, $0\n'
printf '  SENTINEL_EVIDENCE_PATH=/cases/CASE-A \\\n'
printf '    docker compose run --rm offline profile /evidence --json   your own folder, read-only\n'
printf '  OPENAI_API_KEY_FILE=<file> docker compose --profile live run --rm live-smoke\n'
