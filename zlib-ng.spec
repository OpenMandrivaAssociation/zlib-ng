# when building for old (pre 4.3) releases,
# set bcond_with replace_zlib
# to avoid replacing traditional zlib
%bcond_without replace_zlib

%global optflags %{optflags} -O3

%if %{with replace_zlib}
%define major 1
%else
%define major 2
%endif

%define libname %mklibname %{name} %{major}
%define develname %mklibname %{name} -d

%ifarch %{x86_64}
%define lib32name lib%{name}%{major}
%define dev32name lib%{name}-devel
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
Release:	1
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
%if %{with replace_zlib}
%rename		%{_lib}zlib1
%rename		zlib
%rename		zlib1
%rename		%{_lib}z1_
Provides:	%{_lib}z1 = %{EVRD}
Obsoletes:	%{_lib}z1 < 2.0.1
Provides:	%{_lib}z1%{_isa} = %{EVRD}
%endif

%description -n %{libname}
%{description}

%package -n %{develname}
Summary:	Development files for %{name}
Group:		Development/C
Requires:	%{libname} = %{EVRD}
%if %{with replace_zlib}
%rename		%{_lib}z-devel
%rename		zlib-devel
%rename		zlib1-devel
Provides:	%{_lib}z-devel = %{EVRD}
Obsoletes:	%{_lib}z-devel < 2.0.1
%endif

%description -n %{develname}
The %{name}-devel package contains static libraries and header files for
developing application that use %{name}.

%ifarch %{x86_64}
%package -n %{lib32name}
Summary:	%{summary} (32-bit)
Group:		System/Libraries
%if %{with replace_zlib}
%rename		libz-devel
Conflicts:	zlib1 < 1.2.6-3
Provides:	libz1 = %{EVRD}
Obsoletes:	libz1 < 2.0.1
Provides:	libz1%{_isa} = %{EVRD}
%endif

%description -n %{lib32name}
%{description} (32-bit)

%package -n %{dev32name}
Summary:	Development files for %{name} (32-bit)
Group:		Development/C
Requires:	%{lib32name} = %{version}-%{release}
Requires:	%{develname} = %{version}-%{release}
%if %{with replace_zlib}
Provides:	libz-devel = %{EVRD}
%endif

%description -n %{dev32name}
The %{name}-devel package contains static libraries and header files for
developing application that use %{name} (32-bit).
%endif

%prep
%autosetup -p1

%build
%ifarch %{x86_64}
%cmake32 \
%if %{with replace_zlib}
	-DZLIB_COMPAT=ON \
%endif
	-G Ninja

%ninja_build
cd ..
%endif

%if %{with pgo}
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
%if %{with replace_zlib}
	-DZLIB_COMPAT=ON \
%endif
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
	-DZLIB_COMPAT=ON \
%endif
	-G Ninja

%ninja_build

%install
%ifarch %{x86_64}
install -d %{buildroot}%{_prefix}/lib
%ninja_install -C build32
%endif

%ninja_install -C build

%files -n %{libname}
%license LICENSE.md
%doc README.md
%{_libdir}/libz*so.%{major}*

%files -n %{develname}
%{_includedir}/*.h
%{_libdir}/libz*.so
%{_libdir}/pkgconfig/*.pc

%ifarch %{x86_64}
%files -n %{lib32name}
%{_prefix}/lib/libz*so.%{major}*

%files -n %{dev32name}
%{_prefix}/lib/libz*.so
%{_prefix}/lib/pkgconfig/*.pc
%endif
