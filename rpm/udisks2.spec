%global glib2_version                   2.36
%global gobject_introspection_version   1.30.0
%global polkit_version                  0.102
%global systemd_version                 208
%global dbus_version                    1.4.0
%global libblockdev_version             2.14

Name:    udisks2
Summary: Disk Manager
Version: 2.7.5
Release: 1
License: GPLv2+
Group:   System Environment/Libraries
URL:     https://github.com/storaged-project/udisks
Source0: %{name}-%{version}.tar.bz2
Source1: udisks2-symlink-mount-path
Patch1: 0001-Disable-libblockdev-mdraid-and-part-support-from-sou.patch
Patch2: 0002-Drop-smartata-dependencies.patch
Patch3: 0003-Loosen-up-mount-unmount-rights.patch
Patch4: 0004-Introduce-mount-sd-service-that-is-executed-as-nemo.patch
Patch5: 0005-Add-udev-rule-for-the-sda-drives.patch
Patch6: 0006-Disable-zram-rule-for-now.patch
Patch7: 0007-Create-mount-path-with-755-rights.patch
Patch8: 0008-Make-it-possible-to-format-from-another-seat.-Fixes-.patch
Patch9: 0009-Make-it-possible-to-unlock-from-another-seat.patch

BuildRequires: pkgconfig(glib-2.0) >= %{glib2_version}
BuildRequires: pkgconfig(gobject-introspection-1.0)
BuildRequires: pkgconfig(polkit-agent-1) >= %{polkit_version}
BuildRequires: pkgconfig(polkit-gobject-1) >= %{polkit_version}
BuildRequires: pkgconfig(systemd) >= %{systemd_version}
BuildRequires: pkgconfig(openssl)
BuildRequires: gettext-devel
BuildRequires: autoconf
BuildRequires: automake
BuildRequires: libxslt
BuildRequires: libtool
BuildRequires: intltool
BuildRequires: libacl-devel
BuildRequires: chrpath
BuildRequires: pkgconfig(gudev-1.0) >= %{systemd_version}
BuildRequires: intltool
BuildRequires: gnome-common
BuildRequires: libblockdev-devel        >= %{libblockdev_version}
BuildRequires: libblockdev-loop-devel   >= %{libblockdev_version}
BuildRequires: libblockdev-swap-devel   >= %{libblockdev_version}
BuildRequires: libblockdev-fs-devel     >= %{libblockdev_version}
BuildRequires: libblockdev-crypto-devel >= %{libblockdev_version}
BuildRequires: oneshot

Requires: libblockdev        >= %{libblockdev_version}
Requires: libblockdev-loop   >= %{libblockdev_version}
Requires: libblockdev-swap   >= %{libblockdev_version}
Requires: libblockdev-fs     >= %{libblockdev_version}
Requires: libblockdev-crypto >= %{libblockdev_version}

# Needed for the systemd-related macros used in this file
%{?systemd_requires}
BuildRequires: systemd

# Needed to pull in the system bus daemon
Requires: dbus >= %{dbus_version}
# Needed to pull in the systemd as that provides udev daemon
Requires: systemd >= %{systemd_version}
# For mount, umount, mkswap
Requires: util-linux
# For mkfs.ext3, mkfs.ext3, e2label
Requires: e2fsprogs
#Requires: gdisk
# For ejecting removable disks
#Requires: eject

Requires: lib%{name} = %{version}-%{release}

%{_oneshot_requires_post}

Obsoletes: sd-utils < 0.1.6
Provides: sd-utils >= 0.1.6

%description
The Udisks project provides a daemon, tools and libraries to access and
manipulate disks, storage devices and technologies.

%package -n lib%{name}
Summary: Dynamic library to access the udisksd daemon
Group: System Environment/Libraries
License: LGPLv2+

%description -n lib%{name}
This package contains the dynamic library, which provides
access to the udisksd daemon.

%package -n lib%{name}-devel
Summary: Development files for lib%{name}
Group: Development/Libraries
Requires: lib%{name} = %{version}-%{release}
License: LGPLv2+

