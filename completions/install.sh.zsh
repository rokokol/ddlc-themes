# Zsh completion for ./install.sh of ddlc-themes. Sourced from the checkout, not
# installed:
#   source completions/install.sh.zsh
# Defines the function and registers it directly — no fpath, no rehash; needs compinit
# to have run, which every interactive zsh with completion already has.
#
# The flag list is written by hand on purpose and checked against install.sh by
# check-sh.sh -c — same discipline as the bash file
_install_sh_completion() {
  _arguments \
    '(-h --help)'{-h,--help}'[show help and exit]' \
    '(-v --version)'{-v,--version}'[print the version and exit]' \
    '--component[which themes to install]:component:(kitty btop matplotlib claude-code opencode all)' \
    '--kitty[compatibility shorthand for --component kitty]' \
    '--btop[compatibility shorthand for --component btop]' \
    '--config-home[install under this directory instead of ~/.config]:directory:_files -/' \
    '--claude-home[install the Claude Code themes under this directory]:directory:_files -/' \
    '--destdir[staging root]:directory:_files -/' \
    '--uninstall[remove a previous install by its manifest]'
}
compdef _install_sh_completion install.sh
