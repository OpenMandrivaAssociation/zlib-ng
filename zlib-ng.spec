# when building for old (pre 4.3) releases,
# set bcond_with replace_zlib
# to avoid replacing traditional zlib
%bcond_without replace_zlib

# Please don't disable static libraries -- qemu needs them

%global optflags %{optflags} -O3

%define major 1
%define ngmajor 2

%define libname %mklibname z %{major}
%define develname %mklibname z -d
%define sdevelname %mklibname z -d -s

%define nglibname %mklibname z-ng %{major}
%define ngdevelname %mklibname z-ng -d
%define ngsdevelname %mklibname z-ng -d -s

%ifarch %{x86_64}
%define lib32name libz%{major}
%define dev32name libz-devel
%define sdev32name libz-static-devel

%define nglib32name libz-ng%{major}
%define ngdev32name libz-ng-devel
%define ngsdev32name libz-ng-static-devel
%endif

# (tpg) enable PGO build
%bcond_without pgo

Summary:	Zlib replacement with optimizations
Name:		zlib-ng
Version:	2.0.6
Release:	4
License:	zlib
Group:		System/Libraries
Url:		https://github.com/zlib-ng/zlib-ng
Source0:	https://github.com/zlib-ng/zlib-ng/archive/%{version}/%{name}-%{version}.tar.gz
Patch0:		zlib-ng-2.0.2-pkgconfig-fix-libtool-mess.patch
# (tpg) patches from upstream stable branch
# (currently none)

BuildRequires:	cmake
BuildRequires:	ninja

%description
zlib-ng is a zlib replacement that provides optimizations for "next generation"
systems.

%package -n %{libname}
Summary:	%{summary}
Group:		System/Libraries
%rename		%{_lib}zlib1
%rename		zlib
%rename		zlib1
%rename		%{_lib}z1_

%description -n %{libname}
%{description}

%package -n %{develname}
Summary:	Development files for %{name}
Group:		Development/C
Requires:	%{libname} = %{EVRD}
%rename		zlib-devel
%rename		zlib1-devel

%description -n %{develname}
The %{name}-devel package contains header files for
developing application that use %{name}.

%package -n %{sdevelname}
Summary:	Static libraries for %{name}
Group:		Development/C
Requires:	%{develname} = %{EVRD}
Provides:	zlib-static-devel = %{EVRD}

%description -n %{sdevelname}
The %{name}-static-devel package contains static libraries for
developing application that use %{name}.

%ifarch %{x86_64}
%package -n %{lib32name}
Summary:	%{summary} (32-bit)
Group:		System/Libraries
Conflicts:	zlib1 < 1.2.6-3
BuildRequires:	libc6
Requires:	libc6

%description -n %{lib32name}
%{description} (32-bit).

%package -n %{dev32name}
Summary:	Development files for %{name} (32-bit)
Group:		Development/C
Requires:	%{lib32name} = %{version}-%{release}
Requires:	%{develname} = %{version}-%{release}
%rename		zlib-devel

%description -n %{dev32name}
The %{name}-devel package contains header files for
developing application that use %{name} (32-bit).

%package -n %{sdev32name}
Summary:	Static libraries for %{name} (32-bit)
Group:		Development/C
Requires:	%{dev32name} = %{version}-%{release}
%rename		zlib-devel

%description -n %{sdev32name}
The %{name}-devel package contains static libraries for
developing application that use %{name} (32-bit).
%endif

%package -n %{nglibname}
Summary:	%{summary}
Group:		System/Libraries

%description -n %{nglibname}
%{description}

%package -n %{ngdevelname}
Summary:	Development files for %{name}
Group:		Development/C
Requires:	%{nglibname} = %{EVRD}

%description -n %{ngdevelname}
The %{name}-devel package contains header files for
developing application that use %{name}.

%package -n %{ngsdevelname}
Summary:	Static libraries for %{name}
Group:		Development/C
Requires:	%{ngdevelname} = %{EVRD}

%description -n %{ngsdevelname}
The %{name}-devel package contains static libraries for
developing application that use %{name}.

%ifarch %{x86_64}
%package -n %{nglib32name}
Summary:	%{summary} (32-bit)
Group:		System/Libraries

%description -n %{nglib32name}
%{description} (32-bit).

%package -n %{ngdev32name}
Summary:	Development files for %{name} (32-bit)
Group:		Development/C
Requires:	%{nglib32name} = %{version}-%{release}
Requires:	%{ngdevelname} = %{version}-%{release}

%description -n %{ngdev32name}
The %{name}-devel package contains header files for
developing application that use %{name} (32-bit).

%package -n %{ngsdev32name}
Summary:	Static libraries for %{name} (32-bit)
Group:		Development/C
Requires:	%{ngdev32name} = %{version}-%{release}

%description -n %{ngsdev32name}
The %{name}-devel package contains static libraries for
developing application that use %{name} (32-bit).
%endif

%prep
%autosetup -p1

%build
# zlib-ng uses nonstandard behavior for BUILD_SHARED_LIBS/BUILD_STATIC_LIBS
# BUILD_SHARED_LIBS=ON here means build ONLY shared libs
# BUILD_STATIC_LIBS=ON is ignored
# BUILD_SHARED_LIBS unset means build both shared and static libs.

%ifarch %{x86_64}
%if %{with replace_zlib}
%cmake32 \
	-DZLIB_COMPAT:BOOL=ON \
	-UBUILD_SHARED_LIBS \
	-G Ninja

