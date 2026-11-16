#!/usr/bin/env bash
# Distro tests for ddlc-themes: run install.sh for real, as root, inside a container of
# an actual distribution — the one thing the stub-based suite cannot do. Asserts the
# whole contract: the preflight refuses and its printed guidance actually works, the
# install lands every component, selective uninstall keeps the rest, --uninstall takes
# everything back out.
#
#   tests/distro.sh              every distribution below
#   tests/distro.sh debian       just one
#
# Needs docker or podman. In CI this runs on push to master, weekly, and by hand — never
# on pull requests: a flaky mirror must not redden someone's change. Images are :latest
# on purpose — the weekly run is the upstream-drift detector, so no assertion may depend
# on what an image happens to carry already.
#
# From the huix-standard template, adapted: this installer projects onto a config tree
# (~/.config and ~/.claude), not a prefix, so the PREFIX asserts become config-home ones
set -euo pipefail

HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO=$(dirname "$HERE")

declare -A IMAGE=(
  [debian]=docker.io/library/debian:latest
  [ubuntu]=docker.io/library/ubuntu:latest
  [arch]=docker.io/library/archlinux:latest
  [fedora]=docker.io/library/fedora:latest
)

# Bootstrap: only what the harness itself needs to run in a minimal image — never a
# dependency the preflight's guidance is supposed to provide, or the guidance test would
# pass because the answer was planted
declare -A BOOTSTRAP=(
  [debian]='apt-get update -qq && apt-get install -y -qq bash'
  [ubuntu]='apt-get update -qq && apt-get install -y -qq bash'
  [arch]='pacman -Syu --noconfirm --needed bash'
  [fedora]='dnf install -y -q bash'
)

# ======================================================================================
# host half: find an engine, pull fresh, re-execute this script inside the container
# ======================================================================================

