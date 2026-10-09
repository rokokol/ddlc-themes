# Changelog

Kept in the shape of [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), versioned by [semver](https://semver.org/spec/v2.0.0.html)

## Unreleased

### Added

- kind roles that colour a note by its kind, as an Obsidian callout type does: `--ddlc-kind-note`, `-summary`, `-tip`, `-success`, `-warning`, `-danger`, `-example`, `-quote` and `-experiment`, each in its own hue
- Nunito in `dist/` as `Nunito.woff2` and `Nunito-Italic.woff2`, every script and weight, with its licence (`lib.nunito`)
- the faces `--ddlc-font-heading` and a `heading` face in the letter styles
- Departure Mono with the Nerd Fonts icons in `dist/` as `DepartureMonoNerdFontMono-Regular.woff2`, with the font's licence and the icon sets' licences beside it (`lib.nerd`)

### Changed

- the weekly lock bump renders `dist/` again from the new inputs and lands both together, so a new palette, fonttools or Nerd Fonts archive reaches `dist/` without a hand. A colour that moved upstream now lands this way too, and `palette-drift.yml`, which opened a pull request for it, is removed
- a link takes the new roles `--ddlc-link` and `--ddlc-link-live`: on ink it is blush and turns paper under the pointer, brighter than the accent's pink was; on paper it stays plum
- **the prose face is Nunito**, Medium in the report with bold in Black, instead of Doki. The report stylesheet now expects `Nunito.woff2` and `Nunito-Italic.woff2` beside it. A heading is Doki where it is installed and Nunito Black otherwise; Doki is personal-use only and not shipped
- a letter falls back from Nunito to the reader's system face, Segoe UI, Roboto or Helvetica, instead of Georgia
- matplotlib draws in Nunito instead of its default DejaVu Sans. It cannot pick a weight from a variable font, so the text is Nunito's thin default weight, and a chart's title is no longer bold
- the web kit keeps the brand's mark and the gaps in the bar on a phone; it no longer hides them under 480 px
- the web kit draws a checkbox itself, as a square frame with the switch's knob in it when it is on, instead of the browser's rounded box in the accent colour
- the report's "Just Monika." pop-up centres a list or a table as one block with its own left edge inside, so a list's markers stand in one column, and keeps a code block's left edge

## [3.0.0] - 2026-10-08

### Added

- `ddlc-ui.css`, a web kit drawn on the Departure Mono grid: the bar, a three-column layout of tools, stage and readouts, cards, buttons, switches, fields, meters, dialogs and a toast, both variants in one file (`lib.ui`)
- `ddlc-theme.js`, a theme button that cycles system, light and dark, and `ddlc-cloud.js`, the pointer's dithered cloud with a colour reader and the dithering for a canvas (`lib.js.theme`, `lib.js.cloud`)
- Departure Mono 1.500 in `dist/`, beside the kit that reads it (`lib.font`)
- `ddlc-mail.json`, the light colours, the faces and ready `style` values for an HTML letter, which cannot use `var()` (`lib.mail`)
- `ddlc-tokens.css`, the roles alone for a theme with its own palette and selectors (`lib.tokens`)
- `ddlc-syntax.json`, one table of syntax colours per variant for every editor theme (`lib.syntax`)
- a flake template, `nix flake init -t github:rokokol/ddlc-themes#app`, with the bar, the three columns and the cards
- `docs/ui-demo.html`, every class of the kit on one page

### Changed

- **Breaking:** the report stylesheet's roles are renamed and recomputed from the shared role table. `--ddlc-ink` is now `--ddlc-text`, `--ddlc-divider` is `--ddlc-line`, and `--ddlc-inform-ground` and `--ddlc-inform-border` are `--ddlc-popup-ground` and `--ddlc-popup-frame`. A role no longer takes the name of a palette colour, so the stylesheet no longer repaints `--ddlc-ink` when `palette.css` is linked beside it
- **Breaking:** the report stylesheet's tokens are no longer hex literals but `light-dark()` over the palette. A letter that parsed them reads `ddlc-mail.json` instead
- the report stylesheet: muted text is 55% ink over the jacket on paper and 75% jacket over the paper on ink, so it reads at 6.7:1 rather than 2.55:1 on paper
- the report stylesheet: prose sets in Doki, a code block is a dark kitty window with a prompt and its `data-lang` in a title bar, `.ddlc-inform` is the "Just Monika." pop-up with an optional `.ddlc-inform-title`, and a quote is a note taped onto the page
- opencode: the syntax and markdown colours come from the shared syntax table. Variables, operators and punctuation take the text colour, and in light comments and quotes are the muted mix and types are `rule`

## [2.1.0] - 2026-09-29

### Changed

- kitty light: the cursor, links, the active border and the active tab are `plum`, the colour of the site's links and download button; the dark variant is unchanged

### Fixed

- kitty light: bright black (`color8`) is `jacket`, not `natsuki`, so shell suggestions and dimmed output no longer vanish on paper
- Claude Code: Clawd's eyes take the terminal background (`paper` in light, `ink` in dark), so they no longer show as a framed pale block on the light theme
- Claude Code light: the changed-word highlight in a diff is now the light `monikaEye` and `monika`, not the dark `ribbon` and `bowShadow`, so the syntax theme's dark text on it reads
- Claude Code: the selection is a cold blue in both variants (`sayoriEye` in light, `skirt` in dark), and no longer shares its colour with the hovered user message or sinks into the theme's pinks
- opencode light: added diff lines have a pale green background (20% of `monikaEye` over `paper`) and removed ones `natsuki`, so a diff no longer shows its lines alike on the pink tool panel

## [2.0.2] - 2026-09-21

### Changed

- `install.sh` now exits 2, not 1, on a usage error — an unknown flag, a relative `--config-home`/`--claude-home`, or an unknown `--component` — and `--help` ends with the `Exit` sentence naming every code it can produce; a missing dependency in the preflight still exits 1
- the installer's completions are now drift-checked against `install.sh` by the vendored [bash-best-practices](https://github.com/rokokol/bash-best-practices-skill) `check-sh.sh -c`, replacing `tests/check-completions.sh`
- `install.sh --help` says once, not twice, that components are additive and that `--uninstall --component` takes one out on its own: the paragraph about re-running a component already carried it
- `generate.sh --help` no longer repeats its own title line, and says instead that it writes `dist/`, which is committed for consumers without Nix
- `generate.sh` and `install.sh` move their header's caller-facing paragraph into `--help`, leaving the header to editor-only notes. `tests/run.sh -h|--help|help` now documents the suite, including that it reaches no network

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
