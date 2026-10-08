# CLAUDE.md

## What this repo is

The DDLC colours as themes for kitty, btop, matplotlib, Claude Code and opencode, plus a web kit, a report stylesheet, letter styles and a syntax table, light and dark, rendered by `generate.sh` out of `ddlc-palette`. kitty and btop come from the base16 schemes, the rest from the flat `palette.env`, because they have more roles than sixteen slots. Nothing here is a taste call except which slot goes where. `dist/` holds the rendered files, committed for consumers without Nix

Everything that is not a terminal reads two tables in `generate.sh`: `ui_roles` and `syntax_slots`. Other repositories depend on their names, so renaming or removing a role is a breaking release:

- `ddlc-obsidian-theme` vendors `dist/ddlc-tokens.css`
- `ddlc.nvim` vendors `dist/ddlc-syntax.json`
- `easy-bitmap.github.io` and `fly-vs-cybersafe-lct2026` vendor `ddlc-ui.css`, the two scripts and the font
- `mail-node` and `skibidi-vpn` read `lib.mail` through their flake lock

Seams in `rokokol/huix`, and no module on any: `programs/term/kitty.nix` does `readFile lib.kitty.dark`, `programs/cli/btop.nix` sets `source = lib.btop.dark`, `programs/cli/matplotlib.nix` sets `source =` on the three `lib.matplotlib` paths. That is deliberate: the themes are files, and a module would only wrap `readFile`s. The Claude Code and opencode themes are NOT deployed declaratively there on purpose: the owner wants them as plain editable files, placed once by `install.sh`

## Build / check

```sh
nix build                # the rendered themes
nix flake check          # dist/ current, every value filled, module wiring, scripts-lint, tests/run.sh
./tests/run.sh           # the installer suite alone, outside the sandbox
./tests/distro.sh fedora # the full cycle in a real container (docker/podman; deliberate, images are large)
nix fmt -- --ci
```

`VERSION` is the one source of version: the package reads it, `install.sh -v` prints it, CI asserts `CHANGELOG.md` has a matching heading. `install.sh` is standard huix-standard grammar adapted to a config tree: no `--prefix` (themes live in `~/.config` and `~/.claude`), components are **additive** with a per-component sweep, and `--uninstall --component C` takes one out selectively; the manifest lines carry the owning component first. New flags update both `completions/` files in the same commit, or `check-sh.sh -c` fails the flake check

`docs/ui-demo.html` loads the kit's module scripts, so a browser opens it only over HTTP: `python3 -m http.server` at the root

## Changing a colour

It comes from `ddlc-palette`, as a base16 scheme for kitty and btop and as a named colour out of `palette.env` for the rest, never a literal here. What this repo may change is which slot goes where, in `generate.sh`; then regenerate `dist/`, or `dist-is-current` fails. The weekly `palette-drift.yml` re-renders against the palette's HEAD rather than the lock and opens a pull request when a colour has moved upstream

A role never takes the name of a palette colour, a stylesheet in `src/` reads only names something defines, and every syntax colour holds 3:1 on its ground: `generate.sh` refuses a run that breaks one of these. A stylesheet colour goes through a role, so it follows both variants; a palette name is read directly only where the colour is the same on both sides

btop only finds a theme under the name it lands with, which is why `install.sh` places the files by name rather than copying a directory

## Releasing

Every user-visible change adds a bullet under `## Unreleased` in `CHANGELOG.md`. A release moves those bullets under a new version heading with the date, tags `v<x.y.z>` and cuts a `gh release` whose notes are that section. Dates belong in this file and nowhere else: the no-dates rule holds everywhere but here, because Keep a Changelog asks for them
