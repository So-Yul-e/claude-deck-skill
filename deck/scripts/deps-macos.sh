#!/usr/bin/env bash
set -eu

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DECK_HOME="${DECK_HOME:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-deck-skill}"
DECK_VENV="$DECK_HOME/venv"
DECK_PYTHON="$DECK_VENV/bin/python"
REQ_FILE="$SKILL_DIR/requirements.txt"
FONT_SOURCE_DIR="$SKILL_DIR/assets/fonts"
FONT_TARGET_DIR="${DECK_FONT_TARGET_DIR:-$HOME/Library/Fonts}"

find_brew() {
  if command -v brew >/dev/null 2>&1; then
    command -v brew
    return 0
  fi
  for candidate in /opt/homebrew/bin/brew /usr/local/bin/brew; do
    if [ -x "$candidate" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

find_python() {
  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return 0
  fi
  for candidate in /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
    if [ -x "$candidate" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

has_renderer() {
  command -v soffice >/dev/null 2>&1 || [ -d "/Applications/Microsoft PowerPoint.app" ] || [ -d "$HOME/Applications/Microsoft PowerPoint.app" ]
}

has_fonts_installed() {
  if command -v fc-match >/dev/null 2>&1; then
    regular_family="$(fc-match -f '%{family}\n' 'Pretendard:style=Regular' 2>/dev/null || true)"
    bold_family="$(fc-match -f '%{family}\n' 'Pretendard:style=Bold' 2>/dev/null || true)"
    if printf '%s\n' "$regular_family" | grep -qi 'Pretendard' && \
       printf '%s\n' "$bold_family" | grep -qi 'Pretendard'; then
      return 0
    fi
  fi
  { [ -f "$FONT_TARGET_DIR/Pretendard-Regular.otf" ] && \
    [ -f "$FONT_TARGET_DIR/Pretendard-Bold.otf" ]; } || \
  { [ -f "$HOME/Library/Fonts/Pretendard-Regular.otf" ] && \
    [ -f "$HOME/Library/Fonts/Pretendard-Bold.otf" ]; } || \
  { [ -f "/Library/Fonts/Pretendard-Regular.otf" ] && \
    [ -f "/Library/Fonts/Pretendard-Bold.otf" ]; }
}

has_python_env() {
  [ -x "$DECK_PYTHON" ] && "$DECK_PYTHON" - <<'PY' >/dev/null 2>&1
import PIL  # noqa: F401
import pptx  # noqa: F401
import pypdf  # noqa: F401
PY
}

check_deps() {
  missing=0
  if has_python_env; then
    echo "READY    Python packages — python-pptx + Pillow + pypdf"
  else
    echo "MISSING  deck venv — python-pptx + Pillow + pypdf"
    missing=1
  fi

  if has_renderer; then
    echo "READY    renderer — LibreOffice or Microsoft PowerPoint"
  else
    echo "MISSING  renderer — LibreOffice or Microsoft PowerPoint"
    missing=1
  fi

  if command -v pdffonts >/dev/null 2>&1; then
    echo "READY    PDF font checker — pdffonts"
  else
    echo "MISSING  PDF font checker — pdffonts"
    missing=1
  fi

  if has_fonts_installed; then
    echo "READY    font — Pretendard installed"
  else
    echo "MISSING  font — Pretendard not installed in system fonts"
    missing=1
  fi

  if [ "$missing" -ne 0 ]; then
    echo
    echo "Install is available after user approval:"
    echo "  bash \"$SCRIPT_DIR/deps-macos.sh\" --install"
    return 1
  fi

  echo "READY    deck skill is runnable"
}

install_fonts() {
  mkdir -p "$FONT_TARGET_DIR"
  cp -f "$FONT_SOURCE_DIR/Pretendard-Regular.otf" "$FONT_TARGET_DIR/"
  cp -f "$FONT_SOURCE_DIR/Pretendard-Bold.otf" "$FONT_TARGET_DIR/"
  if command -v fc-cache >/dev/null 2>&1; then
    fc-cache -f "$FONT_TARGET_DIR" >/dev/null 2>&1 || true
  fi
}

install_deps() {
  brew_bin="$(find_brew || true)"
  python_bin="$(find_python || true)"

  if [ -z "$python_bin" ]; then
    if [ -z "$brew_bin" ]; then
      echo "Python 3 is missing and Homebrew was not found." >&2
      return 1
    fi
    "$brew_bin" install python
    python_bin="$(find_python || true)"
  fi

  mkdir -p "$DECK_HOME"
  if [ ! -x "$DECK_PYTHON" ]; then
    "$python_bin" -m venv "$DECK_VENV"
  fi
  "$DECK_PYTHON" -m pip install --upgrade pip >/dev/null
  "$DECK_PYTHON" -m pip install -r "$REQ_FILE"

  install_fonts

  if ! has_renderer; then
    if [ -z "$brew_bin" ]; then
      echo "No renderer found. Install LibreOffice or Microsoft PowerPoint." >&2
      return 1
    fi
    "$brew_bin" install --cask libreoffice
  fi

  if ! command -v pdffonts >/dev/null 2>&1; then
    if [ -z "$brew_bin" ]; then
      echo "pdffonts is missing and Homebrew was not found." >&2
      return 1
    fi
    "$brew_bin" install poppler
  fi

  check_deps
}

case "${1:---check}" in
  --check)
    check_deps
    ;;
  --install)
    install_deps
    ;;
  --python)
    if has_python_env; then
      printf '%s\n' "$DECK_PYTHON"
    else
      echo "Run bash \"$SCRIPT_DIR/deps-macos.sh\" --install first." >&2
      exit 1
    fi
    ;;
  *)
    echo "Usage: bash deps-macos.sh [--check|--install|--python]" >&2
    exit 2
    ;;
esac
