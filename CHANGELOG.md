# Changelog

Kept in the shape of [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), versioned by [semver](https://semver.org/spec/v2.0.0.html)

## [Unreleased]

### Changed

- `install.sh` now exits 2, not 1, on a usage error — an unknown flag, a relative `--config-home`/`--claude-home`, or an unknown `--component` — and `--help` ends with the `Exit` sentence naming every code it can produce; a missing dependency in the preflight still exits 1
- the installer's completions are now drift-checked against `install.sh` by the vendored [bash-best-practices](https://github.com/rokokol/bash-best-practices-skill) `check-sh.sh -c`, replacing `tests/check-completions.sh`

### Fixed

- `completions/install.sh.bash` no longer uses `mapfile`, which the bash 3.2 a stock macOS ships does not have, so sourcing the completion there no longer fails with "mapfile: command not found"

## [2.0.1] - 2026-09-02

### Added

- `ddlc-report.css` speaks the inform level: `--ddlc-inform-ground` and `--ddlc-inform-border` (a dot ground under the ink with a blush frame in light, yuriShadow under a yuri frame on dark), plus a `.ddlc-inform` class shaped like the game's own dialog box — framed on all sides, everything centred, the ink doing the talking. Consumers that were rebuilding this from the raw palette's character names can now read it from the stylesheet like every other role

## [2.0.0] - 2026-09-01

### Changed

- **the repository is `ddlc-themes` now** — it stopped being terminal-only two applications ago. GitHub redirects the old URLs; the overlay attribute (`pkgs.ddlc-themes`), the package's `share/ddlc-themes/` path and the recommended flake input name follow the new name, which is the breaking half of the rename
- `install.sh` reworked onto the [huix-standard](https://github.com/rokokol/huix-standard) grammar, adapted to a config tree: `-h`/`-v` short flags, a preflight that installs nothing and prints exact per-distro guidance, and an install manifest at `~/.config/ddlc-themes/install-manifest`. Components stay additive, and re-running one sweeps its own stale files only

### Added

- `VERSION` at the repo root as the one source of version: the package reads it, `install.sh -v|--version` prints it, CI asserts the changelog heading matches
- `./install.sh --uninstall` removes an install by its manifest — `--uninstall --component btop` takes a single application's themes out and keeps the rest; installs made before the manifest existed fall back to the known layout for this one release
- tab completion for the installer, `source completions/install.sh.{bash,zsh}`, drift-checked against `install.sh` by `tests/check-completions.sh`
- `tests/run.sh` — the installer's contract as a fast suite, also run by `nix flake check`: manifest, per-component sweep, selective uninstall, staging, the refusal path per distro
- `tests/distro.sh` — the full preflight→guidance→install→uninstall cycle inside real `debian`, `ubuntu`, `arch` and `fedora` containers, with four per-distro CI badges (push, weekly cron, never pull requests)

- matplotlib styles and colormaps — `ddlc.mplstyle`, `ddlc-dark.mplstyle` and `ddlc_cmaps.py`, moved over from [rokokol/huix](https://github.com/rokokol/huix) so the theme ships with the family instead of living in one rice; the light cycler's order is its colour-blind safety mechanism and the dark one is three colours because the palette is polarised. `docs/matplotlib-demo.py` renders the demo figures the README shows
- Claude Code themes, `ddlc-claude-code-{dark,light}.json` for `~/.claude/themes/` — the dark leans into the slots ddlc.nvim draws from base16 dark, blush text and neon pink frames, the light sits on the colours that actually read on paper, and every foreground slot is contrast-checked against its own ground
- `ddlc-report.css` — the matplotlib theme spoken in CSS for HTML reports: one file, light by default, dark under `prefers-color-scheme` with `data-theme` winning, the series as `--ddlc-series-*` custom properties; `docs/report-demo.html` renders the README screenshots
- an opencode theme, `ddlc-opencode.json` — one file for both variants, its `defs` carrying the palette by name so the mapping stays readable in place
- `generate.sh` takes the flat `palette.env` as a third input, because these three themes have more roles than sixteen base16 slots
- module switches `matplotlib.enable`, `claude-code.enable` and `opencode.enable`, deploy-only and variant-less — each application picks its own variant, and none of the switches touches the application's config
- `install.sh` components `matplotlib`, `claude-code` and `opencode`, with `--claude-home` for the one application that reads outside `~/.config`

### Changed

- `install.sh` accepts a staging `DESTDIR` and a `kitty|btop|all` component while retaining the short `--kitty` and `--btop` forms

## [1.0.0] - 2026-08-13

Split out of [rokokol/huix](https://github.com/rokokol/huix), where the kitty and btop generators were two hundred lines inside `ddlc-palette`'s `generate.sh`

### Added

- kitty and btop themes, light and dark, rendered from the base16 schemes in `ddlc-palette`
- `dist/`, committed for consumers without Nix, and `install.sh` that places btop's theme under the name it is found by
- `homeModules.default`, `overlays.default`
- checks: `dist/` is current, every slot is filled, the module wires both applications up and touches neither while disabled
- a weekly `palette-drift.yml` that re-renders against the palette's HEAD rather than the lock