if [[ "${1:-}" != "--inside" ]]; then
  engine=""
  for candidate in "${CONTAINER_ENGINE:-}" docker podman; do
    [[ -n "$candidate" ]] || continue
    if command -v "$candidate" >/dev/null && "$candidate" info >/dev/null 2>&1; then
      engine="$candidate"
      break
    fi
  done
  if [[ -z "$engine" ]]; then
    echo "tests/distro.sh: needs a working docker or podman" >&2
    exit 1
  fi

  wanted=("$@")
  ((${#wanted[@]})) || wanted=(debian ubuntu arch fedora)

  fails=0
  for distro in "${wanted[@]}"; do
    image="${IMAGE[$distro]:-}"
    if [[ -z "$image" ]]; then
      echo "tests/distro.sh: no such distribution: $distro" >&2
      exit 1
    fi
    printf '\n== %s (%s)\n' "$distro" "$image"
    # One retry on the pull: a mirror hiccup is not a verdict on anything
    "$engine" pull -q "$image" >/dev/null || "$engine" pull -q "$image" >/dev/null
    # The checkout goes in read-only — the run must not be able to edit it
    if ! "$engine" run --rm -v "$REPO:/src:ro" "$image" \
      bash /src/tests/distro.sh --inside "$distro"; then
      printf '  %s: FAILED\n' "$distro"
      fails=$((fails + 1))
    else
      printf '  %s: passed\n' "$distro"
    fi
  done
  ((fails)) && exit 1
  echo
  echo "all distributions passed"
  exit 0
fi

# ======================================================================================
# container half
# ======================================================================================

distro="$2"

say() { printf '\n  -- %s\n' "$1"; }
die() {
  printf '  !! %s\n' "$1" >&2
  exit 1
}

say "bootstrap ($distro)"
bash -c "${BOOTSTRAP[$distro]}" >/dev/null

# The checkout is mounted read-only; work on a copy a package manager cannot be blamed for
cp -r /src /work
cd /work

config="$HOME/.config"
claude="$HOME/.claude"
share_dir="$config/ddlc-themes"
manifest="$share_dir/install-manifest"

say "a relative config home is rejected"
if ./install.sh --config-home relative/path >/dev/null 2>&1; then
  die "install.sh accepted a relative config home"
fi

say "install, running the printed guidance when the preflight refuses"
rc=0
out=$(./install.sh 2>&1) || rc=$?
if ((rc != 0)); then
  # The refusal must be complete and clean: name what is missing, write nothing
  printf '%s\n' "$out" | grep -q 'missing dependencies' ||
    die "the refusal did not say what is missing: $out"
  [[ ! -e "$share_dir" && ! -e "$config/kitty" ]] ||
    die "a refused install left files behind"
  printf '%s\n' "$out" | grep -qE 'command not found|: line [0-9]' &&
    die "the preflight listed what is missing and then carried on: $out"

  # Runnable guidance lines are `  $ command`; they are run exactly as printed.
  # Non-interactivity is arranged around the command — DEBIAN_FRONTEND, yes on stdin —
  # never inside it: the printed line has no -y because a human reads it
  commands=$(printf '%s\n' "$out" | sed -n 's/^  \$ //p')
  if [[ -z "$commands" ]]; then
    # A required dep with no scriptable official method on this distribution: visible
    # skip, green job. Red is reserved for the standard's promise breaking
    echo "::notice title=ddlc-themes distro test::SKIP on $distro — guidance is manual-only"
    printf '  SKIP: no runnable guidance on %s\n' "$distro"
    exit 0
  fi
  # The container is root and none of these images ships sudo. Answered with a shim, not
  # by editing the line: a sudo can sit mid-pipeline (| sudo tee) where stripping a
  # prefix cannot reach, and an edited line is no longer the line the reader was given.
  # exec env, not exec: a printed line may carry VAR=value assignments after sudo
  if ! command -v sudo >/dev/null; then
    printf '#!/bin/sh\nexec env "$@"\n' >/usr/local/bin/sudo
    chmod +x /usr/local/bin/sudo
  fi
  export DEBIAN_FRONTEND=noninteractive
  while IFS= read -r cmd; do
    printf '  running printed guidance: %s\n' "$cmd"
    # yes answers "y" to [Y/n]-style prompts; dnf treats an empty answer as No. Fed by
    # process substitution, not a pipe: pipefail would turn yes's own SIGPIPE death —
    # normal for a command that never reads stdin — into a failed pipeline
    bash -c "$cmd" < <(yes 2>/dev/null) || die "printed guidance failed: $cmd"
  done <<<"$commands"

  say "install succeeds once the guidance has been followed"
  ./install.sh || die "install failed after following the guidance"
else
  echo "  (every install dependency was already present — the refusal path ran in tests/run.sh)"
fi

say "the installed themes answer"
[[ -f "$manifest" ]] || die "no install-manifest after install"
[[ -f "$config/kitty/ddlc-kitty-dark.conf" ]] || die "kitty theme missing"
[[ -f "$config/btop/themes/ddlc-dark.theme" ]] || die "btop theme missing"
[[ -f "$config/matplotlib/stylelib/ddlc.mplstyle" ]] || die "matplotlib style missing"
[[ -f "$claude/themes/ddlc-dark.json" ]] || die "Claude Code theme missing"
[[ -f "$config/opencode/themes/ddlc.json" ]] || die "opencode theme missing"
version_out=$(./install.sh --version)
[[ "$version_out" == *"$(cat VERSION)"* ]] ||
  die "--version does not match VERSION: $version_out"
./install.sh --help >/dev/null || die "--help failed"

say "selective uninstall removes one component and keeps the rest"
./install.sh --uninstall --component btop || die "--uninstall --component failed"
[[ ! -e "$config/btop" ]] || die "selective uninstall left btop behind"
[[ -f "$config/kitty/ddlc-kitty-dark.conf" ]] || die "selective uninstall took kitty"
./install.sh --component btop || die "reinstalling one component failed"
[[ -f "$config/btop/themes/ddlc-dark.theme" ]] || die "btop did not come back"

say "uninstall removes exactly what the manifest names"
mapfile -t manifest_paths < <(grep -v '^#' "$manifest" | sed 's/^[a-z-]* //')
./install.sh --uninstall || die "--uninstall failed"
for path in "${manifest_paths[@]}"; do
  [[ ! -e "$path" ]] || die "uninstall left $path behind"
done
[[ ! -e "$share_dir" ]] || die "uninstall left $share_dir behind"
[[ ! -e "$claude/themes/ddlc-dark.json" ]] || die "uninstall left the Claude Code themes"

say "a second uninstall is quiet and succeeds"
./install.sh --uninstall >/dev/null || die "uninstall is not idempotent"

echo
echo "  $distro: full cycle passed"
