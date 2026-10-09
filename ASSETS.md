# Assets and third-party content

`LICENSE` (MIT) covers the **code** in this repository: `generate.sh`, `install.sh`, `src/`, `templates/` and the Nix expressions. It does **not** cover the colours, which are Team Salvato's, or the fonts below; this repository only maps the colours onto applications and pages

## Fonts

| Path | Font | Author | Licence |
| --- | --- | --- | --- |
| `vendor/departure-mono/DepartureMono-Regular.woff2`, copied to `dist/` | [Departure Mono](https://github.com/rektdeckard/departure-mono) 1.500 | Helena Zhang | [SIL OFL 1.1](vendor/departure-mono/DepartureMono-LICENSE.txt) |
| `vendor/nunito/Nunito-wght.ttf` and `Nunito-Italic-wght.ttf`, packed into `dist/Nunito.woff2` and `dist/Nunito-Italic.woff2` | [Nunito](https://github.com/googlefonts/nunito) | The Nunito Project Authors | [SIL OFL 1.1](vendor/nunito/Nunito-LICENSE.txt) |
| `dist/DepartureMonoNerdFontMono-Regular.woff2`, packed from the Nerd Fonts v3.5.0 archive `DepartureMono.tar.xz` | [Departure Mono](https://github.com/rektdeckard/departure-mono) patched by [Nerd Fonts](https://github.com/ryanoasis/nerd-fonts) | Helena Zhang; the icon sets' authors | the font under [SIL OFL 1.1](dist/DepartureMonoNerdFont-LICENSE.txt), each icon set under the licence the [archive's README](dist/DepartureMonoNerdFont-README.md) names |

The copies in `vendor/` are unmodified and kept byte-equal to their sources by `vendor-sync.sh`. The Nerd Fonts archive is not vendored: nixpkgs fetches it by hash, so this flake's lock pins it, and its `LICENSE` and `README.md` are copied to `dist/` unchanged. The WOFF2 files in `dist/` hold the same glyphs, only compressed

The headings name `Doki`, a font by 538Fonts from 2015, which is not part of the game. It is free for personal use only, so it is **not** shipped here; a reader who has it installed sees it, and everyone else sees Nunito Black

## Doki Doki Literature Club

Doki Doki Literature Club and Doki Doki Literature Club Plus are the property of [Team Salvato](https://teamsalvato.com/). This project is **unaffiliated with and not endorsed by Team Salvato**

The following are derived from official DDLC material:

| Path | What |
| --- | --- |
| `dist/ddlc-kitty-*.conf`, `dist/ddlc-btop-*.theme`, `dist/ddlc*.mplstyle`, `dist/ddlc_cmaps.py`, `dist/ddlc-*.css`, `dist/ddlc-mail.json`, `dist/ddlc-syntax.json`, `dist/ddlc-claude-code-*.json`, `dist/ddlc-opencode.json` | the colours come from [ddlc-palette](https://github.com/rokokol/ddlc-palette), which measures them off [ddlc.moe](https://ddlc.moe/). Which colour fills which slot of which application is mine, the values are theirs |

No official artwork is bundled. `docs/*.png` are screenshots of my own terminal and renders of `docs/matplotlib-demo.py`, `docs/ui-demo.html` and `docs/report-demo.html`

Use here follows [Team Salvato's IP guidelines](https://teamsalvato.com/ip-guidelines): this is non-commercial fan content, nothing containing official assets is sold, and no claim of affiliation is made. If you reuse any of it, the same conditions apply to you

Team Salvato reserves the right to act on copyright or trademark infringement; nothing here grants a licence to their intellectual property
