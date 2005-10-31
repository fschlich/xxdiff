Summary: A graphical front end to the diff command
Name: xxdiff
Version: 2.0.2
Release: 1
Copyright: GNU GPL
Group: Development/Tools
Source: http://prdownloads.sourceforge.net/xxdiff/xxdiff-%{version}.tar.gz
URL: http://xxdiff.sourceforge.net
Packager: Martin Blais <blais@iro.umontreal.ca>
Buildroot: %{_tmppath}/%{name}-%{version}-root
Requires: qt
BuildRequires: qt-devel tmake

%description
xxdiff is a graphical browser for viewing the differences between two
files and can be used to produce a merged version.  The text of the
two or three files are presented side by side with their differences
highlighted for easy identification.

%prep
%setup -q

%build
if [ -z "$QTDIR" ]; then 
	. /etc/profile.d/qt.sh
fi

cd src
tmake xxdiff.pro > Makefile
make

%install
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf $RPM_BUILD_ROOT

mkdir -p ${RPM_BUILD_ROOT}/usr/X11R6/bin

install -c -m 755 -s src/xxdiff ${RPM_BUILD_ROOT}/usr/X11R6/bin/

%clean
[ "${RPM_BUILD_ROOT}" != "/" ] && rm -rf ${RPM_BUILD_ROOT}

%files
%defattr(-,root, root)
%doc README
%doc CHANGES

/usr/X11R6/bin/xxdiff


%changelog
* Sun Nov 5 2001 Martin Blais <blais@discreet.com>
- Made it work with tmake.

* Tue Jul 24 2001 Martin Blais <blais@discreet.com>
- added defattr field, thanks to Mirko Zeibig for suggestion.

* Thu Jun  7 2001 Martin Blais <blais@discreet.com> 1.13
- released 1.13

* Thu Jun  7 2001 Martin Blais <blais@discreet.com> 1.12-2
- don't reset QTDIR if it is already set.

* Mon Jun  4 2001 Martin Blais <blais@iro.umontreal.ca>
- fixed for QTDIR

* Mon Jun  4 2001 Martin Blais <blais@discreet.com> 1.12-1
- 1.12

* Wed May 30 2001 Peder Stray <peder@linpro.no>
- fixed .spec-file

* Tue May 29 2001 Martin Blais <blais@discreet.com> 1.11.0-1
- 1.11.0