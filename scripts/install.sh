#!/usr/bin/env bash
# Install Witnis. Default: full CLI via pip. Optional: download witnis-core binary.
set -euo pipefail

CORE_BINARY=0
PIP_TARGET="witnis"

usage() {
  cat <<'EOF'
Usage: scripts/install.sh [--core-binary] [--from-git]

  (default)     pip install -U witnis   # full Trusted Agent Loop CLI
  --from-git    pip install from GitHub master
  --core-binary also fetch latest witnis-core release asset for this OS/arch
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --core-binary) CORE_BINARY=1; shift ;;
    --from-git) PIP_TARGET="git+https://github.com/L00PLeGeNd/Witnis.git"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown arg: $1" >&2; usage; exit 1 ;;
  esac
done

if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
  echo "Python 3.11+ required for the full witnis CLI (pip fallback)." >&2
  exit 1
fi
PY="$(command -v python3 || command -v python)"

echo "==> pip install ${PIP_TARGET}"
"$PY" -m pip install -U "${PIP_TARGET}"
echo "==> witnis version: $($PY -m witnis version 2>/dev/null || witnis version || true)"

if [[ "$CORE_BINARY" -eq 1 ]]; then
  OS="$(uname -s)"
  ARCH="$(uname -m)"
  case "$OS/$ARCH" in
    Linux/x86_64) ARTIFACT="witnis-core-x86_64-unknown-linux-gnu" ;;
    Darwin/arm64) ARTIFACT="witnis-core-aarch64-apple-darwin" ;;
    Darwin/x86_64) ARTIFACT="witnis-core-x86_64-apple-darwin" ;;
    *)
      echo "No prebuilt witnis-core mapping for $OS/$ARCH — use cargo build -p witnis-cli --release" >&2
      exit 0
      ;;
  esac
  DEST="${WITNIS_CORE_DIR:-$HOME/.local/bin}"
  mkdir -p "$DEST"
  URL="https://github.com/L00PLeGeNd/Witnis/releases/latest/download/${ARTIFACT}"
  echo "==> download ${URL}"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL -o "${DEST}/witnis-core" "$URL" || {
      echo "Download failed (no release asset yet?). Build locally: cargo build -p witnis-cli --release" >&2
      exit 0
    }
  else
    wget -q -O "${DEST}/witnis-core" "$URL"
  fi
  chmod +x "${DEST}/witnis-core"
  echo "==> installed ${DEST}/witnis-core"
fi

echo "Done. Docs: docs/BINARY.md · loop: witnis loop-init"
