# Assets and third-party content

`LICENSE` (MIT) covers the **code** in this repository: `generate.sh`, `install.sh`, `src/`, `templates/` and the Nix expressions. It does **not** cover the colours, which are Team Salvato's, or the fonts below; this repository only maps the colours onto applications and pages

## Fonts

| Path | Font | Author | Licence |
| --- | --- | --- | --- |
| `vendor/departure-mono/DepartureMono-Regular.woff2`, copied to `dist/` | [Departure Mono](https://github.com/rektdeckard/departure-mono) 1.500 | Helena Zhang | [SIL OFL 1.1](vendor/departure-mono/DepartureMono-LICENSE.txt) |
| `vendor/nunito/Nunito-wght.ttf` and `Nunito-Italic-wght.ttf`, packed into `dist/Nunito.woff2` and `dist/Nunito-Italic.woff2` | [Nunito](https://github.com/googlefonts/nunito) | The Nunito Project Authors | [SIL OFL 1.1](vendor/nunito/Nunito-LICENSE.txt) |
| `vendor/noto-sans/NotoSans-wdth-wght.ttf`, merged into `dist/MyaNunito*` | [Noto Sans](https://github.com/notofonts/latin-greek-cyrillic) | The Noto Project Authors | [SIL OFL 1.1](vendor/noto-sans/NotoSans-LICENSE.txt) |
| `vendor/noto-sans-math/NotoSansMath-Regular.ttf`, merged into `dist/MyaNunito*` | [Noto Sans Math](https://github.com/notofonts/math) | The Noto Project Authors | [SIL OFL 1.1](vendor/noto-sans-math/NotoSansMath-LICENSE.txt) |
| `dist/MyaNunito.{ttf,woff2}`, `dist/MyaNunito-Italic.{ttf,woff2}` and `dist/MyaNunitoStatic-*.ttf`, merged from the three fonts above | Mya Nunito and Mya Nunito Static, a Modified Version of Nunito, Noto Sans and Noto Sans Math in the OFL's sense | The Nunito Project Authors; The Noto Project Authors | [SIL OFL 1.1](dist/MyaNunito-LICENSE.txt), with the notices of all three |
| `dist/DepartureMonoNerdFontMono-Regular.woff2`, packed from the Nerd Fonts v3.5.0 archive `DepartureMono.tar.xz` | [Departure Mono](https://github.com/rektdeckard/departure-mono) patched by [Nerd Fonts](https://github.com/ryanoasis/nerd-fonts) | Helena Zhang; the icon sets' authors | the font under [SIL OFL 1.1](dist/DepartureMonoNerdFont-LICENSE.txt), each icon set under the licence the [archive's README](dist/DepartureMonoNerdFont-README.md) names |

The copies in `vendor/` are unmodified and kept byte-equal to their sources by `vendor-sync.sh`. The Nerd Fonts archive is not vendored: nixpkgs fetches it by hash, so this flake's lock pins it, and its `LICENSE` and `README.md` are copied to `dist/` unchanged. The WOFF2 files of Departure Mono and Nunito in `dist/` hold the same glyphs, only compressed

The two Noto fonts come from [notofonts.github.io](https://github.com/notofonts/notofonts.github.io), whose repository is too large to fetch each week, so `vendor-sync.sh` pins each file by the SHA-256 of a download from a fixed commit. The licences come from the two script repositories named in the table, and `dist/` carries them as `NotoSans-LICENSE.txt` and `NotoSansMath-LICENSE.txt`. Mya Nunito is not a copy: `src/mya-nunito.py` keeps every glyph of Nunito as it is and adds the Greek, arrow, operator, letterlike and index glyphs that Nunito lacks, from Noto Sans at its normal width and from Noto Sans Math where Noto Sans lacks them. The added glyphs are scaled to Nunito's x-height and drawn at Nunito's weights, emboldened or thinned where no weight of Noto matches and only as far as the openings between their strokes allow, and they keep their sidebearings at every weight, as Nunito's own mathematical signs do. The added letters have their outward corners rounded, so a stroke ends in a half circle as in Nunito, while the signs keep their points. Mya Nunito Static is the same font at fixed weights. Neither licence reserves a font name, and the new name keeps the merge apart from both sources all the same. The font's own names carry the copyright notices of all three sources and the OFL, and so does `dist/MyaNunito-LICENSE.txt` beside it. Like every font here, it is under the OFL and not under this repository's MIT licence

The headings name `Doki`, a font by 538Fonts from 2015, which is not part of the game. It is free for personal use only, so it is **not** shipped here; a reader who has it installed sees it, and everyone else sees Mya Nunito Black

## Doki Doki Literature Club

Doki Doki Literature Club and Doki Doki Literature Club Plus are the property of [Team Salvato](https://teamsalvato.com/). This project is **unaffiliated with and not endorsed by Team Salvato**

The following are derived from official DDLC material:

| Path | What |
| --- | --- |
| `dist/ddlc-kitty-*.conf`, `dist/ddlc-btop-*.theme`, `dist/ddlc*.mplstyle`, `dist/ddlc_cmaps.py`, `dist/ddlc-*.css`, `dist/ddlc-mail.json`, `dist/ddlc-syntax.json`, `dist/ddlc-roles.json`, `dist/ddlc-claude-code-*.json`, `dist/ddlc-opencode.json`, `dist/ddlc-super-productivity.css`, `dist/ddlc-polka-*.{gif,webp}` | the colours come from [ddlc-palette](https://github.com/rokokol/ddlc-palette), which measures them off [ddlc.moe](https://ddlc.moe/). Which colour fills which slot of which application is mine, the values are theirs |

No official artwork is bundled. `dist/ddlc-polka-*.{gif,webp}` are drawn by `src/polka.py` after the game menu's polka-dot paper, and no game artwork is copied. `docs/*.png` are screenshots of my own terminal and of Super Productivity's web build under this theme, and renders of `docs/matplotlib-demo.py`, `docs/ui-demo.html` and `docs/report-demo.html`. Super Productivity is [super-productivity/super-productivity](https://github.com/super-productivity/super-productivity), MIT; its interface shows in those two screenshots only

Use here follows [Team Salvato's IP guidelines](https://teamsalvato.com/ip-guidelines): this is non-commercial fan content, nothing containing official assets is sold, and no claim of affiliation is made. If you reuse any of it, the same conditions apply to you

Team Salvato reserves the right to act on copyright or trademark infringement; nothing here grants a licence to their intellectual property