%description -n lib%{name}-devel
This package contains the development files for the library lib%{name}, a
dynamic library, which provides access to the udisksd daemon.

%prep
%setup -q -n %{name}-%{version}/%{name}

%patch1 -p1 -b .disable-mdraid_and_part
%patch2 -p1 -b .drop-smartata
%patch3 -p1 -b .loosen-up-rights
%patch4 -p1 -b .mount-sd-service
%patch5 -p1 -b .udev-rules-for-sda
%patch6 -p1 -b .udev-disable-zram
%patch7 -p1 -b .mount-path-rights
%patch8 -p1 -b .format-another-seat
%patch9 -p1 -b .unlock-another-seat

# Disable gtk-doc
sed -i 's/SUBDIRS = data udisks src tools modules po doc/SUBDIRS = data udisks src tools modules po/' Makefile.am
sed -i '/--enable-gtk-doc/d' Makefile.am
sed -i '/doc\/Makefile/d' configure.ac
sed -i '/GTK_DOC_CHECK/d' configure.ac

%build
glib-gettextize --force --copy
intltoolize --force --copy --automake
autoreconf -vfi -Wno-portability
%configure \
    --sysconfdir=/etc \
    --enable-man=no \
    --prefix=%{_prefix}
make %{?_smp_mflags}

%install
make install DESTDIR=%{buildroot}

find %{buildroot} -name \*.la -o -name \*.a | xargs rm

chrpath --delete %{buildroot}/%{_sbindir}/umount.udisks2
chrpath --delete %{buildroot}/%{_bindir}/udisksctl
chrpath --delete %{buildroot}/%{_libexecdir}/udisks2/udisksd

mkdir -p %{buildroot}/%{_oneshotdir}/
install -m 0755 %{SOURCE1} %{buildroot}/%{_oneshotdir}

mkdir -p %{buildroot}/%{_unitdir}/graphical.target.wants
ln -s ../udisks2.service %{buildroot}/%{_unitdir}/graphical.target.wants/udisks2.service

%find_lang udisks2

%post -n %{name}
systemctl daemon-reload || :
systemctl reload-or-try-restart udisks2.service || :
udevadm control --reload || :
udevadm trigger || :

%{_bindir}/add-oneshot --late udisks2-symlink-mount-path || :

%preun -n %{name}
if [ "$1" -eq 0 ]; then
    systemctl stop udisks2.service || :
fi

%post -n lib%{name} -p /sbin/ldconfig

%postun -n lib%{name} -p /sbin/ldconfig

%files -f udisks2.lang
%doc COPYING

%dir %{_sysconfdir}/udisks2
%{_sysconfdir}/udisks2/udisks2.conf

%{_sysconfdir}/dbus-1/system.d/org.freedesktop.UDisks2.conf
%{_datadir}/bash-completion/completions/udisksctl
%{_unitdir}/udisks2.service
%{_unitdir}/graphical.target.wants/udisks2.service
%{_unitdir}/clean-mount-point@.service
%{_unitdir}/mount-sd@.service
%{_udevrulesdir}/80-udisks2.rules
%{_sbindir}/umount.udisks2
%{_oneshotdir}/*
%dir %{_libexecdir}/udisks2
%{_libexecdir}/udisks2/udisksd

%{_bindir}/udisksctl

%{_datadir}/polkit-1/actions/org.freedesktop.UDisks2.policy
%{_datadir}/dbus-1/system-services/org.freedesktop.UDisks2.service

%files -n lib%{name}
%{_libdir}/libudisks2.so.*
%{_libdir}/girepository-1.0/UDisks-2.0.typelib

%files -n lib%{name}-devel
%doc COPYING NEWS README.md AUTHORS HACKING
%{_libdir}/libudisks2.so
%dir %{_includedir}/udisks2
%dir %{_includedir}/udisks2/udisks
%{_includedir}/udisks2/udisks/*.h
%{_datadir}/gir-1.0/UDisks-2.0.gir
%{_libdir}/pkgconfig/udisks2.pc
