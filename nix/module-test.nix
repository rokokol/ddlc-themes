# Evaluates the module against stubs of the options it writes to, so the wiring is checked
# without a Home Manager generation. What it cannot check is the option names themselves —
# those come from Home Manager, and a real configuration is what proves them
{ lib, module }:

let
  stubs = {
    options = {
      programs.kitty.extraConfig = lib.mkOption {
        type = lib.types.lines;
        default = "";
      };
      # The same type Home Manager gives it. types.attrs would not do: it does not recurse, so
      # an mkDefault on a single key would never be resolved and the check would read a marker
      programs.btop.settings = lib.mkOption {
        type =
          with lib.types;
          attrsOf (oneOf [
            bool
            float
            int
            str
          ]);
        default = { };
      };
      xdg.configFile = lib.mkOption {
        type = lib.types.attrsOf (
          lib.types.submodule { options.source = lib.mkOption { type = lib.types.path; }; }
        );
        default = { };
      };
      # Claude Code reads ~/.claude, which sits outside XDG, so those themes go through
      # home.file rather than xdg.configFile
      home.file = lib.mkOption {
        type = lib.types.attrsOf (
          lib.types.submodule { options.source = lib.mkOption { type = lib.types.path; }; }
        );
        default = { };
      };
    };
  };

  eval =
    settings:
    (lib.evalModules {
      modules = [
        stubs
        module
        settings
      ];
    }).config;

  on = eval {
    ddlc.kitty.enable = true;
    ddlc.btop.enable = true;
    ddlc.matplotlib.enable = true;
    ddlc.claude-code.enable = true;
    ddlc.opencode.enable = true;
  };
  light = eval {
    ddlc.kitty = {
      enable = true;
      variant = "light";
    };
    ddlc.btop = {
      enable = true;
      variant = "light";
    };
  };
  off = eval { };

  # The setting a consumer would write next to the module, to prove the colours land after it
  ordered = eval {
    ddlc.kitty.enable = true;
    programs.kitty.extraConfig = "background #123456\n";
  };
in
{
  kitty = on.programs.kitty.extraConfig;
  kittyLight = light.programs.kitty.extraConfig;
  kittyOrder = ordered.programs.kitty.extraConfig;

  # Everything that lands through xdg.configFile — btop, matplotlib and opencode alike
  configFiles = lib.attrNames on.xdg.configFile;
  homeFiles = lib.attrNames on.home.file;
  btopTheme = on.programs.btop.settings.color_theme or null;
  btopThemeLight = light.programs.btop.settings.color_theme or null;

  offKitty = off.programs.kitty.extraConfig;
  offFiles = lib.attrNames off.xdg.configFile;
  offHomeFiles = lib.attrNames off.home.file;
  offTheme = off.programs.btop.settings.color_theme or null;
}
