{ lib, python3, qt6, ruff, makeFontsConf, dejavu_fonts }:
let
  project = builtins.fromTOML (builtins.readFile ../../pyproject.toml);
  fonts = makeFontsConf { fontDirectories = [ dejavu_fonts ]; };
in
python3.pkgs.buildPythonApplication {
  pname = "piksel-atolyesi";
  version = project.project.version;
  pyproject = true;
  src = lib.cleanSourceWith {
    src = ../..;
    filter = path: type:
      let name = baseNameOf path;
      in lib.cleanSourceFilter path type
        && !(builtins.elem name [ ".venv" "build" "dist" "work" "runtime"
          "local-data" ".pytest_cache" ".ruff_cache" "__pycache__"
          "parts" "stage" "prime" ".snapcraft" "result" ])
        && !(lib.hasSuffix ".egg-info" name)
        && !(lib.hasPrefix "result-" name)
        && !(lib.hasSuffix ".pyc" name)
        && !(lib.hasSuffix ".sqlite3" name);
  };
  build-system = [ python3.pkgs.setuptools ];
  dependencies = with python3.pkgs; [ pyside6 numpy pillow ];
  nativeBuildInputs = [ qt6.wrapQtAppsHook ];
  buildInputs = with qt6; [ qtbase qtsvg qtwayland ];
  dontWrapQtApps = true;
  preFixup = ''
    makeWrapperArgs+=( "''${qtWrapperArgs[@]}" )
    makeWrapperArgs+=( --set FONTCONFIG_FILE "${fonts}" )
  '';
  nativeCheckInputs = [ python3.pkgs.pytest ruff ];
  checkPhase = ''
    runHook preCheck
    export QT_QPA_PLATFORM=offscreen
    export FONTCONFIG_FILE="${fonts}"
    export QT_PLUGIN_PATH="${qt6.qtbase}/${qt6.qtbase.qtPluginPrefix}:${qt6.qtsvg}/${qt6.qtbase.qtPluginPrefix}"
    ruff check src tests run.py packaging/build_bundle.py packaging/build_rpm.py
    ${python3.interpreter} -m pytest -q
    runHook postCheck
  '';
  postInstall = ''
    install -Dm644 packaging/appimage/io.github.teknolojifilozoflari.PixelColorGame.desktop \
      "$out/share/applications/io.github.teknolojifilozoflari.PixelColorGame.desktop"
    install -Dm644 src/pixel_coloring/resources/icons/piksel-atolyesi.png \
      "$out/share/icons/hicolor/512x512/apps/piksel-atolyesi.png"
    install -Dm644 packaging/appimage/io.github.teknolojifilozoflari.PixelColorGame.appdata.xml \
      "$out/share/metainfo/io.github.teknolojifilozoflari.PixelColorGame.appdata.xml"
    mkdir -p "$out/share/doc/piksel-atolyesi"
    cp LICENSE ASSETS_LICENSE.md THIRD_PARTY.md TELIF-VE-YAYIN-NOTU.md "$out/share/doc/piksel-atolyesi/"
    cp -a LICENSES "$out/share/doc/piksel-atolyesi/"
    ln -s "$out/bin/pixel-coloring" "$out/bin/piksel-atolyesi"
  '';
  pythonImportsCheck = [ "pixel_coloring" "pixel_coloring.app" ];
  meta = {
    description = "Offline pixel painting game with 900 bundled paintings";
    homepage = "https://github.com/Teknoloji-Filozoflari/Pixel_Color_Game";
    license = lib.licenses.mit;
    platforms = lib.platforms.linux;
    mainProgram = "piksel-atolyesi";
  };
}
