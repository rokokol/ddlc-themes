# app

A page on the [DDLC web kit](https://github.com/rokokol/ddlc-themes): the bar, three columns of tools, stage and readouts, and cards. `index.html` is the layout, and `app.css` and `app.js` hold the page's own rules and code

## Vendor the kit

The page reads the kit out of `vendor/`. Take each file at a pinned commit with [vendor-sync.sh](https://github.com/rokokol/ci-skill/blob/master/templates/vendor-sync.sh), so a weekly run can move it forward only on a green build:

```sh
for f in ddlc-ui.css ddlc-theme.js ddlc-cloud.js DepartureMono-Regular.woff2 DepartureMono-LICENSE.txt; do
  ./vendor-sync.sh add "vendor/$f" rokokol/ddlc-themes "dist/$f"
done
```

Serve the directory over HTTP to open it, because a browser does not load module scripts from a file

## Assets

The font is Departure Mono by Helena Zhang under the SIL Open Font License, and its licence lands beside it in `vendor/`. The colours are Team Salvato's, measured off [ddlc.moe](https://ddlc.moe) by [ddlc-palette](https://github.com/rokokol/ddlc-palette); this page is unaffiliated with and not endorsed by Team Salvato
