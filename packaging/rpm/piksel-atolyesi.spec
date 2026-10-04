%global debug_package %{nil}
%global __os_install_post %{nil}
%global __provides_exclude_from ^/usr/lib/piksel-atolyesi/.*$
%global __requires_exclude_from ^/usr/lib/piksel-atolyesi/.*$

Name: piksel-atolyesi
Version: %{app_version}
Release: 1%{?dist}
Summary: Offline color-by-number desktop game
License: MIT
URL: https://github.com/Teknoloji-Filozoflari/Pixel_Color_Game
Source0: payload.tar.gz
Requires: glibc >= 2.42
Requires: fontconfig, dbus-libs, mesa-libEGL, mesa-libGL
Requires: libX11, libX11-xcb, libxcb, libxkbcommon, libxkbcommon-x11
Requires: xcb-util-cursor, xcb-util-image, xcb-util-keysyms
Requires: xcb-util-renderutil, xcb-util-wm

%description
Piksel Atolyesi is an offline pixel painting game with 900 bundled paintings.
Python, Qt, NumPy and Pillow are included in the private application bundle.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build

%install
mkdir -p %{buildroot}
cp -a usr %{buildroot}/

%files
/usr/lib/piksel-atolyesi
/usr/bin/piksel-atolyesi
/usr/share/applications/io.github.teknolojifilozoflari.PixelColorGame.desktop
/usr/share/icons/hicolor/512x512/apps/piksel-atolyesi.png
/usr/share/metainfo/io.github.teknolojifilozoflari.PixelColorGame.appdata.xml
%license /usr/share/doc/piksel-atolyesi
