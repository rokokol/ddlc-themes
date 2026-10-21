<div align="center">

# ddlc-themes

**The Doki Doki Literature Club colours for kitty, btop, matplotlib, Claude Code, opencode, Super Productivity, your web pages, reports and letters, light and dark** （´ω｀♡%）

![kitty](https://img.shields.io/badge/kitty-theme-72D0FA?style=flat)
![btop](https://img.shields.io/badge/btop-theme-76C332?style=flat)
![matplotlib](https://img.shields.io/badge/matplotlib-theme-BB5599?style=flat)
![Claude Code](https://img.shields.io/badge/Claude_Code-theme-F1A796?style=flat)
![opencode](https://img.shields.io/badge/opencode-theme-DD77BB?style=flat)
![Super Productivity](https://img.shields.io/badge/Super_Productivity-theme-FFBDE1?style=flat)
![Nix](https://img.shields.io/badge/Nix-flake-7EBAE4?style=flat&logo=nixos&logoColor=white)
[![FlakeHub](https://img.shields.io/endpoint?url=https://flakehub.com/f/rokokol/ddlc-themes/badge)](https://flakehub.com/flake/rokokol/ddlc-themes)
[![palette](https://img.shields.io/badge/colours-ddlc--palette-FF80C0?style=flat)](https://github.com/rokokol/ddlc-palette)
[![assets](https://img.shields.io/badge/assets-Team_Salvato-FF80C0?style=flat)](ASSETS.md)
[![license](https://img.shields.io/badge/code-MIT-3DA639?style=flat)](LICENSE)
[![fonts](https://img.shields.io/badge/fonts-OFL_1.1-3DA639?style=flat)](ASSETS.md#fonts)
[![build](https://github.com/rokokol/ddlc-themes/actions/workflows/build.yml/badge.svg)](https://github.com/rokokol/ddlc-themes/actions/workflows/build.yml)
[![debian](https://github.com/rokokol/ddlc-themes/actions/workflows/distro-debian.yml/badge.svg)](https://github.com/rokokol/ddlc-themes/actions/workflows/distro-debian.yml)
[![ubuntu](https://github.com/rokokol/ddlc-themes/actions/workflows/distro-ubuntu.yml/badge.svg)](https://github.com/rokokol/ddlc-themes/actions/workflows/distro-ubuntu.yml)
[![arch](https://github.com/rokokol/ddlc-themes/actions/workflows/distro-arch.yml/badge.svg)](https://github.com/rokokol/ddlc-themes/actions/workflows/distro-arch.yml)
[![fedora](https://github.com/rokokol/ddlc-themes/actions/workflows/distro-fedora.yml/badge.svg)](https://github.com/rokokol/ddlc-themes/actions/workflows/distro-fedora.yml)

</div>

Themes for the applications above, a web kit, a report stylesheet and the styles for HTML letters, rendered out of [ddlc-palette](https://github.com/rokokol/ddlc-palette). The palette measures every colour off [ddlc.moe](https://ddlc.moe) rather than eyeballing it. kitty and btop read the base16 schemes. The rest have more roles than sixteen slots, so their tables name palette colours directly. Nothing here is a taste call except which slot goes where

Everything that is not a terminal reads one table of roles and one table of syntax colours. So a muted caption, a link or a keyword is the same colour in a web page, a report, a letter, opencode, [ddlc.nvim](https://github.com/rokokol/ddlc.nvim) and the [Obsidian theme](https://github.com/rokokol/ddlc-obsidian-theme)

Came over from my rice, **[rokokol/huix](https://github.com/rokokol/huix)**

```sh
# render nothing, install nothing, just look
nix build github:rokokol/ddlc-themes && cat result/share/ddlc-themes/ddlc-kitty-dark.conf
```

## Contents

- [What it looks like](#what-it-looks-like)
- [In use](#in-use)
- [Install](#install)
  - [Home Manager](#home-manager)
  - [Any other distribution](#any-other-distribution)
  - [Super Productivity](#super-productivity)
- [Web pages, reports and letters](#web-pages-reports-and-letters)
- [Where the slots go](#where-the-slots-go)
- [Re-rendering](#re-rendering)
- [Tests](#tests)
- [Layout](#layout)

## What it looks like

![the web kit, light variant](docs/ui-light.png)

![the web kit, dark variant](docs/ui-dark.png)

> [`docs/ui-demo.html`](docs/ui-demo.html) is the page behind these, with every class of the kit. Serve the checkout over HTTP, because a browser does not load the kit's scripts from a file, and pin a variant with `?theme=dark`

| ![the report stylesheet, light variant](docs/report-light.png) | ![the report stylesheet, dark variant](docs/report-dark.png) |
| -------------------------------------------------------------- | ------------------------------------------------------------ |

> [`docs/report-demo.html`](docs/report-demo.html) is the page behind these. Open it from the checkout and pin a variant with `?theme=dark`

| ![the matplotlib demo figure, light variant](docs/matplotlib-light.png) | ![the matplotlib demo figure, dark variant](docs/matplotlib-dark.png) |
| ----------------------------------------------------------------------- | --------------------------------------------------------------------- |

> [`docs/matplotlib-demo.py`](docs/matplotlib-demo.py) renders both: the cycler on lines and bars — five series on paper, three on ink, which is the theme's own statement — and the two colormap families on the heatmaps


![kitty running fastfetch and a directory listing](docs/screenshot-kitty.png)

![btop, all four panels](docs/screenshot-btop.png)

> The wallpaper comes through because kitty runs at `background_opacity 0.9` — neither theme sets an opacity of its own, and btop simply inherits the terminal's

![opencode](docs/opencode.png)

| ![Super Productivity, light variant](docs/super-productivity-light.png) | ![Super Productivity, dark variant](docs/super-productivity-dark.png) |
| ----------------------------------------------------------------------- | --------------------------------------------------------------------- |

> Super Productivity over the polka-dot paper as a project's background image: a task is a card, a done one sinks back to its own colour until the pointer is on it, a banner is the "Just Monika." pop-up and a notice is a small kitty window. [`docs/super-productivity-demo.py`](docs/super-productivity-demo.py) takes both from the app's web build in a fresh profile: `nix run .#sp-demo` on Linux, after `dist/` is rendered

## In use

- [bitmap.rokokol.art](https://bitmap.rokokol.art) ([source](https://github.com/rokokol/easy-bitmap)): an editor for 1-bit pictures on Arduino displays, drawn with the web kit
- [fly.rokokol.art](https://fly.rokokol.art) ([source](https://github.com/rokokol/fly-vs-cybersafe-lct2026)): an interactive page where a fly smells its way to a safe's PIN, drawn with the web kit
- [ddlc-obsidian-theme](https://github.com/rokokol/ddlc-obsidian-theme): an Obsidian theme on the same roles

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

**Without the module.** `lib.kitty.{light,dark}`, `lib.btop.{light,dark}`, `lib.matplotlib.{light,dark,cmaps}`, `lib.claude-code.{light,dark}` and `lib.opencode` are paths, so `readFile` or a `source =` places them yourself; `packages.default` lays the same files under `share/ddlc-themes/`. The files for pages, reports and letters are paths too, see [below](#web-pages-reports-and-letters)

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

### Super Productivity

Super Productivity keeps a theme inside its own storage rather than in a file, so neither the module nor `install.sh` places it. Upload [`dist/ddlc-super-productivity.css`](dist/ddlc-super-productivity.css), which every [release](https://github.com/rokokol/ddlc-themes/releases/latest) also carries, with "Install theme" in the theme section of its settings and select it there; it follows the app's own dark mode switch. The app loads nothing a theme names, so the faces are the ones installed on the system: Mya Nunito or Nunito for the prose and Departure Mono for a notice, each with a system fallback

For the polka-dot paper behind the tasks, pick the screen-sized WebP of the variant as a project's background image in that project's settings. The GIF of the same screen is larger than the app takes from a file

## Web pages, reports and letters

These have no switch and no installer, because they belong next to a page and not in `~/.config`. Copy them out of `dist/` or a release's files, take them from `lib` in the flake, or vendor them at a pinned commit:

| file | for | in the flake |
| --- | --- | --- |
| `ddlc-ui.css` | a web page or a small app: the bar, three columns of tools, stage and readouts, cards, buttons, switches, fields, meters, dialogs | `lib.ui` |
| `ddlc-theme.js`, `ddlc-cloud.js` | the theme button that cycles system, light and dark; the pointer's dithered cloud and the colour reader for a canvas | `lib.js.{theme,cloud}` |
| `DepartureMono-Regular.woff2` | the face the kit is drawn in, expected beside `ddlc-ui.css` | `lib.font` |
| `ddlc-report.css` | an HTML report: prose, tables, code as a kitty window, the "Just Monika." pop-up, quotes taped on | `lib.report` |
| `MyaNunito.woff2`, `MyaNunito-Italic.woff2` | the prose face of a report, expected beside `ddlc-report.css`: Mya Nunito, which is Nunito with the Greek, arrows, operators, blackboard letters and indices it lacks, drawn from Noto Sans and Noto Sans Math at its size and along its weight axis, without closing the openings between their strokes and spaced alike at every weight, as Nunito's own signs are. A heading takes Doki where it is installed and Mya Nunito Black otherwise. Its licence, the OFL with the notices of all three fonts, is `MyaNunito-LICENSE.txt` beside it | `lib.mya-nunito.{regular,italic}` |
| `MyaNunito.ttf`, `MyaNunito-Italic.ttf` | Mya Nunito for the system, variable as on a page | `lib.mya-nunito.ttf.{regular,italic}` |
| `MyaNunitoStatic-{Regular,Medium,Bold,Black}.ttf` and their `Italic`, `MediumItalic`, `BoldItalic`, `BlackItalic` | Mya Nunito at fixed weights, as a family of its own, Mya Nunito Static, so a system holding both sees each once: for matplotlib, which reads no variation axis and draws a variable font at its lightest. The matplotlib styles name it for text and formulas alike | `lib.mya-nunito.static.{regular,medium,bold,black,italic,medium-italic,bold-italic,black-italic}` |
| `Nunito.woff2`, `Nunito-Italic.woff2` | Nunito as it comes, for a page that wants it without the additions | `lib.nunito.{regular,italic}` |
| `DepartureMonoNerdFontMono-Regular.woff2` | Departure Mono with the [Nerd Fonts](https://www.nerdfonts.com) icons, for code that shows them; its licences are the two `DepartureMonoNerdFont-*` files beside it | `lib.nerd` |
| `ddlc-mail.json` | an HTML letter: the light colours, the faces and ready values for `style` attributes | `lib.mail` |
| `ddlc-tokens.css` | a theme that brings its own palette and selectors: the roles alone | `lib.tokens` |
| `ddlc-syntax.json` | an editor theme: the syntax colours per variant | `lib.syntax` |
| `ddlc-roles.json` | a theme without CSS: every role as a hex per variant, and the grid and the drift of the game menu's polka-dot paper, which CSS reads as `--ddlc-polka-*` | `lib.roles` |
| `ddlc-polka-{dark,light}{,-2x,-1920x1080}.gif`, `ddlc-polka-{dark,light}-1920x1080.webp` | a surface that takes a picture rather than CSS: the polka-dot paper drifting in a loop, as a tile that repeats and as a whole screen for a surface that stretches its picture to cover. The screen's WebP holds the same pixels as its GIF at a fraction of the size, for an app that caps a picture's size | `lib.polka.{dark,light}.{tile,tile-2x,screen,screen-webp}` |

Each stylesheet is one `<link>` and carries both variants: it follows the system until `data-theme="light|dark"` on `<html>` pins a side. A colour in a page's own rules comes from a `--ddlc-*` role, so it follows both sides too

A letter gets literal styles because Gmail drops any declaration that carries `var()`:

```python
mail = json.load(open(os.environ["DDLC_MAIL"]))
S = mail["styles"]
html = f'<div style="{S["page"]}"><h1 style="{S["h1"]}">Weekly report</h1></div>'
```

A new page starts from the template, which lays out the bar, the three columns and the cards and says how to vendor the kit into it:

```sh
nix flake init -t github:rokokol/ddlc-themes#app
```

## Where the slots go

kitty follows [tinted-kitty](https://github.com/tinted-theming/tinted-kitty) slot for slot with one departure: that template grounds the selection in `base03`, which leaves `base05` on it at 1.65:1 here, so `base02` carries it instead

btop has no base16 template anywhere upstream, so its mapping is this repository's own:

| group  | how it is coloured                                                                                                                                        |
| ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| boxes  | `cpu_box` blue, `mem_box` green, `net_box` magenta, `proc_box` cyan — four accents, so a glance lands in the right panel                                  |
| load   | temperature, CPU and process gradients rise through the palette's warm accents: green, then yellow, then red                                              |
| meters | free, cached, available, used, download and upload carry no scale, so each is one colour with an empty mid and end, which is how btop spells a flat meter |

The roles are one table in `generate.sh`, and every stylesheet, the letters and the Obsidian theme read it. A role never takes the name of a palette colour, so a page can link `palette.css` beside a stylesheet from here. Links are plum with a pink hover and dividers are blush, because that is what the site itself does. Muted text mixes the jacket with the ink, because the bare jacket is too faint to read on paper. The series continue the matplotlib cycler: five on paper and three on ink, where `--ddlc-series-4` and `-5` collapse into the muted grey, so a tail that was not folded into the three stays visible but stops pretending to be a series

The syntax table holds ddlc.nvim's groups. Every colour in it reads at least 3:1 on its own ground, so a slot that does not is replaced in that variant, and `generate.sh` refuses a table that breaks the rule. opencode, ddlc.nvim and the code window of the report and the Obsidian theme all take their syntax colours from it

matplotlib's light cycler runs `plum, bow, rule, monikaEye, yuri`, and the order is the safety mechanism rather than a taste: adjacent entries are what a stacked bar or a multi-line chart puts side by side, and each neighbour pair clears deuteranopia and protanopia simulation by a measured OKLab distance. The dark cycler is three colours, not five — everything else either leaves the dark lightness band or falls under 3:1 on `ink`. `import ddlc_cmaps` adds four colormaps (and their `_r` reversals): sequential runs one hue toward the foreground of its ground, diverging is two one-hue arms about the only grey in it

Claude Code and opencode sit on the palette's named colours with the contrast checked per slot against the variant's own ground: the body text is `dot` on dark (12.6:1 on `ink`) and `yuriShadow` on light (15.3:1) rather than a saturated pink — the pinks are accents there, not the page — and the rest spreads across the palette: `sayoriEye` for permissions, `monikaEye` and `ribbon` for success, the blues for links, `bow` for errors, and the syntax table for code. The light variants leave the added-diff background to the base theme (Claude Code) or the terminal (opencode), because the site ships no light green

> [!NOTE]
> The two variants draw different accents, because the palette is polarised — a colour that reads on `ink` is a pastel on `paper`. For kitty and btop the [slot table](https://github.com/rokokol/ddlc-palette#as-a-theme) in ddlc-palette says which palette key fills which base16 slot; for the other three the tables sit in `generate.sh` itself

## Re-rendering

`generate.sh` reads the two base16 yamls and the flat `palette.env`, and writes `dist/`. It also assembles the stylesheets and scripts out of `src/`, copies the vendored fonts and merges Mya Nunito out of them. The devShell puts all three inputs in the environment:

```sh
nix develop -c ./generate.sh
./generate.sh --light base16-ddlc-light.yaml --dark base16-ddlc-dark.yaml \
  --palette palette.env   # without Nix
```

The colours come from ddlc-palette and nothing else does — the palette is measured, this repository is only a mapping. A weekly workflow takes the palette's HEAD with every other input, renders `dist/` again in the same commit and lands it on green, so a colour cannot move upstream and quietly leave this dark

## Tests

`nix flake check` proves that `dist/` is what `generate.sh` writes today, that every value in it is a hex colour the palette actually holds (down to every opencode reference resolving against its `defs`, and every letter style holding no `var()`), that the polka-dot GIFs show the paper `ddlc-roles.json` describes and loop with no seam, that Mya Nunito keeps every glyph and the weight axis of Nunito while its added glyphs cover the mathematical blocks, stand at Nunito's x-height and grow heavier with the weight, that every component, class and variable the Super Productivity theme hooks into still exists in that app's source at the locked version, that the module wires every application up (and touches none while disabled), that every shell file passes shellcheck and shfmt with the completions in step with `install.sh`, and it runs `tests/run.sh` — the installer's whole contract: manifest, per-component sweep, selective uninstall, staging, the refusal path

`tests/distro.sh <distro>` (needs docker or podman) runs the full cycle inside a real `debian`, `ubuntu`, `arch` or `fedora` container: preflight, its printed guidance run verbatim, install, selective uninstall, uninstall. In CI that is the four distro badges — on push, weekly against `:latest`, never on pull requests

## Layout

```
generate.sh   the mapping: base16 slots and palette colours in, the themes out
src/          the web kit, the report stylesheet, the scripts, the GIF drawer and the Mya Nunito merger, by hand
vendor/       Departure Mono, Nunito, Noto Sans and Noto Sans Math, kept byte-equal to their sources by vendor-sync.sh
templates/    the page `nix flake init -t` starts from
nix/          module.nix, module-test.nix
dist/         the rendered themes, committed for consumers without Nix
install.sh    for systems without Nix; VERSION is the one source of version
completions/  tab completion for install.sh, sourced from the checkout
check-sh.sh   vendored from bash-best-practices, holds install.sh's help
              and completions to its parser
tests/        run.sh (fast, sandboxed), distro.sh (containers), polka-gifs.py,
              sp-hooks.py
```