%ninja_build
cd ..
%endif

CMAKE_BUILD_DIR32=build32-ng \
%cmake32 \
	-DZLIB_COMPAT:BOOL=OFF \
	-UBUILD_SHARED_LIBS \
	-G Ninja

%ninja_build
cd ..
%endif

%if %{with pgo}
%if %{with replace_zlib}
export LD_LIBRARY_PATH="$(pwd)"

CFLAGS="%{optflags} -fprofile-generate" \
CXXFLAGS="%{optflags} -fprofile-generate" \
FFLAGS="$CFLAGS" \
FCFLAGS="$CFLAGS" \
LDFLAGS="%{build_ldflags} -fprofile-generate" \
%cmake \
	-DWITH_SANITIZERS=ON \
	-DINSTALL_LIB_DIR=%{_libdir} \
	-DZLIB_COMPAT:BOOL=ON \
	-UBUILD_SHARED_LIBS \
	-G Ninja

%ninja_build

%ninja_test ||:
unset LD_LIBRARY_PATH
llvm-profdata merge --output=../%{name}-llvm.profdata $(find . -name "*.profraw" -type f)
PROFDATA="$(realpath ../%{name}-llvm.profdata)"
rm -f *.profraw
ninja clean
cd ..
rm -rf build

CFLAGS="%{optflags} -fprofile-use=$PROFDATA" \
CXXFLAGS="%{optflags} -fprofile-use=$PROFDATA" \
LDFLAGS="%{build_ldflags} -fprofile-use=$PROFDATA" \
%endif
%cmake \
	-DWITH_SANITIZERS=ON \
	-DINSTALL_LIB_DIR=%{_libdir} \
%if %{with replace_zlib}
	-DZLIB_COMPAT:BOOL=ON \
%endif
	-UBUILD_SHARED_LIBS \
	-G Ninja

%ninja_build
cd ..
%endif

%if %{with replace_zlib}
%if %{with pgo}
export LD_LIBRARY_PATH="$(pwd)"
export CMAKE_BUILD_DIR=build-ng

CFLAGS="%{optflags} -fprofile-generate" \
CXXFLAGS="%{optflags} -fprofile-generate" \
FFLAGS="$CFLAGS" \
FCFLAGS="$CFLAGS" \
LDFLAGS="%{build_ldflags} -fprofile-generate" \
%cmake \
	-DWITH_SANITIZERS=ON \
	-DINSTALL_LIB_DIR=%{_libdir} \
	-DZLIB_COMPAT:BOOL=OFF \
	-UBUILD_SHARED_LIBS \
	-G Ninja

%ninja_build

%ninja_test ||:
unset LD_LIBRARY_PATH
llvm-profdata merge --output=../%{name}-llvm.profdata $(find . -name "*.profraw" -type f)
PROFDATA="$(realpath ../%{name}-llvm.profdata)"
rm -f *.profraw
ninja clean
cd ..
rm -rf build-ng

CFLAGS="%{optflags} -fprofile-use=$PROFDATA" \
CXXFLAGS="%{optflags} -fprofile-use=$PROFDATA" \
LDFLAGS="%{build_ldflags} -fprofile-use=$PROFDATA" \
%endif
%cmake \
	-DWITH_SANITIZERS=ON \
	-DINSTALL_LIB_DIR=%{_libdir} \
	-DZLIB_COMPAT:BOOL=OFF \
	-UBUILD_SHARED_LIBS \
	-G Ninja

%ninja_build
%endif

%install
%ifarch %{x86_64}
install -d %{buildroot}%{_prefix}/lib
%if %{with replace_zlib}
%ninja_install -C build32
%endif

%ninja_install -C build32-ng
%endif

%if %{with replace_zlib}
%ninja_install -C build
%endif

%ninja_install -C build-ng

%if %{with replace_zlib}
%files -n %{libname}
%license LICENSE.md
%doc README.md
%{_libdir}/libz.so.%{major}*
%endif

%files -n %{nglibname}
%license LICENSE.md
%doc README.md
%{_libdir}/libz-ng.so.%{ngmajor}*

%if %{with replace_zlib}
%files -n %{develname}
%{_includedir}/zlib.h
%{_includedir}/zconf.h
%{_libdir}/libz.so
%{_libdir}/pkgconfig/zlib.pc

%files -n %{sdevelname}
%{_libdir}/libz.a
%endif

%files -n %{ngdevelname}
%{_includedir}/zlib-ng.h
%{_includedir}/zconf-ng.h
%{_libdir}/libz-ng.so
%{_libdir}/pkgconfig/zlib-ng.pc

%files -n %{ngsdevelname}
%{_libdir}/libz-ng.a

%ifarch %{x86_64}
%if %{with replace_zlib}
%files -n %{lib32name}
%{_prefix}/lib/libz.so.%{major}*

%files -n %{dev32name}
%{_prefix}/lib/libz.so
%{_prefix}/lib/pkgconfig/zlib.pc

%files -n %{sdev32name}
%{_prefix}/lib/libz.a
%endif

%files -n %{nglib32name}
%{_prefix}/lib/libz-ng.so.%{ngmajor}*

%files -n %{ngdev32name}
%{_prefix}/lib/libz-ng.so
%{_prefix}/lib/pkgconfig/zlib-ng.pc

%files -n %{ngsdev32name}
%{_prefix}/lib/libz-ng.a
%endif
