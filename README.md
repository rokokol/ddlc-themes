<div align="center">

# ddlc-themes

**The Doki Doki Literature Club colours for kitty, btop, matplotlib, Claude Code, opencode and your reports, light and dark** （´ω｀♡%）

![kitty](https://img.shields.io/badge/kitty-theme-72D0FA?style=flat)
![btop](https://img.shields.io/badge/btop-theme-76C332?style=flat)
![matplotlib](https://img.shields.io/badge/matplotlib-theme-BB5599?style=flat)
![Claude Code](https://img.shields.io/badge/Claude_Code-theme-F1A796?style=flat)
![opencode](https://img.shields.io/badge/opencode-theme-DD77BB?style=flat)
![Nix](https://img.shields.io/badge/Nix-flake-7EBAE4?style=flat&logo=nixos&logoColor=white)
[![palette](https://img.shields.io/badge/colours-ddlc--palette-FF80C0?style=flat)](https://github.com/rokokol/ddlc-palette)
[![assets](https://img.shields.io/badge/assets-Team_Salvato-FF80C0?style=flat)](ASSETS.md)
[![license](https://img.shields.io/badge/code-MIT-3DA639?style=flat)](LICENSE)
[![build](https://github.com/rokokol/ddlc-themes/actions/workflows/build.yml/badge.svg)](https://github.com/rokokol/ddlc-themes/actions/workflows/build.yml)
[![debian](https://github.com/rokokol/ddlc-themes/actions/workflows/distro-debian.yml/badge.svg)](https://github.com/rokokol/ddlc-themes/actions/workflows/distro-debian.yml)
[![ubuntu](https://github.com/rokokol/ddlc-themes/actions/workflows/distro-ubuntu.yml/badge.svg)](https://github.com/rokokol/ddlc-themes/actions/workflows/distro-ubuntu.yml)
[![arch](https://github.com/rokokol/ddlc-themes/actions/workflows/distro-arch.yml/badge.svg)](https://github.com/rokokol/ddlc-themes/actions/workflows/distro-arch.yml)
[![fedora](https://github.com/rokokol/ddlc-themes/actions/workflows/distro-fedora.yml/badge.svg)](https://github.com/rokokol/ddlc-themes/actions/workflows/distro-fedora.yml)

</div>

Themes for five applications and a report stylesheet, rendered out of [ddlc-palette](https://github.com/rokokol/ddlc-palette), which measures every colour off [ddlc.moe](https://ddlc.moe) rather than eyeballing it. kitty and btop read the base16 schemes; the rest have more roles than sixteen slots, so their tables name palette colours directly. Nothing here is a taste call except which slot goes where

Came over from my rice, **[rokokol/huix](https://github.com/rokokol/huix)**

```sh
# render nothing, install nothing, just look
nix build github:rokokol/ddlc-themes && cat result/share/ddlc-themes/ddlc-kitty-dark.conf
```

## Contents

- [What it looks like](#what-it-looks-like)
- [Install](#install)
  - [Home Manager](#home-manager)
  - [Any other distribution](#any-other-distribution)
- [Where the slots go](#where-the-slots-go)
- [Re-rendering](#re-rendering)
- [Tests](#tests)
- [Layout](#layout)

## What it looks like

![kitty running fastfetch and a directory listing](docs/screenshot-kitty.png)

![btop, all four panels](docs/screenshot-btop.png)

> The wallpaper comes through because kitty runs at `background_opacity 0.9` — neither theme sets an opacity of its own, and btop simply inherits the terminal's

![opencode](docs/opencode.png)

| ![the matplotlib demo figure, light variant](docs/matplotlib-light.png) | ![the matplotlib demo figure, dark variant](docs/matplotlib-dark.png) |
| ----------------------------------------------------------------------- | --------------------------------------------------------------------- |

> [`docs/matplotlib-demo.py`](docs/matplotlib-demo.py) renders both: the cycler on lines and bars — five series on paper, three on ink, which is the theme's own statement — and the two colormap families on the heatmaps

| ![the report stylesheet, light variant](docs/report-light.png) | ![the report stylesheet, dark variant](docs/report-dark.png) |
| -------------------------------------------------------------- | ------------------------------------------------------------ |

> [`docs/report-demo.html`](docs/report-demo.html) is the page behind these — open it from the checkout and pin a variant with `?theme=dark`

## Install

### Home Manager

```nix
{
  inputs.ddlc-themes.url = "github:rokokol/ddlc-themes";

  # in your home configuration
  imports = [ inputs.ddlc-themes.homeManagerModules.default ];

  ddlc.kitty.enable = true;
  ddlc.btop.enable = true;
  ddlc.matplotlib.enable = true;
}
```

One switch per application, because each is wired up differently and the wiring is the half that goes wrong:

| option               | what it does                                                                                                           | default |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------- | ------- |
| `kitty.enable`       | the colours into `kitty.conf`, after your own settings — kitty takes the last word for a key                           | `false` |
| `kitty.variant`      | `light` or `dark`                                                                                                      | `dark`  |
| `btop.enable`        | both themes into `~/.config/btop/themes/` and one of them named in `btop.conf`                                         | `false` |
| `btop.variant`       | which one is named. The other is deployed anyway — btop lists that directory, so it is a keypress away in its own menu | `dark`  |
| `matplotlib.enable`  | both styles into `~/.config/matplotlib/stylelib/` and the colormaps module next to them                                | `false` |
| `claude-code.enable` | both themes into `~/.claude/themes/`, where `/theme` lists them as `ddlc-dark` and `ddlc-light`                        | `false` |
| `opencode.enable`    | the one file into `~/.config/opencode/themes/` — it carries both variants itself                                       | `false` |

The last three have no `variant`: each application picks its own — matplotlib names a style per chart, Claude Code lists its themes directory in `/theme`, opencode reads the variant out of the file by the terminal's background. None of them touches the application's own config, so the selection stays yours; and a declaratively deployed theme is a read-only store link, so if you would rather keep the files editable in place, skip the switch and use `install.sh` below — it copies plain files

**Without the module.** `lib.kitty.{light,dark}`, `lib.btop.{light,dark}`, `lib.matplotlib.{light,dark,cmaps}`, `lib.claude-code.{light,dark}`, `lib.opencode` and `lib.report` are paths, so `readFile` or a `source =` places them yourself; `packages.default` lays the same files under `share/ddlc-themes/`

The report stylesheet has no switch at all: it belongs next to a report, not in `~/.config`, so copy `dist/ddlc-report.css` (or take `lib.report`) and `<link>` it — one file carries both variants, light by default, dark under `prefers-color-scheme`, an explicit `data-theme="dark|light"` winning over both

### Any other distribution

```sh
git clone https://github.com/rokokol/ddlc-themes
cd ddlc-themes
./install.sh              # --component kitty|btop|matplotlib|claude-code|opencode for one of them
```

Nothing is built: [`dist/`](dist) is committed, so this is a copy into `~/.config` — except the Claude Code themes, which land in `~/.claude/themes/` because that is where the application looks (`--claude-home` moves it). kitty gets both variants next to `kitty.conf`, where `include ddlc-kitty-dark.conf` resolves; matplotlib keeps its filenames, because they are the API — `plt.style.use("ddlc")`, `import ddlc_cmaps`. The rest list a theme under its file name, so the app segment is dropped on the way in: `ddlc-btop-dark.theme` lands as `ddlc-dark.theme`, the Claude Code pair as `ddlc-dark.json` and `ddlc-light.json`, and `ddlc-opencode.json` as `ddlc.json`

Nothing is ever installed behind your back: the script needs only coreutils, and if even that is missing it names what and how to get it, exactly, for your distribution. The applications being themed are not dependencies — a warning if one is absent, and the theme installs anyway

Every path written is recorded in `~/.config/ddlc-themes/install-manifest`, so the install is reversible, per component or whole:

```sh
./install.sh --uninstall --component btop   # take one application's themes out
./install.sh --uninstall                    # take everything out
```

Components are additive — installing one never touches another — but re-running one converges it: a file a previous install of that component wrote and this run does not is swept away

Tab completion for the installer's own flags is sourced from the checkout:

```sh
source completions/install.sh.bash   # bash
source completions/install.sh.zsh   # zsh
```

Package recipes can stage another config root without duplicating the layout: `DESTDIR="$pkgdir" ./install.sh --config-home /usr/share/ddlc-themes`. Add `--component kitty` or `--component btop` for split packages

## Where the slots go

kitty follows [tinted-kitty](https://github.com/tinted-theming/tinted-kitty) slot for slot with one departure: that template grounds the selection in `base03`, which leaves `base05` on it at 1.65:1 here, so `base02` carries it instead

btop has no base16 template anywhere upstream, so its mapping is this repository's own:

| group  | how it is coloured                                                                                                                                        |
| ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| boxes  | `cpu_box` blue, `mem_box` green, `net_box` magenta, `proc_box` cyan — four accents, so a glance lands in the right panel                                  |
| load   | temperature, CPU and process gradients rise through the palette's warm accents: green, then yellow, then red                                              |
| meters | free, cached, available, used, download and upload carry no scale, so each is one colour with an empty mid and end, which is how btop spells a flat meter |

The report stylesheet is the matplotlib theme spoken in CSS: the same grounds and inks, rules between table rows only — the grid stays under the data — and the same series as custom properties, five on paper, three on ink (in dark, `--ddlc-series-4` and `-5` collapse into the muted grey — a tail that was not folded into the remaining three stays visible but stops pretending to be a series). Links are plum with a pink hover and dividers are blush, because that is what the site itself does

matplotlib's light cycler runs `plum, bow, rule, monikaEye, yuri`, and the order is the safety mechanism rather than a taste: adjacent entries are what a stacked bar or a multi-line chart puts side by side, and each neighbour pair clears deuteranopia and protanopia simulation by a measured OKLab distance. The dark cycler is three colours, not five — everything else either leaves the dark lightness band or falls under 3:1 on `ink`. `import ddlc_cmaps` adds four colormaps (and their `_r` reversals): sequential runs one hue toward the foreground of its ground, diverging is two one-hue arms about the only grey in it

Claude Code and opencode sit on the palette's named colours with the contrast checked per slot against the variant's own ground: the body text is `dot` on dark (12.6:1 on `ink`) and `yuriShadow` on light (15.3:1) rather than a saturated pink — the pinks are accents there, not the page — and the rest spreads across the palette: `sayoriEye` for permissions, `monikaEye` and `ribbon` for success, the blues for links and syntax, `bow` for errors. The light variants leave the added-diff background to the base theme (Claude Code) or the terminal (opencode), because the site ships no light green

> [!NOTE]
> The two variants draw different accents, because the palette is polarised — a colour that reads on `ink` is a pastel on `paper`. For kitty and btop the [slot table](https://github.com/rokokol/ddlc-palette#as-a-theme) in ddlc-palette says which palette key fills which base16 slot; for the other three the tables sit in `generate.sh` itself

## Re-rendering

`generate.sh` reads the two base16 yamls and the flat `palette.env`, and writes `dist/`. The devShell puts all three in the environment:

```sh
nix develop -c ./generate.sh
./generate.sh --light base16-ddlc-light.yaml --dark base16-ddlc-dark.yaml \
  --palette palette.env   # without Nix
```

The colours come from ddlc-palette and nothing else does — the palette is measured, this repository is only a mapping. A weekly workflow re-renders against the palette's HEAD rather than the lock and opens a pull request when they part ways, so a colour cannot move upstream and quietly leave this dark

## Tests

`nix flake check` proves that `dist/` is what `generate.sh` writes today, that every value in it is a hex colour the palette actually holds (down to every opencode reference resolving against its `defs`), that the module wires every application up (and touches none while disabled), that every shell file passes shellcheck and shfmt with the completions in step with `install.sh`, and it runs `tests/run.sh` — the installer's whole contract: manifest, per-component sweep, selective uninstall, staging, the refusal path

`tests/distro.sh <distro>` (needs docker or podman) runs the full cycle inside a real `debian`, `ubuntu`, `arch` or `fedora` container: preflight, its printed guidance run verbatim, install, selective uninstall, uninstall. In CI that is the four distro badges — on push, weekly against `:latest`, never on pull requests

## Layout

```
generate.sh   the mapping: base16 slots and palette colours in, the themes out
nix/          module.nix, module-test.nix
dist/         the rendered themes, committed for consumers without Nix
install.sh    for systems without Nix; VERSION is the one source of version
completions/  tab completion for install.sh, sourced from the checkout
check-sh.sh   vendored from bash-best-practices, holds install.sh's help
              and completions to its parser
tests/        run.sh (fast, sandboxed), distro.sh (containers)
```
