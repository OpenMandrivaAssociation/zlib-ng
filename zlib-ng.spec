# (tpg) when ready to ditch zlib
# add -DZLIB_COMPAT=ON 
# and adjust major, provides, requires and obsoletes

%global optflags %{optflags} -O3

%define major 1
%define libname %mklibname %{name} %{major}
%define develname %mklibname %{name} -d

%bcond_without compat32

%if %{with compat32}
%define lib32name lib%{name}%{major}
%define dev32name lib%{name}-devel
%endif

# (tpg) enable PGO build
%ifnarch riscv64
%bcond_with pgo
%else
%bcond_with pgo
%endif

Summary:	Zlib replacement with optimizations
Name:		zlib-ng
Version:	2.0.1
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

%description -n %{libname}
%{description}

%package -n %{develname}
Summary:	Development files for %{name}
Group:		Development/C
Requires:	%{libname}= %{EVRD}

%description -n %{develname}
The %{name}-devel package contains static libraries and header files for
developing application that use %{name}.

%prep
%autosetup -p1

%build
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
	-DZLIB_COMPAT=ON \
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
	-DZLIB_COMPAT=ON \
	-G Ninja

%ninja_build
    
%check
#ninja_test -C build

%install
%ninja_install -C build

%files -n %{libname}
%license LICENSE.md
%doc README.md
%{_libdir}/libz*.so.%{major}*

%files -n %{develname}
%{_includedir}/*.h
%{_includedir}/*.h
%{_libdir}/libz*.so
%{_libdir}/pkgconfig/*.pc
