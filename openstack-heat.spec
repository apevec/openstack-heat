#
# This is 2013.1 grizzly-rc1 milestone
#
%global release_name grizzly
%global release_letter rc
%global milestone 1

%global with_doc %{!?_without_doc:1}%{?_without_doc:0}

Name:		openstack-heat
Summary:	OpenStack Orchestration (heat)
Version:	2013.1
Release:	0.8.%{release_letter}%{milestone}%{?dist}
License:	ASL 2.0
Group:		System Environment/Base
URL:		http://www.openstack.org
Source0:	https://launchpad.net/heat/%{release_name}/%{release_name}-%{release_letter}%{milestone}/+download/heat-%{version}.%{release_letter}%{milestone}.tar.gz
Obsoletes:	heat < 7-2
Provides:	heat

Source1:	heat.logrotate
Source2:	openstack-heat-api.init
Source3:	openstack-heat-api-cfn.init
Source4:	openstack-heat-engine.init
Source5:	openstack-heat-api-cloudwatch.init

BuildArch: noarch
BuildRequires: python2-devel
BuildRequires: python-setuptools
BuildRequires: python-sphinx10

Requires: %{name}-common = %{version}-%{release}
Requires: %{name}-engine = %{version}-%{release}
Requires: %{name}-api = %{version}-%{release}
Requires: %{name}-api-cfn = %{version}-%{release}
Requires: %{name}-api-cloudwatch = %{version}-%{release}
Requires: %{name}-cli = %{version}-%{release}

%prep
%setup -q -n heat-%{version}.%{release_letter}%{milestone}

%build
%{__python} setup.py build

%install
%{__python} setup.py install -O1 --skip-build --root=%{buildroot}
sed -i -e '/^#!/,1 d' %{buildroot}/%{python_sitelib}/heat/db/sqlalchemy/manage.py
sed -i -e '/^#!/,1 d' %{buildroot}/%{python_sitelib}/heat/db/sqlalchemy/migrate_repo/manage.py
sed -i -e '/^#!/,1 d' %{buildroot}/%{python_sitelib}/heat/testing/runner.py
mkdir -p %{buildroot}/var/log/heat/
install -p -D -m 644 %{SOURCE1} %{buildroot}%{_sysconfdir}/logrotate.d/openstack-heat

# install init scripts
install -p -D -m 755 %{SOURCE2} %{buildroot}%{_initrddir}/openstack-heat-api
install -p -D -m 755 %{SOURCE3} %{buildroot}%{_initrddir}/openstack-heat-api-cfn
install -p -D -m 755 %{SOURCE4} %{buildroot}%{_initrddir}/openstack-heat-engine
install -p -D -m 755 %{SOURCE5} %{buildroot}%{_initrddir}/openstack-heat-api-cloudwatch

mkdir -p %{buildroot}/var/lib/heat/
mkdir -p %{buildroot}/etc/heat/

export PYTHONPATH="$( pwd ):$PYTHONPATH"
pushd doc
sphinx-1.0-build -b html -d build/doctrees source build/html
sphinx-1.0-build -b man -d build/doctrees source build/man

