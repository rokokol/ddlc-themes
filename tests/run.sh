#!/usr/bin/env bash
# The fast suite for install.sh: flag surface, the manifest contract, the per-component
# sweep, selective uninstall, staging, and the refusal path — everything that needs no
# container. tests/distro.sh covers what a real distribution provides; this covers what
# the installer promises
set -euo pipefail

HERE=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO="${1:-$(dirname "$HERE")}"

fails=0
say() { printf -- '-- %s\n' "$1"; }
die() {
  printf '!! %s\n' "$1" >&2
  fails=$((fails + 1))
}

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

cfg="$tmp/config"
claude="$tmp/claude"
manifest="$cfg/ddlc-themes/install-manifest"
run() { "$REPO/install.sh" --config-home "$cfg" --claude-home "$claude" "$@"; }

say "--help names every flag the case parses, and -v matches VERSION"
mapfile -t flags < <(
  sed -n 's/^ *\(-[-a-zA-Z0-9 |]*\))$/\1/p' "$REPO/install.sh" |
    tr '|' '\n' | tr -d ' ' | sort -u
)
((${#flags[@]})) || die "found no flags in install.sh — the extractor is broken"
help_out=$("$REPO/install.sh" --help)
for flag in "${flags[@]}"; do
  grep -qF -- "$flag" <<<"$help_out" || die "--help does not mention $flag"
done
[[ "$("$REPO/install.sh" -v)" == "ddlc-themes $(cat "$REPO/VERSION")" ]] ||
  die "-v does not print 'ddlc-themes \$(cat VERSION)'"

say "bad arguments are refused with exit 2, the usage-error code"
rc=0
run --config-home relative/path >/dev/null 2>&1 || rc=$?
((rc == 2)) || die "a relative config home exited $rc, not the usage-error code 2"
rc=0
run --claude-home relative >/dev/null 2>&1 || rc=$?
((rc == 2)) || die "a relative claude home exited $rc, not the usage-error code 2"
rc=0
run --component emacs >/dev/null 2>&1 || rc=$?
((rc == 2)) || die "an unknown component exited $rc, not the usage-error code 2"
rc=0
run --no-such-flag >/dev/null 2>&1 || rc=$?
((rc == 2)) || die "an unknown flag exited $rc, not the usage-error code 2"

say "a full install lands every component and writes the manifest"
run >/dev/null
[[ -f "$cfg/kitty/ddlc-kitty-dark.conf" ]] || die "kitty theme missing"
[[ -f "$cfg/btop/themes/ddlc-dark.theme" ]] || die "btop theme missing (or under its dist name)"
[[ -f "$cfg/matplotlib/stylelib/ddlc.mplstyle" ]] || die "matplotlib style missing"
[[ -f "$cfg/matplotlib/ddlc_cmaps.py" ]] || die "colormaps module missing"
[[ -f "$claude/themes/ddlc-dark.json" ]] || die "Claude Code theme missing"
[[ -f "$cfg/opencode/themes/ddlc.json" ]] || die "opencode theme missing"
[[ -f "$manifest" ]] || die "no manifest after install"
for comp in kitty btop matplotlib claude-code opencode; do
  grep -q "^$comp " "$manifest" || die "manifest has no $comp entries"
done

say "--uninstall --component removes one component and keeps the rest"
run --uninstall --component btop >/dev/null
[[ ! -e "$cfg/btop" ]] || die "selective uninstall left btop behind"
[[ -f "$cfg/kitty/ddlc-kitty-dark.conf" ]] || die "selective uninstall took kitty with it"
[[ -f "$claude/themes/ddlc-dark.json" ]] || die "selective uninstall took claude-code with it"
if grep -q '^btop ' "$manifest"; then die "manifest still claims btop"; fi

say "re-running a component sweeps its stale files and touches no other component"
stale="$cfg/kitty/ddlc-kitty-old.conf"
touch "$stale"
echo "kitty $stale" >>"$manifest"
run --component kitty >/dev/null
[[ ! -e "$stale" ]] || die "the sweep left a stale kitty file behind"
if grep -qF "$stale" "$manifest"; then die "manifest still lists the stale file"; fi
[[ -f "$cfg/matplotlib/ddlc_cmaps.py" ]] || die "installing kitty disturbed matplotlib"
[[ ! -e "$cfg/btop" ]] || die "installing kitty resurrected btop"

say "--uninstall takes everything out and is idempotent"
run --uninstall >/dev/null
[[ ! -e "$cfg/ddlc-themes" ]] || die "uninstall left the manifest dir"
[[ ! -e "$cfg/kitty" && ! -e "$cfg/matplotlib" && ! -e "$cfg/opencode" ]] ||
  die "uninstall left component files"
[[ ! -e "$claude/themes" ]] || die "uninstall left the Claude Code themes"
out=$(run --uninstall)
[[ "$out" == *"nothing to uninstall"* ]] || die "a second uninstall was not quiet: $out"

say "a pre-manifest install is still uninstallable (fallback layout)"
install -D -m644 "$REPO/dist/ddlc-kitty-dark.conf" "$cfg/kitty/ddlc-kitty-dark.conf"
install -D -m644 "$REPO/dist/ddlc-btop-dark.theme" "$cfg/btop/themes/ddlc-dark.theme"
run --uninstall >/dev/null
[[ ! -e "$cfg/kitty/ddlc-kitty-dark.conf" && ! -e "$cfg/btop" ]] ||
  die "legacy uninstall missed the pre-manifest layout"

say "DESTDIR stages the tree and the manifest records runtime paths"
stage="$tmp/stage"
run --destdir "$stage" --component kitty >/dev/null
[[ -f "$stage$cfg/kitty/ddlc-kitty-dark.conf" ]] || die "staged file not under DESTDIR"
staged_manifest="$stage$cfg/ddlc-themes/install-manifest"
[[ -f "$staged_manifest" ]] || die "no staged manifest"
if grep -v '^#' "$staged_manifest" | grep -qF "$stage"; then
  die "the staged manifest leaks DESTDIR into a recorded path"
fi

say "the preflight refuses completely when an install dep is missing"
stub="$tmp/bin"
mkdir -p "$stub"
for tool in bash cat dirname readlink sed tr grep rm rmdir mktemp; do
  ln -s "$(command -v "$tool")" "$stub/$tool"
done
echo "ID=debian" >"$tmp/os-release" # the flake-check sandbox has no /etc/os-release
rc=0
out=$(OS_RELEASE="$tmp/os-release" PATH="$stub" bash "$REPO/install.sh" \
  --config-home "$tmp/refused" --claude-home "$tmp/refused-claude" 2>&1) || rc=$?
((rc == 1)) || die "the preflight exited $rc, not the missing-dependency code 1"
grep -q 'missing dependencies' <<<"$out" || die "the refusal did not say what is missing"
grep -q ' - install$' <<<"$out" || die "the refusal did not name install(1)"
grep -qE '^  \$ ' <<<"$out" || die "the refusal printed no runnable guidance"
[[ ! -e "$tmp/refused" ]] || die "a refused install wrote files"

say "the guidance is per-distro and printed as runnable lines"
for pair in "debian:  \$ sudo apt install coreutils" \
  "ubuntu:  \$ sudo apt install coreutils" \
  "arch:  \$ sudo pacman -S --needed coreutils" \
  "fedora:  \$ sudo dnf install coreutils"; do
  id="${pair%%:*}"
  line="${pair#*:}"
  echo "ID=$id" >"$tmp/os-release"
  out=$(OS_RELEASE="$tmp/os-release" PATH="$stub" bash "$REPO/install.sh" \
    --config-home "$tmp/refused" --claude-home "$tmp/refused-claude" 2>&1) || true
  grep -qxF "$line" <<<"$out" || die "no '$line' in the $id refusal"
done

say "install.sh and its completions agree"
bash "$REPO/check-sh.sh" -c "$REPO/completions/install.sh.bash" "$REPO/completions/install.sh.zsh" \
  "$REPO/install.sh" >/dev/null || die "completions drift"

echo
if ((fails)); then
  echo "$fails failure(s)"
  exit 1
fi
echo "all install.sh checks passed"
