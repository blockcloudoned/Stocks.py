{pkgs}: {
  deps = [
    pkgs.postgresql
    pkgs.glibcLocales
    pkgs.xsimd
    pkgs.pkg-config
    pkgs.libxcrypt
  ];
}
