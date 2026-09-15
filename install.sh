#!/usr/bin/env bash
set -euo pipefail

here="$(cd -- "$(dirname -- "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
VERSION=$(cat "$here/VERSION")

config="${XDG_CONFIG_HOME:-$HOME/.config}"
claude_home="${CLAUDE_HOME:-$HOME/.claude}"
DESTDIR="${DESTDIR:-}"
COMPONENT="${COMPONENT:-all}"
OS_RELEASE="${OS_RELEASE:-/etc/os-release}"

usage() {
  cat <<EOF
install the ddlc-themes $VERSION kitty, btop, matplotlib, Claude Code and opencode themes

Installer for ddlc-themes on systems without Nix. Copies the rendered themes out of
dist/ into a config tree — nothing is built — and records every path it wrote in
share-style manifest at <config-home>/ddlc-themes/install-manifest, which --uninstall
consumes. Components are additive: installing one never touches another, and
--uninstall --component takes one back out on its own

Re-running a component converges it: a file a previous install of that component wrote
and this run does not is removed. Other components are never touched — install them one
at a time, take them out one at a time

usage: ./install.sh [options]
  -h, --help           show this help and exit
  -v, --version        print the version and exit
      --component C    kitty, btop, matplotlib, claude-code, opencode, or all
                       (default: $COMPONENT)
      --kitty          compatibility shorthand for --component kitty
      --btop           compatibility shorthand for --component btop
      --config-home D  install under D instead of $config
                       (env XDG_CONFIG_HOME)
      --claude-home D  install the Claude Code themes under D instead of $claude_home
                       (env CLAUDE_HOME)
      --destdir D      staging root: files land under D but the manifest records the
                       real paths (env DESTDIR)
      --uninstall      remove what a previous install wrote, by its manifest;
                       with --component C, only that component

kitty gets both variants next to kitty.conf, where an include with a bare name resolves.
btop, Claude Code and opencode list a theme under its filename, so the app segment is
dropped on the way in: ddlc-btop-dark.theme lands as ddlc-dark.theme, the Claude Code
themes as ddlc-dark.json and ddlc-light.json, and ddlc-opencode.json as ddlc.json.
matplotlib keeps its names — they are the API: plt.style.use("ddlc"), import ddlc_cmaps.
Everything lands as a plain file, yours to edit; only Claude Code reads outside
~/.config, which is what --claude-home covers

Exit 0 done, 1 when the install could not be made — a dependency missing, a manifest
that cannot be written — and 2 on a usage error
EOF
}

die() { # the request itself is wrong
  printf 'install.sh: %s\n' "$1" >&2
  exit 2
}

UNINSTALL=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h | --help)
      usage
      exit 0
      ;;
    -v | --version)
      echo "ddlc-themes $VERSION"
      exit 0
      ;;
    --kitty | --btop)
      COMPONENT="${1#--}"
      shift
      ;;
    --component)
      # Not ${2:?}: that exits 1 with bash's own message, and a usage error is 2
      (($# >= 2)) || die "$1 needs a component"
      COMPONENT="$2"
      shift 2
      ;;
    --config-home)
      (($# >= 2)) || die "$1 needs a directory"
      config="$2"
      shift 2
      ;;
    --claude-home)
      (($# >= 2)) || die "$1 needs a directory"
      claude_home="$2"
      shift 2
      ;;
    --destdir)
      (($# >= 2)) || die "$1 needs a directory"
      DESTDIR="$2"
      shift 2
      ;;
    --uninstall)
      UNINSTALL=1
      shift
      ;;
    *)
      usage >&2
      exit 2
      ;;
  esac
done

[[ "$config" == /* ]] || die "config home must be absolute: $config"
[[ "$claude_home" == /* ]] || die "claude home must be absolute: $claude_home"

case "$COMPONENT" in
  all | kitty | btop | matplotlib | claude-code | opencode) ;;
  *) die "component must be kitty, btop, matplotlib, claude-code, opencode, or all: $COMPONENT" ;;
esac

root="${DESTDIR%/}$config"
share_runtime="$config/ddlc-themes"
share="${DESTDIR%/}$share_runtime"
manifest="$share/install-manifest"

in_scope() { # is component $1 covered by this run's selection?
  [[ "$COMPONENT" == all || "$COMPONENT" == "$1" ]]
}

# --- manifest helpers ------------------------------------------------------------------
# Each line is `component path`: the component name first (it cannot contain a space),
# then the path it owns as its final runtime path (no DESTDIR) — the manifest ships
# inside a staged tree and stays correct wherever the tree ends up. The component field
# is what makes both the per-component sweep and --uninstall --component possible

old_entries=()
if [[ -f "$manifest" ]]; then
  mapfile -t old_entries < <(grep -v '^#' "$manifest")
fi

installed=()

put() { # put COMPONENT SRC RUNTIME_DST — install one file and record its owner
  install -D -m644 "$2" "${DESTDIR%/}$3"
  installed+=("$1 $3")
}

prune() { # remove now-empty parents of RUNTIME_PATH, stopping at its home root
  local dir stop
  dir="$(dirname "${DESTDIR%/}$1")"
  stop="${DESTDIR%/}$config"
  [[ "$1" == "$claude_home"/* ]] && stop="${DESTDIR%/}$claude_home"
  while [[ "$dir" == "$stop"/* ]]; do
    rmdir "$dir" 2>/dev/null || break
    dir="$(dirname "$dir")"
  done
}

legacy_entries() {
  # Installs made before the manifest existed (<= 1.0.0) left no record; this is their
  # layout, kept for exactly one release after the manifest arrived — delete this
  # function in the release after that
  local v
  for v in light dark; do
    echo "kitty $config/kitty/ddlc-kitty-$v.conf"
    echo "btop $config/btop/themes/ddlc-$v.theme"
    echo "claude-code $claude_home/themes/ddlc-$v.json"
  done
  echo "matplotlib $config/matplotlib/stylelib/ddlc.mplstyle"
  echo "matplotlib $config/matplotlib/stylelib/ddlc-dark.mplstyle"
  echo "matplotlib $config/matplotlib/ddlc_cmaps.py"
  echo "opencode $config/opencode/themes/ddlc.json"
}

# --- uninstall -------------------------------------------------------------------------

if ((UNINSTALL)); then
  entries=("${old_entries[@]}")
  had_manifest=1
  if [[ ! -f "$manifest" ]]; then
    had_manifest=0
    mapfile -t entries < <(legacy_entries)
  fi
  kept=()
  removed=0
  for entry in "${entries[@]}"; do
    [[ -z "$entry" ]] && continue
    comp="${entry%% *}"
    path="${entry#* }"
    if in_scope "$comp"; then
      if [[ -e "${DESTDIR%/}$path" ]]; then
        rm -f "${DESTDIR%/}$path"
        removed=$((removed + 1))
      fi
      prune "$path"
    else
      kept+=("$entry")
    fi
  done
  if ((had_manifest)) && ((${#kept[@]})); then
    {
      echo "# ddlc-themes $VERSION install manifest"
      printf '%s\n' "${kept[@]}"
    } >"$manifest"
    echo "uninstalled the $COMPONENT themes ($removed files); the rest stays"
  elif ((had_manifest)); then
    rm -f "$manifest"
    rmdir "$share" 2>/dev/null || true
    echo "uninstalled ddlc-themes from $root"
  elif ((removed)); then
    # A pre-manifest install: files were found and removed, but there is no record to
    # rewrite, so nothing claims the other components exist
    echo "uninstalled the $COMPONENT themes ($removed files, pre-manifest install)"
  else
    echo "ddlc-themes: nothing to uninstall under $root"
  fi
  exit 0
fi

# --- preflight: refuse loudly, install nothing ----------------------------------------
# install deps: the copy itself cannot happen without them — any missing means collect
# them all, print the report, exit 1 having written nothing.
# session deps: the applications being themed — a theme for an app you have not
# installed yet is still a valid install, so one warning each and the install proceeds

missing=()
absent=()

need() { command -v "$1" >/dev/null 2>&1 || missing+=("$1"); }
want() { command -v "$1" >/dev/null 2>&1 || absent+=("$1"); }

need install
if in_scope kitty; then want kitty; fi
if in_scope btop; then want btop; fi
if in_scope claude-code; then want claude; fi
if in_scope opencode; then want opencode; fi

distro_id() {
  sed -n 's/^ID\(_LIKE\)\?=//p' "$OS_RELEASE" 2>/dev/null | tr -d '"' | tr '\n' ' '
}

guidance() {
  # One recommended method per distro. Runnable lines are printed as `  $ command` —
  # two spaces, dollar, space — and the distro tests run exactly those lines, so this
  # text cannot rot silently. No -y/--noconfirm: a human is reading; the tests arrange
  # non-interactivity around the command, never inside it
  case " $(distro_id) " in
    *" arch "*)
      echo "Install them on Arch:"
      echo '  $ sudo pacman -S --needed coreutils'
      ;;
    *" debian "* | *" ubuntu "*)
      echo "Install them on Debian/Ubuntu:"
      echo '  $ sudo apt install coreutils'
      ;;
    *" fedora "*)
      echo "Install them on Fedora:"
      echo '  $ sudo dnf install coreutils'
      ;;
    *)
      echo "Install coreutils with your package manager"
      ;;
  esac
}

if ((${#missing[@]})); then
  {
    echo "install.sh: missing dependencies:"
    printf '  - %s\n' "${missing[@]}"
    echo
    guidance
  } >&2
  exit 1
fi
if ((${#absent[@]})); then
  printf 'install.sh: not found (the theme installs anyway): %s\n' "${absent[@]}" >&2
fi

# --- install ---------------------------------------------------------------------------

if in_scope kitty; then
  for variant in light dark; do
    put kitty "$here/dist/ddlc-kitty-$variant.conf" "$config/kitty/ddlc-kitty-$variant.conf"
  done
  echo "kitty: installed into $root/kitty — add \"include ddlc-kitty-dark.conf\" to kitty.conf"
fi

if in_scope btop; then
  for variant in light dark; do
    put btop "$here/dist/ddlc-btop-$variant.theme" "$config/btop/themes/ddlc-$variant.theme"
  done
  echo "btop: installed into $root/btop/themes — set color_theme = \"ddlc-dark\" in btop.conf"
fi

if in_scope matplotlib; then
  put matplotlib "$here/dist/ddlc.mplstyle" "$config/matplotlib/stylelib/ddlc.mplstyle"
  put matplotlib "$here/dist/ddlc-dark.mplstyle" "$config/matplotlib/stylelib/ddlc-dark.mplstyle"
  put matplotlib "$here/dist/ddlc_cmaps.py" "$config/matplotlib/ddlc_cmaps.py"
  echo "matplotlib: installed into $root/matplotlib — plt.style.use(\"ddlc\"), import ddlc_cmaps"
fi

if in_scope claude-code; then
  for variant in light dark; do
    put claude-code "$here/dist/ddlc-claude-code-$variant.json" "$claude_home/themes/ddlc-$variant.json"
  done
  echo "claude-code: installed into ${DESTDIR%/}$claude_home/themes — pick ddlc-dark or ddlc-light in /theme"
fi

if in_scope opencode; then
  put opencode "$here/dist/ddlc-opencode.json" "$config/opencode/themes/ddlc.json"
  echo "opencode: installed into $root/opencode/themes — set \"theme\": \"ddlc\" or pick it in /theme"
fi

# The per-component sweep: whatever a previous install of these components wrote and
# this run did not — a renamed theme leaves no stale file behind. Entries of components
# outside this run's scope carry over untouched
kept=()
for entry in "${old_entries[@]}"; do
  [[ -z "$entry" ]] && continue
  comp="${entry%% *}"
  path="${entry#* }"
  if in_scope "$comp"; then
    fresh=0
    for now in "${installed[@]}"; do
      [[ "$entry" == "$now" ]] && fresh=1
    done
    if ((fresh == 0)); then
      rm -f "${DESTDIR%/}$path"
      prune "$path"
    fi
  else
    kept+=("$entry")
  fi
done

install -d "$share"
{
  echo "# ddlc-themes $VERSION install manifest"
  printf '%s\n' "${kept[@]}" "${installed[@]}"
} >"$manifest"

echo "installed ddlc-themes $VERSION ($COMPONENT) — manifest: $manifest"
