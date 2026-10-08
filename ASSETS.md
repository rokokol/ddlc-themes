# Assets and third-party content

`LICENSE` (MIT) covers the **code** in this repository: `generate.sh`, `install.sh`, `src/`, `templates/` and the Nix expressions. It does **not** cover the colours, which are Team Salvato's, or the font below; this repository only maps the colours onto applications and pages

## Fonts

| Path | Font | Author | Licence |
| --- | --- | --- | --- |
| `vendor/departure-mono/DepartureMono-Regular.woff2`, copied to `dist/` | [Departure Mono](https://github.com/rektdeckard/departure-mono) 1.500 | Helena Zhang | [SIL OFL 1.1](vendor/departure-mono/DepartureMono-LICENSE.txt) |

The copy is unmodified and kept byte-equal to its source by `vendor-sync.sh`

## Doki Doki Literature Club

Doki Doki Literature Club and Doki Doki Literature Club Plus are the property of [Team Salvato](https://teamsalvato.com/). This project is **unaffiliated with and not endorsed by Team Salvato**

The following are derived from official DDLC material:

| Path | What |
| --- | --- |
| `dist/ddlc-kitty-*.conf`, `dist/ddlc-btop-*.theme`, `dist/ddlc*.mplstyle`, `dist/ddlc_cmaps.py`, `dist/ddlc-*.css`, `dist/ddlc-mail.json`, `dist/ddlc-syntax.json`, `dist/ddlc-claude-code-*.json`, `dist/ddlc-opencode.json` | the colours come from [ddlc-palette](https://github.com/rokokol/ddlc-palette), which measures them off [ddlc.moe](https://ddlc.moe/). Which colour fills which slot of which application is mine, the values are theirs |

No official artwork is bundled. `docs/*.png` are screenshots of my own terminal and renders of `docs/matplotlib-demo.py`, `docs/ui-demo.html` and `docs/report-demo.html`

The `Doki` font family is Team Salvato's and is **not** shipped here. The report stylesheet and the letters name it first in their font stack, so it is used only where a reader has it installed

Use here follows [Team Salvato's IP guidelines](https://teamsalvato.com/ip-guidelines): this is non-commercial fan content, nothing containing official assets is sold, and no claim of affiliation is made. If you reuse any of it, the same conditions apply to you

Team Salvato reserves the right to act on copyright or trademark infringement; nothing here grants a licence to their intellectual property
