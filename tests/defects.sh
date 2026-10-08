#!/usr/bin/env bash
# The defect list for generate.sh's own guards, read by `scripts/t.sh falsify`
#
# Each entry breaks one guard's input, and the generator must refuse the run. The format
# is in `scripts/t.sh help falsify`; the run, inside the dev shell for the palette files, is
#
#   nix develop -c scripts/t.sh falsify -d tests/defects.sh -- bash generate.sh
#
# FIND must appear exactly once in FILE, or the entry is reported stale
#
# shellcheck disable=SC2016 # every $ in a single-quoted text here is text to find, never an expansion

GENERATE='generate.sh'
UI='src/ui.css'

# The role table

defect 'roles/palette-name' "$GENERATE" \
  'faint                 jacket' \
  'dot                   jacket' \
  'a role named after a palette colour repaints that colour on a page that links palette.css'

defect 'roles/unknown-operand' "$GENERATE" \
  'line-live             plum' \
  'line-live             plumm' \
  'a role names a colour that does not exist and the stylesheet ships a hole'

defect 'roles/share-out-of-range' "$GENERATE" \
  'jacket@75:paper' \
  'jacket@175:paper' \
  'a mix share past 100 per cent renders as a colour nobody chose'

# The syntax table

defect 'syntax/under-the-floor' "$GENERATE" \
  'number      base09     yuri' \
  'number      base09     sayori' \
  'numbers in light editors read at 2:1 on paper'

defect 'syntax/dark-column-reads-a-role' "$GENERATE" \
  'comment     base03     muted' \
  'comment     muted      muted' \
  'the dark code window takes a light-dark() role and turns light under a light page'

defect 'opencode/unknown-syntax-role' "$GENERATE" \
  'syntaxKeyword              =keyword' \
  'syntaxKeyword              =keywrd' \
  'opencode reads a syntax role that does not exist and the theme ships a hole'

# The stylesheets in src/

defect 'css/undefined-name' "$UI" \
  'var(--ddlc-switch-off)' \
  'var(--ddlc-switch-of)' \
  'a declaration reads a name nothing defines and the browser drops it in silence'

defect 'css/defines-a-palette-name' "$UI" \
  '  --ddlc-gap: 16px;' \
  '  --ddlc-gap: 16px;
  --ddlc-pink: red;' \
  'the kit repaints a palette colour for every page that links it'

# The letters

defect 'mail/unknown-placeholder' "$GENERATE" \
  'column        max-width:736px' \
  'column        color:{nope};max-width:736px' \
  'a letter style carries an unfilled placeholder into every mail'
