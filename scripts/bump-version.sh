#!/usr/bin/env bash
set -euo pipefail

PART="${1:-patch}"

# Find latest v-prefixed tag (including pre-release like v3.0.0-rc1)
LATEST=$(git tag --list 'v*' --sort=-version:refname | head -1)

if [ -z "$LATEST" ]; then
  echo "1.0.0"
  exit 0
fi

# Strip leading 'v'
VER="${LATEST#v}"

# Check for pre-release tag (e.g., 3.0.0-rc1)
if [[ "$VER" =~ ^([0-9]+\.[0-9]+\.[0-9]+)-rc([0-9]+)$ ]]; then
  BASE="${BASH_REMATCH[1]}"
  RC="${BASH_REMATCH[2]}"

  # Compute stable + part bump for option 3
  IFS='.' read -r M1 M2 M3 <<< "$BASE"
  case "$PART" in
    major) STABLE_BUMP="$((M1 + 1)).0.0" ;;
    minor) STABLE_BUMP="$M1.$((M2 + 1)).0" ;;
    patch) STABLE_BUMP="$M1.$M2.$((M3 + 1))" ;;
    *)     STABLE_BUMP="unknown" ;;
  esac

  echo ""
  echo "Current tag: $LATEST"
  echo "What next?"
  echo "  1) Promote to stable (v${BASE})"
  echo "  2) Bump RC (v${BASE}-rc$((RC + 1)))"
  echo "  3) Promote to stable and bump $PART (v${STABLE_BUMP})"
  echo "  q) Abort"
  read -p "Choose [1/2/3/q]: " choice
  echo ""
  case "$choice" in
    1) echo "$BASE" ;;
    2) echo "${BASE}-rc$((RC + 1))" ;;
    3) echo "$STABLE_BUMP" ;;
    *) echo "Aborted." >&2; exit 1 ;;
  esac
  exit 0
fi

# Regular semver bump
IFS='.' read -r MAJ MIN PAT <<< "$VER"

case "$PART" in
  major) echo "$((MAJ + 1)).0.0" ;;
  minor) echo "$MAJ.$((MIN + 1)).0" ;;
  patch) echo "$MAJ.$MIN.$((PAT + 1))" ;;
  *)     echo "usage: $0 {major|minor|patch}" >&2; exit 1 ;;
esac
