%global glib2_version                   2.50
%global gobject_introspection_version   1.30.0
%global polkit_version                  0.102
%global systemd_version                 208
%global dbus_version                    1.4.0
%global libblockdev_version             2.25

Name:    udisks2
Summary: Disk Manager
Version: 2.9.4
Release: 1
License: GPLv2+
URL:     https://github.com/storaged-project/udisks
Source0: %{name}-%{version}.tar.bz2
Source1: udisks2-symlink-mount-path
Source2: udisks2-fs-mount-whitelist.txt

# i=1; for j in 00*patch; do printf "Patch%04d: %s\n" $i $j; i=$((i+1));done
Patch0001: 0001-Make-libblockdev-mdraid-and-part-support-optional.patch
Patch0002: 0002-Make-libatasmart-support-optional.patch
Patch0003: 0003-Loosen-up-polkit-policies-to-work-from-another-seat.patch
Patch0004: 0004-Introduce-mount-sd-service-that-is-executed-as-user.patch
Patch0005: 0005-Disable-zram-rule-for-now.patch
Patch0006: 0006-Create-mount-path-with-755-rights.patch
Patch0007: 0007-Make-it-possible-to-encrypt-mmcblk-format-with-encry.patch
Patch0008: 0008-Reduce-reserved-blocks-percentage-to-zero-for-ext2-e.patch
Patch0009: 0009-Allow-rescan-for-inactive.patch
Patch0010: 0010-Allow-whitelisting-filesystems-that-can-be-mounted.patch
Patch0011: 0011-Add-option-to-set-filesystem-group-permissions.patch
Patch0012: 0012-Always-mount-filesystems-using-the-UUID-instead-of-l.patch
Patch0013: 0013-Check-if-GTK_DOC_CHECK-is-defined-in-case-gtk-doc-is.patch
Patch0014: 0014-Add-workaround-in-case-gtk-doc-isn-t-installed.patch

BuildRequires: pkgconfig(glib-2.0) >= %{glib2_version}
BuildRequires: pkgconfig(gobject-introspection-1.0)
BuildRequires: pkgconfig(polkit-agent-1) >= %{polkit_version}
BuildRequires: pkgconfig(polkit-gobject-1) >= %{polkit_version}
BuildRequires: pkgconfig(systemd) >= %{systemd_version}
BuildRequires: pkgconfig(openssl)
BuildRequires: pkgconfig(mount) >= 2.30
BuildRequires: pkgconfig(dconf) >= 0.28.0
BuildRequires: pkgconfig(uuid)

BuildRequires: gettext-devel
BuildRequires: autoconf
BuildRequires: automake
BuildRequires: libxslt
BuildRequires: libtool
BuildRequires: libacl-devel
BuildRequires: chrpath
BuildRequires: pkgconfig(gudev-1.0) >= %{systemd_version}
BuildRequires: libblockdev-devel        >= %{libblockdev_version}
BuildRequires: libblockdev-loop-devel   >= %{libblockdev_version}
BuildRequires: libblockdev-swap-devel   >= %{libblockdev_version}
BuildRequires: libblockdev-fs-devel     >= %{libblockdev_version}
BuildRequires: libblockdev-part-devel   >= %{libblockdev_version}
BuildRequires: libblockdev-crypto-devel >= %{libblockdev_version}
BuildRequires: oneshot

Requires: libblockdev        >= %{libblockdev_version}
Requires: libblockdev-loop   >= %{libblockdev_version}
Requires: libblockdev-swap   >= %{libblockdev_version}
Requires: libblockdev-fs     >= %{libblockdev_version}
Requires: libblockdev-crypto >= %{libblockdev_version}
Requires: libblockdev-part   >= %{libblockdev_version}

%{?systemd_requires}

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
Requires: libmount >= 2.30
# The actual polkit agent
Requires: polkit >= %{polkit_version}

Requires: lib%{name} = %{version}-%{release}

%{_oneshot_requires_post}

Obsoletes: sd-utils < 0.1.6
Provides: sd-utils >= 0.1.6

%description
The Udisks project provides a daemon, tools and libraries to access and
manipulate disks, storage devices and technologies.

%package -n lib%{name}
Summary: Dynamic library to access the udisksd daemon
License: LGPLv2+

%description -n lib%{name}
This package contains the dynamic library, which provides
access to the udisksd daemon.

%package -n lib%{name}-devel
Summary: Development files for lib%{name}
Requires: lib%{name} = %{version}-%{release}
License: LGPLv2+

%description -n lib%{name}-devel
This package contains the development files for the library lib%{name}, a
dynamic library, which provides access to the udisksd daemon.

%prep
%autosetup -p1 -n %{name}-%{version}/%{name}

%build
# Disable gtk-doc
# Those need to be defined because the upstream Makefile boilerplate
# (doc/reference/Makefile.am) relies on them.
cat > gtk-doc.make <<EOF
EXTRA_DIST =
CLEANFILES =
EOF

glib-gettextize --force --copy
autoreconf -vfi -Wno-portability
%configure \
    --sysconfdir=/etc \
    --enable-man=no \
    --prefix=%{_prefix}
%make_build

%install
%make_install

chrpath --delete %{buildroot}/%{_sbindir}/umount.udisks2
chrpath --delete %{buildroot}/%{_bindir}/udisksctl
chrpath --delete %{buildroot}/%{_libexecdir}/udisks2/udisksd

mkdir -p %{buildroot}/%{_oneshotdir}/
install -m 0755 %{SOURCE1} %{buildroot}/%{_oneshotdir}

mkdir -p %{buildroot}/%{_sysconfdir}/dconf/db/vendor.d/locks/
install -m 0644 %{SOURCE2} %{buildroot}/%{_sysconfdir}/dconf/db/vendor.d/locks/

chmod +x %{buildroot}/%{_bindir}/udisksctl-user

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
%license COPYING

%dir %{_sysconfdir}/udisks2
%{_sysconfdir}/udisks2/udisks2.conf

%{_datadir}/dbus-1/system.d/org.freedesktop.UDisks2.conf
%{_sysconfdir}/dconf/db/vendor.d/locks/*
%{_datadir}/bash-completion/completions/udisksctl
%{_unitdir}/udisks2.service
%{_unitdir}/mount-sd@.service
%{_udevrulesdir}/80-udisks2.rules
%{_tmpfilesdir}/udisks2.conf
%{_sbindir}/umount.udisks2
%{_oneshotdir}/*
%dir %{_libexecdir}/udisks2
%{_libexecdir}/udisks2/udisksd

%{_bindir}/udisksctl
%{_bindir}/udisksctl-user

%{_datadir}/polkit-1/actions/org.freedesktop.UDisks2.policy
%{_datadir}/dbus-1/system-services/org.freedesktop.UDisks2.service

%files -n lib%{name}
%{_libdir}/libudisks2.so.*
%{_libdir}/girepository-1.0/UDisks-2.0.typelib

%files -n lib%{name}-devel
%doc NEWS README.md AUTHORS HACKING
%{_sysconfdir}/udisks2/mount_options.conf.example
%{_libdir}/libudisks2.so
%dir %{_includedir}/udisks2
%dir %{_includedir}/udisks2/udisks
%{_includedir}/udisks2/udisks/*.h
%{_datadir}/gir-1.0/UDisks-2.0.gir
%{_libdir}/pkgconfig/udisks2.pc
