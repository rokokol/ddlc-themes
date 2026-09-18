{
  description = "The Doki Doki Literature Club themes for kitty, btop, matplotlib, Claude Code and opencode, light and dark";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    ddlc-palette = {
      url = "github:rokokol/ddlc-palette";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      ddlc-palette,
    }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});

      # Each piece isolated, so a README edit doesn't rebuild anything
      generator = builtins.path {
        name = "generate.sh";
        path = ./generate.sh;
      };
      installer = builtins.path {
        name = "install.sh";
        path = ./install.sh;
      };
      dist = builtins.path {
        name = "ddlc-themes-dist";
        path = ./dist;
      };
      versionFile = builtins.path {
        name = "VERSION";
        path = ./VERSION;
      };
      testsDir = builtins.path {
        name = "ddlc-themes-tests";
        path = ./tests;
      };
      checkSh = builtins.path {
        name = "check-sh.sh";
        path = ./check-sh.sh;
      };
      completionsDir = builtins.path {
        name = "ddlc-themes-completions";
        path = ./completions;
      };
      # The one source of version: VERSION at the repo root, read by the package, printed
      # by install.sh -v, asserted against CHANGELOG.md by CI
      version = nixpkgs.lib.fileContents versionFile;

      schemes = ddlc-palette.lib.dist.base16;
      # The base16 schemes carry sixteen slots; the themes with more roles than that name
      # palette colours directly, out of the flat name=HEX form
      palette = ddlc-palette.lib.dist.env;
    in
    {
      # The rendered themes as paths, so a consumer names an app and a variant instead of a
      # filename. There is deliberately no module behind them: readFile or a source = is the
      # whole integration
      #   kitty.extraConfig = builtins.readFile ddlc-terminal-themes.lib.kitty.dark;
      # Both applications read a theme out of ~/.config, so the module is the two settings that
      # name it — which is the half a consumer keeps getting wrong. lib below stays for a
      # configuration that would rather place the files itself
      # homeModules is the name the flake schema knows; homeManagerModules is what most
      # consumers still write, so both point at the same module
      homeModules.default = import ./nix/module.nix { inherit self; };
      homeManagerModules.default = self.homeModules.default;

      lib = {
        kitty = {
          light = ./dist/ddlc-kitty-light.conf;
          dark = ./dist/ddlc-kitty-dark.conf;
        };
        btop = {
          light = ./dist/ddlc-btop-light.theme;
          dark = ./dist/ddlc-btop-dark.theme;
        };
        # The filenames are the API — plt.style.use("ddlc"), import ddlc_cmaps — so keep them
        # when placing these
        matplotlib = {
          light = ./dist/ddlc.mplstyle;
          dark = ./dist/ddlc-dark.mplstyle;
          cmaps = ./dist/ddlc_cmaps.py;
        };
        # The matplotlib roles as a stylesheet for HTML reports; one file, light and dark
        report = ./dist/ddlc-report.css;
        claude-code = {
          light = ./dist/ddlc-claude-code-light.json;
          dark = ./dist/ddlc-claude-code-dark.json;
        };
        # One file, both variants: opencode reads {dark, light} out of each value itself
        opencode = ./dist/ddlc-opencode.json;
      };

      packages = forAllSystems (pkgs: {
        default =
          pkgs.runCommand "ddlc-themes-${version}"
            {
              meta = {
                description = "The Doki Doki Literature Club themes for kitty, btop, matplotlib, Claude Code and opencode";
                homepage = "https://github.com/rokokol/ddlc-themes";
                # MIT covers the generator; the colours themselves are Team Salvato's
                license = pkgs.lib.licenses.mit;
                # Plain config files — nothing here is built for a platform
                platforms = pkgs.lib.platforms.all;
              };
            }
            ''
              mkdir -p $out/share/ddlc-themes
              cp -r ${dist}/. $out/share/ddlc-themes/
            '';
      });

      # dist/ is committed so a consumer without Nix just copies files; this proves it is what
      # the generator would write today against the palette this flake is locked to
      # For a consumer who reaches for pkgs rather than this flake's packages directly
      overlays.default = final: _prev: {
        ddlc-themes = self.packages.${final.stdenv.hostPlatform.system}.default;
      };

      checks = forAllSystems (pkgs: {
        dist-is-current = pkgs.runCommand "dist-is-current" { nativeBuildInputs = [ pkgs.jq ]; } ''
          install -m755 ${generator} generate.sh
          DDLC_BASE16_LIGHT=${schemes.light} DDLC_BASE16_DARK=${schemes.dark} \
            DDLC_PALETTE_ENV=${palette} \
            bash generate.sh >/dev/null
          diff -r ${dist} dist
          touch $out
        '';

        # Enabling a switch has to be enough: the colours in kitty's config after its own
        # settings, both btop variants deployed and the theme named — and nothing while disabled
        module-wiring =
          let
            wiring = import ./nix/module-test.nix {
              inherit (nixpkgs) lib;
              module = self.homeManagerModules.default;
            };
          in
          pkgs.runCommand "module-wiring"
            {
              nativeBuildInputs = [ pkgs.jq ];
              dump = builtins.toJSON wiring;
              passAsFile = [ "dump" ];
            }
            ''
              want() { jq -e "$1" "$dumpPath" >/dev/null || { echo "module wiring: $2"; exit 1; }; }

              want '.kitty | test("background #222222")' "the dark colours do not reach kitty"
              want '.kittyLight | test("background #FFFFFF")' "the variant does not reach kitty"
              # kitty takes the last word for a key, so the theme has to land after any setting
              # the consumer wrote next to the module
              want '.kittyOrder | test("#123456[\\s\\S]*#222222")' "the colours do not land last"

              want '.configFiles | index("btop/themes/ddlc-dark.theme")' "the dark theme is not deployed"
              # Both go in whatever the variant is: btop lists its themes directory, so the other
              # one is a keypress away in its own menu
              want '.configFiles | index("btop/themes/ddlc-light.theme")' "the light theme is not deployed"
              want '.btopTheme == "ddlc-dark"' "btop does not name the theme"
              want '.btopThemeLight == "ddlc-light"' "the variant does not reach btop"

              want '.configFiles | index("matplotlib/stylelib/ddlc.mplstyle")' "the light style is not deployed"
              want '.configFiles | index("matplotlib/stylelib/ddlc-dark.mplstyle")' "the dark style is not deployed"
              want '.configFiles | index("matplotlib/ddlc_cmaps.py")' "the colormaps are not deployed"

              # The slug /theme lists is the filename, so the app segment is dropped on the way in
              want '.homeFiles | index(".claude/themes/ddlc-dark.json")' "the dark Claude Code theme is not deployed"
              want '.homeFiles | index(".claude/themes/ddlc-light.json")' "the light Claude Code theme is not deployed"
              # One file for opencode, landing under the name the theme is selected by
              want '.configFiles | index("opencode/themes/ddlc.json")' "the opencode theme is not deployed"

              want '.offKitty == ""' "kitty is themed while disabled"
              want '.offFiles == []' "a theme is deployed while disabled"
              want '.offHomeFiles == []' "a Claude Code theme is deployed while disabled"
              want '.offTheme == null' "btop is themed while disabled"
              touch $out
            '';

        # The one shell file list lives here and nowhere else: CI's shell job is a fast
        # named status for this check, not a second copy of the commands
        scripts-lint =
          pkgs.runCommand "scripts-lint"
            {
              nativeBuildInputs = [
                # check-sh.sh below is moving to reading the script it is given as a tree,
                # out of `shfmt --to-json`, with jq flattening that tree into rows. This
                # sandbox has a scrubbed PATH, so the dev shell's jq is not reachable here
                # and the tool has to be named on this derivation
                pkgs.jq
                pkgs.shellcheck
                pkgs.shfmt
                pkgs.zsh
              ];
            }
            ''
              files="${generator} ${installer} ${testsDir}/run.sh ${testsDir}/distro.sh ${checkSh} ${completionsDir}/install.sh.bash"
              # shellcheck disable=SC2086
              shellcheck $files
              # shellcheck disable=SC2086
              shfmt -d -i 2 -ci $files
              # zsh is not shellcheck's language; a parse is what can be checked
              zsh -n ${completionsDir}/install.sh.zsh

              # install.sh, its help and its completions must not drift apart
              mkdir -p repo
              cp ${installer} repo/install.sh
              cp ${versionFile} repo/VERSION
              cp -r ${completionsDir} repo/completions
              cp ${checkSh} repo/check-sh.sh
              (cd repo && bash ./check-sh.sh -c completions/install.sh.bash completions/install.sh.zsh install.sh)
              touch $out
            '';

        # The fast installer suite, in the sandbox: the manifest contract, the
        # per-component sweep, selective uninstall, staging, the refusal path
        install-sh-works =
          pkgs.runCommand "install-sh-works"
            {
              # tests/run.sh builds a deliberately install(1)-less PATH out of these
              nativeBuildInputs = [ pkgs.coreutils ];
            }
            ''
              mkdir -p repo/tests
              cp ${installer} repo/install.sh
              cp ${versionFile} repo/VERSION
              cp -r ${dist} repo/dist
              cp -r ${completionsDir} repo/completions
              cp ${checkSh} repo/check-sh.sh
              cp ${testsDir}/run.sh repo/tests/
              chmod +x repo/install.sh repo/tests/*.sh
              patchShebangs repo >/dev/null
              HOME=$PWD bash repo/tests/run.sh "$PWD/repo"
              touch $out
            '';

        # A theme is only usable if every colour reached it, and a missing slot renders as an
        # empty value rather than as an error
        themes-are-filled = pkgs.runCommand "themes-are-filled" { nativeBuildInputs = [ pkgs.jq ]; } ''
          for f in ${dist}/ddlc-kitty-*.conf; do
            grep -Eq '^color21 #[0-9A-F]{6}$' "$f" || { echo "$f: the ANSI table is short"; exit 1; }
            if grep -Ev '^(#|$)' "$f" | grep -Ev ' #[0-9A-F]{6}$'; then
              echo "$f: the value above is not a hex colour" >&2
              exit 1
            fi
          done
          for f in ${dist}/ddlc-btop-*.theme; do
            grep -q 'theme\[main_bg\]="#' "$f" || { echo "$f: no background"; exit 1; }
            # Only the mid and end of a scaleless meter are deliberately empty
            if grep -Ev '^(#|$)' "$f" | grep -Ev '^theme\[[a-z_]+\]="(#[0-9A-F]{6})?"$'; then
              echo "$f: the line above is not a theme[key]=\"#hex\"" >&2
              exit 1
            fi
          done
          # matplotlib takes its hex bare, so every colour-carrying rcparam must end in six hex
          # digits — except the cycler, which is a list of them
          for f in ${dist}/ddlc.mplstyle ${dist}/ddlc-dark.mplstyle; do
            grep -Eq "^axes.prop_cycle:  cycler\('color', \['[0-9A-F]{6}'" "$f" \
              || { echo "$f: no cycler"; exit 1; }
            if grep -E 'colou?r:' "$f" | grep -Ev '(color:( +[0-9A-F]{6}| +cycler.*)|labelcolor: +[0-9A-F]{6})$'; then
              echo "$f: the value above is not a bare hex colour" >&2
              exit 1
            fi
          done
          # Every token the stylesheet defines is a hex; the element rules only reference them
          if grep -E '^ *--ddlc-' ${dist}/ddlc-report.css | grep -Ev '^ *--ddlc-[a-z0-9-]+: #[0-9A-F]{6};$'; then
            echo "ddlc-report.css: the token above is not a hex colour" >&2
            exit 1
          fi
          for f in ${dist}/ddlc-claude-code-*.json; do
            jq -e '(.overrides | length) > 0
              and ([.overrides[] | select(test("^#[0-9A-F]{6}$") | not)] == [])' "$f" >/dev/null \
              || { echo "$f: an override is not a hex colour"; exit 1; }
          done
          # Every def is a hex and every theme value resolves: a def by name, or "none"
          jq -e '. as $r
            | (.defs | length > 0)
            and ([.defs[] | select(test("^#[0-9A-F]{6}$") | not)] == [])
            and ([.theme[] | if type == "object" then .dark, .light else . end
                  | . as $v | select(($v == "none" or ($r.defs | has($v))) | not)] == [])' \
            ${dist}/ddlc-opencode.json >/dev/null \
            || { echo "ddlc-opencode.json: a value does not resolve against defs"; exit 1; }
          touch $out
        '';
      });

      devShells = forAllSystems (pkgs: {
        default = pkgs.mkShell {
          packages = [
            pkgs.shellcheck
            pkgs.shfmt
            pkgs.jq
          ];
          # So generate.sh runs with no arguments inside the shell
          DDLC_BASE16_LIGHT = schemes.light;
          DDLC_BASE16_DARK = schemes.dark;
          DDLC_PALETTE_ENV = palette;
        };
      });

      formatter = forAllSystems (pkgs: pkgs.nixfmt-tree);
    };
}
