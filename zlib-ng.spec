# when building for old (pre 4.3) releases,
# set bcond_with replace_zlib
# to avoid replacing traditional zlib
%bcond_without replace_zlib

%global optflags %{optflags} -O3

%define major 1
%define ngmajor 2

%define libname %mklibname z %{major}
%define develname %mklibname z -d

%define nglibname %mklibname z-ng %{major}
%define ngdevelname %mklibname z-ng -d

%ifarch %{x86_64}
%define lib32name libz%{major}
%define dev32name libz-devel

%define nglib32name libz-ng%{major}
%define ngdev32name libz-ng-devel
%endif

# (tpg) enable PGO build
%ifnarch riscv64
%bcond_without pgo
%else
%bcond_with pgo
%endif

Summary:	Zlib replacement with optimizations
Name:		zlib-ng
Version:	2.0.2
Release:	3
License:	zlib
Group:		System/Libraries
Url:		https://github.com/zlib-ng/zlib-ng
Source0:	https://github.com/zlib-ng/zlib-ng/archive/%{version}/%{name}-%{version}.tar.gz
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
The %{name}-devel package contains static libraries and header files for
developing application that use %{name}.

%ifarch %{x86_64}
%package -n %{lib32name}
Summary:	%{summary} (32-bit)
Group:		System/Libraries
Conflicts:	zlib1 < 1.2.6-3

%description -n %{lib32name}
%{description} (32-bit)

%package -n %{dev32name}
Summary:	Development files for %{name} (32-bit)
Group:		Development/C
Requires:	%{lib32name} = %{version}-%{release}
Requires:	%{develname} = %{version}-%{release}
%rename		zlib-devel

%description -n %{dev32name}
The %{name}-devel package contains static libraries and header files for
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
Requires:	%{libname} = %{EVRD}

%description -n %{ngdevelname}
The %{name}-devel package contains static libraries and header files for
developing application that use %{name}.

%ifarch %{x86_64}
%package -n %{nglib32name}
Summary:	%{summary} (32-bit)
Group:		System/Libraries

%description -n %{nglib32name}
%{description} (32-bit)

%package -n %{ngdev32name}
Summary:	Development files for %{name} (32-bit)
Group:		Development/C
Requires:	%{nglib32name} = %{version}-%{release}
Requires:	%{ngdevelname} = %{version}-%{release}

%description -n %{ngdev32name}
The %{name}-devel package contains static libraries and header files for
developing application that use %{name} (32-bit).
%endif

%prep
%autosetup -p1

%build
%ifarch %{x86_64}
%if %{with replace_zlib}
%cmake32 \
	-DZLIB_COMPAT:BOOL=ON \
	-G Ninja

%ninja_build
cd ..
%endif

CMAKE_BUILD_DIR32=build32-ng \
%cmake32 \
	-DZLIB_COMPAT:BOOL=OFF \
	-G Ninja

%ninja_build
cd ..
%endif

%if %{with pgo}
%if %{with replace_zlib}
CFLAGS="%{optflags} -fprofile-instr-generate"
CXXFLAGS="%{optflags} -fprofile-instr-generate"
FFLAGS="$CFLAGS"
FCFLAGS="$CFLAGS"
LDFLAGS="%{build_ldflags} -fprofile-instr-generate"
export LLVM_PROFILE_FILE=%{name}-%p.profile.d
export LD_LIBRARY_PATH="$(pwd)"

# zlib-ng uses a different macro for library directory.
%cmake \
	-DWITH_SANITIZERS=ON \
	-DINSTALL_LIB_DIR=%{_libdir} \
	-DZLIB_COMPAT:BOOL=ON \
	-G Ninja

%ninja_build

%ninja_test ||:
unset LD_LIBRARY_PATH
unset LLVM_PROFILE_FILE
llvm-profdata merge --output=../%{name}.profile *.profile.d
rm -f *.profile.d
ninja clean
cd ..
rm -rf build

CFLAGS="%{optflags} -fprofile-instr-use=$(realpath %{name}.profile)" \
CXXFLAGS="%{optflags} -fprofile-instr-use=$(realpath %{name}.profile)" \
LDFLAGS="%{ldflags} -fprofile-instr-use=$(realpath %{name}.profile)" \
%endif
%cmake \
	-DWITH_SANITIZERS=ON \
	-DINSTALL_LIB_DIR=%{_libdir} \
%if %{with replace_zlib}
	-DZLIB_COMPAT:BOOL=ON \
%endif
	-G Ninja

%ninja_build
cd ..
%endif

%if %{with replace_zlib}
%if %{with pgo}
CFLAGS="%{optflags} -fprofile-instr-generate"
CXXFLAGS="%{optflags} -fprofile-instr-generate"
FFLAGS="$CFLAGS"
FCFLAGS="$CFLAGS"
LDFLAGS="%{build_ldflags} -fprofile-instr-generate"
export LLVM_PROFILE_FILE=%{name}-%p.profile.d
export LD_LIBRARY_PATH="$(pwd)"

export CMAKE_BUILD_DIR=build-ng
# zlib-ng uses a different macro for library directory.
%cmake \
	-DWITH_SANITIZERS=ON \
	-DINSTALL_LIB_DIR=%{_libdir} \
	-DZLIB_COMPAT:BOOL=OFF \
	-G Ninja

%ninja_build

%ninja_test ||:
unset LD_LIBRARY_PATH
unset LLVM_PROFILE_FILE
llvm-profdata merge --output=../%{name}.profile *.profile.d
rm -f *.profile.d
ninja clean
cd ..
rm -rf build-ng

CFLAGS="%{optflags} -fprofile-instr-use=$(realpath %{name}.profile)" \
CXXFLAGS="%{optflags} -fprofile-instr-use=$(realpath %{name}.profile)" \
LDFLAGS="%{ldflags} -fprofile-instr-use=$(realpath %{name}.profile)" \
%endif
%cmake \
	-DWITH_SANITIZERS=ON \
	-DINSTALL_LIB_DIR=%{_libdir} \
	-DZLIB_COMPAT:BOOL=OFF \
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
%endif

%files -n %{ngdevelname}
%{_includedir}/zlib-ng.h
%{_includedir}/zconf-ng.h
%{_libdir}/libz-ng.so
%{_libdir}/pkgconfig/zlib-ng.pc

%ifarch %{x86_64}
%if %{with replace_zlib}
%files -n %{lib32name}
%{_prefix}/lib/libz.so.%{major}*

%files -n %{dev32name}
%{_prefix}/lib/libz.so
%{_prefix}/lib/pkgconfig/zlib.pc
%endif

%files -n %{nglib32name}
%{_prefix}/lib/libz-ng.so.%{ngmajor}*

%files -n %{ngdev32name}
%{_prefix}/lib/libz-ng.so
%{_prefix}/lib/pkgconfig/zlib-ng.pc
%endif
