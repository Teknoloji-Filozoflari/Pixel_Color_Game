{
  description = "Piksel Atölyesi — çevrim dışı piksel boyama oyunu";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" ];
      eachSystem = nixpkgs.lib.genAttrs systems;
      packageFor = system:
        let pkgs = import nixpkgs { inherit system; };
        in pkgs.callPackage ./packaging/nix/package.nix { };
    in {
      packages = eachSystem (system: {
        piksel-atolyesi = packageFor system;
        default = self.packages.${system}.piksel-atolyesi;
      });

      apps = eachSystem (system: {
        default = {
          type = "app";
          program = "${self.packages.${system}.piksel-atolyesi}/bin/piksel-atolyesi";
        };
      });

      checks = eachSystem (system:
        let pkgs = import nixpkgs { inherit system; };
        in {
          package = self.packages.${system}.piksel-atolyesi;
          smoke = pkgs.runCommand "piksel-atolyesi-installed-smoke" {
            nativeBuildInputs = [ self.packages.${system}.piksel-atolyesi ];
          } ''
            export QT_QPA_PLATFORM=offscreen
            export QT_QUICK_BACKEND=software
            export XDG_CONFIG_HOME="$TMPDIR/config"
            export XDG_DATA_HOME="$TMPDIR/data"
            export XDG_CACHE_HOME="$TMPDIR/cache"
            export XDG_STATE_HOME="$TMPDIR/state"
            piksel-atolyesi --smoke-test --data-dir "$TMPDIR/game-data"
            test -f "$TMPDIR/game-data/progress.sqlite3"
            test -f "$TMPDIR/game-data/game.log"
            touch "$out"
          '';
        });
    };
}
