{pkgs}: {
  deps = [
    pkgs.zstd
    pkgs.dbus
    pkgs.freetype
    pkgs.fontconfig
    pkgs.libxkbcommon
    pkgs.xorg.libxcb
    pkgs.xvfb-run
  ];
}