mkdir -p %{buildroot}%{_mandir}/man1
install -p -D -m 644 build/man/*.1 %{buildroot}%{_mandir}/man1/
popd

rm -rf %{buildroot}/var/lib/heat/.dummy
rm -f %{buildroot}/usr/bin/cinder-keystone-setup

install -p -D -m 640 %{_builddir}/heat-%{version}.%{release_letter}%{milestone}/etc/heat/heat-api.conf %{buildroot}/%{_sysconfdir}/heat
install -p -D -m 640 %{_builddir}/heat-%{version}.%{release_letter}%{milestone}/etc/heat/heat-api-paste.ini %{buildroot}/%{_sysconfdir}/heat
install -p -D -m 640 %{_builddir}/heat-%{version}.%{release_letter}%{milestone}/etc/heat/heat-api-cfn.conf %{buildroot}/%{_sysconfdir}/heat
install -p -D -m 640 %{_builddir}/heat-%{version}.%{release_letter}%{milestone}/etc/heat/heat-api-cfn-paste.ini %{buildroot}/%{_sysconfdir}/heat
install -p -D -m 640 %{_builddir}/heat-%{version}.%{release_letter}%{milestone}/etc/heat/heat-api-cloudwatch.conf %{buildroot}/%{_sysconfdir}/heat
install -p -D -m 640 %{_builddir}/heat-%{version}.%{release_letter}%{milestone}/etc/heat/heat-api-cloudwatch-paste.ini %{buildroot}/%{_sysconfdir}/heat
install -p -D -m 640 %{_builddir}/heat-%{version}.%{release_letter}%{milestone}/etc/heat/heat-engine.conf %{buildroot}/%{_sysconfdir}/heat
install -p -D -m 640 %{_builddir}/heat-%{version}.%{release_letter}%{milestone}/etc/boto.cfg %{buildroot}/%{_sysconfdir}/heat
install -p -D -m 644 %{_builddir}/heat-%{version}.%{release_letter}%{milestone}/etc/bash_completion.d/heat-cfn %{buildroot}/%{_sysconfdir}/bash_completion.d/heat-cfn

%description
Heat provides AWS CloudFormation and CloudWatch functionality for OpenStack.


%package common
Summary: Heat common
Group: System Environment/Base

Requires: python-argparse
Requires: python-boto
Requires: python-crypto
Requires: python-eventlet
Requires: python-greenlet
Requires: python-httplib2
Requires: python-iso8601
Requires: python-kombu
Requires: python-lxml
Requires: python-paste
Requires: python-cinderclient
Requires: python-keystoneclient
Requires: python-memcached
Requires: python-novaclient
Requires: python-oslo-config
Requires: python-quantumclient
Requires: python-swiftclient
Requires: python-routes
Requires: python-sqlalchemy
Requires: python-migrate
Requires: python-qpid
Requires: python-webob
Requires: PyYAML

Requires(pre): shadow-utils

%description common
Components common to all OpenStack Heat services

%files common
%doc LICENSE
%{_bindir}/heat-db-setup
%{_bindir}/heat-keystone-setup
%{python_sitelib}/heat*
%dir %attr(0755,heat,root) %{_localstatedir}/log/heat
%dir %attr(0755,heat,root) %{_sharedstatedir}/heat
%dir %attr(0755,heat,root) %{_sysconfdir}/heat
%config(noreplace) %{_sysconfdir}/logrotate.d/openstack-heat
%{_mandir}/man1/heat-db-setup.1.gz
%{_mandir}/man1/heat-keystone-setup.1.gz

%pre common
# 187:187 for heat - rhbz#845078
getent group heat >/dev/null || groupadd -r --gid 187 heat
getent passwd heat  >/dev/null || \
useradd --uid 187 -r -g heat -d %{_sharedstatedir}/heat -s /sbin/nologin \
-c "OpenStack Heat Daemons" heat
exit 0

%package engine
Summary: The Heat engine
Group: System Environment/Base

Requires: %{name}-common = %{version}-%{release}

Requires(post): chkconfig
Requires(preun): chkconfig
Requires(preun): initscripts
Requires(postun): initscripts

%description engine
OpenStack API for starting CloudFormation templates on OpenStack

%files engine
%doc README.rst LICENSE doc/build/html/man/heat-engine.html
%{_bindir}/heat-engine
%config(noreplace) %attr(-,root,heat) %{_sysconfdir}/heat/heat-engine.conf
%{_initrddir}/openstack-heat-engine
%{_mandir}/man1/heat-engine.1.gz

%post engine
/sbin/chkconfig --add openstack-heat-engine

%preun engine
if [ $1 -eq 0 ]; then
    /sbin/service openstack-heat-engine stop >/dev/null 2>&1
    /sbin/chkconfig --del openstack-heat-engine
fi

%postun engine
if [ $1 -ge 1 ]; then
    /sbin/service openstack-heat-engine condrestart >/dev/null 2>&1 || :
fi


%package api
Summary: The Heat API
Group: System Environment/Base

Requires: %{name}-common = %{version}-%{release}

Requires(post): chkconfig
Requires(preun): chkconfig
Requires(preun): initscripts
Requires(postun): initscripts

%description api
OpenStack-native ReST API to the Heat Engine

%files api
%doc README.rst LICENSE doc/build/html/man/heat-api.html
%{_bindir}/heat-api
%config(noreplace) %attr(-,root,heat) %{_sysconfdir}/heat/heat-api.conf
%config(noreplace) %attr(-,root,heat) %{_sysconfdir}/heat/heat-api-paste.ini
%{_initrddir}/openstack-heat-api
%{_mandir}/man1/heat-api.1.gz

%post api
/sbin/chkconfig --add openstack-heat-api

%preun api
if [ $1 -eq 0 ]; then
    /sbin/service openstack-heat-api stop >/dev/null 2>&1
    /sbin/chkconfig --del openstack-heat-api
fi

%postun api
if [ $1 -ge 1 ]; then
    /sbin/service openstack-heat-api condrestart >/dev/null 2>&1 || :
fi


%package api-cfn
Summary: Heat CloudFormation API
Group: System Environment/Base

Requires: %{name}-common = %{version}-%{release}

Requires(post): chkconfig
Requires(preun): chkconfig
Requires(preun): initscripts
Requires(postun): initscripts

%description api-cfn
AWS CloudFormation-compatible API to the Heat Engine

%files api-cfn
%doc README.rst LICENSE doc/build/html/man/heat-api-cfn.html
%{_bindir}/heat-api-cfn
%config(noreplace) %attr(-,root,heat) %{_sysconfdir}/heat/heat-api-cfn.conf
%config(noreplace) %attr(-,root,heat) %{_sysconfdir}/heat/heat-api-cfn-paste.ini
%{_initrddir}/openstack-heat-api-cfn
%{_mandir}/man1/heat-api-cfn.1.gz

%post api-cfn
/sbin/chkconfig --add openstack-heat-api-cfn

%preun api-cfn
if [ $1 -eq 0 ]; then
    /sbin/service openstack-heat-api-cfn stop >/dev/null 2>&1
    /sbin/chkconfig --del openstack-heat-api-cfn
fi

%postun api-cfn
if [ $1 -ge 1 ]; then
    /sbin/service openstack-heat-api-cfn condrestart >/dev/null 2>&1 || :
fi


%package api-cloudwatch
Summary: Heat CloudWatch API
Group: System Environment/Base

Requires: %{name}-common = %{version}-%{release}

Requires(post): chkconfig
Requires(preun): chkconfig
Requires(preun): initscripts
Requires(postun): initscripts

%description api-cloudwatch
AWS CloudWatch-compatible API to the Heat Engine

%files api-cloudwatch
%doc README.rst LICENSE doc/build/html/man/heat-api-cloudwatch.html
%{_bindir}/heat-api-cloudwatch
%config(noreplace) %attr(-,root,heat) %{_sysconfdir}/heat/heat-api-cloudwatch.conf
%config(noreplace) %attr(-,root,heat) %{_sysconfdir}/heat/heat-api-cloudwatch-paste.ini
%{_initrddir}/openstack-heat-api-cloudwatch
%{_mandir}/man1/heat-api-cloudwatch.1.gz

%post api-cloudwatch
/sbin/chkconfig --add openstack-heat-api-cloudwatch

%preun api-cloudwatch
if [ $1 -eq 0 ]; then
    /sbin/service openstack-heat-api-cloudwatch stop >/dev/null 2>&1
    /sbin/chkconfig --del openstack-heat-api-cloudwatch
fi

%postun api-cloudwatch
if [ $1 -ge 1 ]; then
    /sbin/service openstack-heat-api-cloudwatch condrestart >/dev/null 2>&1 || :
fi


%package cli
Summary: Heat cli
Group: System Environment/Base

Requires: %{name}-common = %{version}-%{release}

%description cli
Heat client tools accessible from the CLI

%files cli
%doc README.rst LICENSE doc/build/html/man/heat-cfn.html
%{_bindir}/heat-boto
%{_bindir}/heat-cfn
%{_bindir}/heat-watch
%config(noreplace) %{_sysconfdir}/bash_completion.d/heat-cfn
%config(noreplace) %attr(-,root,heat) %{_sysconfdir}/heat/boto.cfg
%{_mandir}/man1/heat-cfn.1.gz
%{_mandir}/man1/heat-boto.1.gz
%{_mandir}/man1/heat-watch.1.gz

%changelog
* Wed Mar 27 2013 Jeff Peeler <jpeeler@redhat.com> 2013.1-0.8.rc1
- converted systemd scripts to sysvinit
- changed buildrequires from python-sphinx to python-sphinx10

* Thu Mar 21 2013 Steven Dake <sdake@redhat.com> 2013.1-0.7.rc1
- Add all dependencies required
- Remove buildrequires of python-glanceclient

* Wed Mar 20 2013 Jeff Peeler <jpeeler@redhat.com> 2013.1-0.6.rc1
- Updated URL
- Added version for Obsoletes
- Removed dev suffix in builddir
- Added missing man pages

* Mon Mar 11 2013 Steven Dake <sdake@redhat.com> 2013.1-0.5.g3
- Assign heat user with 167:167
- Rename packages from *-api to api-*
- Rename clients to cli
- change user/gid to heat from openstack-heat
- use shared state dir macro for shared state
- Add /etc/heat dir to owned directory list
- set proper uid/gid for files
- set proper read/write/execute bits

* Thu Dec 20 2012 Jeff Peeler <jpeeler@redhat.com> 2013.1-2
- split into subpackages

* Fri Dec 14 2012 Steve Baker <sbaker@redhat.com> 2013.1-1
- rebase to 2013.1
- expunge heat-metadata
- generate man pages and html developer docs with sphinx

* Tue Oct 23 2012 Zane Bitter <zbitter@redhat.com> 7-1
- rebase to v7
- add heat-api daemon (OpenStack-native API)

* Fri Sep 21 2012 Jeff Peeler <jpeeler@redhat.com> 6-5
- update m2crypto patch (Fedora)
- fix user/group install permissions

* Tue Sep 18 2012 Steven Dake <sdake@redhat.com> 6-4
- update to new v6 binary names in heat

* Tue Aug 21 2012 Jeff Peeler <jpeeler@redhat.com> 6-3
- updated systemd scriptlets

* Tue Aug  7 2012 Jeff Peeler <jpeeler@redhat.com> 6-2
- change user/group ids to openstack-heat

* Wed Aug 1 2012 Jeff Peeler <jpeeler@redhat.com> 6-1
- create heat user and change file permissions
- set systemd scripts to run as heat user

* Fri Jul 27 2012 Ian Main <imain@redhat.com> - 5-1
- added m2crypto patch.
- bumped version for new release.
- added boto.cfg to sysconfigdir

* Tue Jul 24 2012 Jeff Peeler <jpeeler@redhat.com> - 4-5
- added LICENSE to docs
- added dist tag
- added heat directory to files section
- removed unnecessary defattr 

* Tue Jul 24 2012 Jeff Peeler <jpeeler@redhat.com> - 4-4
- remove pycrypto requires

* Fri Jul 20 2012 Jeff Peeler <jpeeler@redhat.com> - 4-3
- change python-devel to python2-devel

* Wed Jul 11 2012 Jeff Peeler <jpeeler@redhat.com> - 4-2
- add necessary requires
- removed shebang line for scripts not requiring executable permissions
- add logrotate, removes all rpmlint warnings except for python-httplib2
- remove buildroot tag since everything since F10 has a default buildroot
- remove clean section as it is not required as of F13
- add systemd unit files
- change source URL to download location which doesn't require a SHA

* Fri Jun 8 2012 Steven Dake <sdake@redhat.com> - 4-1
- removed jeos from packaging since that comes from another repository
- compressed all separate packages into one package
- removed setup options which were producing incorrect results
- replaced python with {__python}
- added a br on python-devel
- added a --skip-build to the install step
- added percent-dir for directories
- fixed most rpmlint warnings/errors

* Mon Apr 16 2012 Chris Alfonso <calfonso@redhat.com> - 3-1
- initial openstack package log
