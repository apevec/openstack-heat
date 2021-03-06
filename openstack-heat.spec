%global release_name havana
%global project heat
Source0:        http://tarballs.openstack.org/%{project}/%{project}-stable-%{release_name}.tar.gz
%global devtag %(tar ztf %{SOURCE0} 2>/dev/null | head -1 | rev | cut -d. -f2 | rev)
%global devrel %(tar ztf %{SOURCE0} 2>/dev/null | head -1 | rev | cut -d. -f3-5 | cut -d- -f1 | rev)

%global with_doc %{!?_without_doc:1}%{?_without_doc:0}

Name:		openstack-heat
Summary:	OpenStack Orchestration (heat)
Version:	%{devrel}
Release:	0.1.%{devtag}%{?dist}
License:	ASL 2.0
Group:		System Environment/Base
URL:		http://www.openstack.org
Obsoletes:	heat < 7-9
Provides:	heat

Source1:	heat.logrotate
Source2:	openstack-heat-api.init
Source3:	openstack-heat-api-cfn.init
Source4:	openstack-heat-engine.init
Source5:	openstack-heat-api-cloudwatch.init
Source20:   heat-dist.conf

#
# patches_base=gerrit/stable/havana
#
Patch0001: 0001-Switch-to-using-M2Crypto.patch
Patch0002: 0002-remove-pbr-runtime-dependency.patch
Patch0003: 0003-Adjust-to-handle-parallel-installed-packages.patch

BuildArch: noarch
BuildRequires: git
BuildRequires: python2-devel
BuildRequires: python-setuptools
BuildRequires: python-oslo-sphinx
BuildRequires: python-argparse
BuildRequires: python-eventlet
BuildRequires: python-greenlet
BuildRequires: python-httplib2
BuildRequires: python-iso8601
BuildRequires: python-kombu
BuildRequires: python-lxml
BuildRequires: python-netaddr
BuildRequires: python-memcached
BuildRequires: python-migrate
BuildRequires: python-qpid
BuildRequires: python-six
BuildRequires: PyYAML
BuildRequires: m2crypto
BuildRequires: python-paramiko
BuildRequires: python-sphinx10
# These are required to build due to the requirements check added
BuildRequires: python-paste-deploy1.5
BuildRequires: python-routes1.12
BuildRequires: python-sqlalchemy0.7
BuildRequires: python-webob1.2

BuildRequires: python-pbr
BuildRequires: python-d2to1
%if 0%{?with_doc}
BuildRequires: python-oslo-config
BuildRequires: python-cinderclient
BuildRequires: python-keystoneclient
BuildRequires: python-novaclient
BuildRequires: python-neutronclient
BuildRequires: python-swiftclient
%endif

Requires: %{name}-common = %{version}-%{release}
Requires: %{name}-engine = %{version}-%{release}
Requires: %{name}-api = %{version}-%{release}
Requires: %{name}-api-cfn = %{version}-%{release}
Requires: %{name}-api-cloudwatch = %{version}-%{release}

%prep
%setup -q -c -T
tar --strip-components=1 -zxf %{SOURCE0}
%patch0001 -p1
%patch0002 -p1
%patch0003 -p1
sed -i s/REDHATHEATVERSION/%{version}/ heat/version.py
sed -i s/REDHATHEATRELEASE/%{release}/ heat/version.py
sed -i 's/^Version: .*/Version: %{version}/' PKG-INFO

# Remove the requirements file so that pbr hooks don't add it
# to distutils requires_dist config
rm -rf {test-,}requirements.txt tools/{pip,test}-requires

echo '
#
# Options to be passed to keystoneclient.auth_token middleware
# NOTE: These options are not defined in heat but in keystoneclient
#
[keystone_authtoken]

# the name of the admin tenant (string value)
#admin_tenant_name=

# the keystone admin username (string value)
#admin_user=

# the keystone admin password (string value)
#admin_password=

# the keystone host (string value)
#auth_host=

# the keystone port (integer value)
#auth_port=

# protocol to be used for auth requests http/https (string value)
#auth_protocol=

#auth_uri=

# signing_dir is configurable, but the default behavior of the authtoken
# middleware should be sufficient.  It will create a temporary directory
# in the home directory for the user the heat process is running as.
#signing_dir=/var/lib/heat/keystone-signing
' >> etc/heat/heat.conf.sample

# Programmatically update defaults in sample config
# which is installed at /etc/heat/heat.conf
# TODO: Make this more robust
# Note it only edits the first occurance, so assumes a section ordering in sample
# and also doesn't support multi-valued variables.
while read name eq value; do
  test "$name" && test "$value" || continue
  sed -i "0,/^# *$name=/{s!^# *$name=.*!#$name=$value!}" etc/heat/heat.conf.sample
done < %{SOURCE20}

%build
%{__python} setup.py build

%install
%{__python} setup.py install -O1 --skip-build --root=%{buildroot}
sed -i -e '/^#!/,1 d' %{buildroot}/%{python_sitelib}/heat/db/sqlalchemy/manage.py
sed -i -e '/^#!/,1 d' %{buildroot}/%{python_sitelib}/heat/db/sqlalchemy/migrate_repo/manage.py
mkdir -p %{buildroot}/var/log/heat/
mkdir -p %{buildroot}/var/run/heat/
install -p -D -m 644 %{SOURCE1} %{buildroot}%{_sysconfdir}/logrotate.d/openstack-heat

# install init scripts
install -p -D -m 755 %{SOURCE2} %{buildroot}%{_initrddir}/openstack-heat-api
install -p -D -m 755 %{SOURCE3} %{buildroot}%{_initrddir}/openstack-heat-api-cfn
install -p -D -m 755 %{SOURCE4} %{buildroot}%{_initrddir}/openstack-heat-engine
install -p -D -m 755 %{SOURCE5} %{buildroot}%{_initrddir}/openstack-heat-api-cloudwatch

mkdir -p %{buildroot}/var/lib/heat/
mkdir -p %{buildroot}/etc/heat/

%if 0%{?with_doc}
export PYTHONPATH="$( pwd ):$PYTHONPATH"
pushd doc
sphinx-1.0-build -b html -d build/doctrees source build/html
sphinx-1.0-build -b man -d build/doctrees source build/man

mkdir -p %{buildroot}%{_mandir}/man1
install -p -D -m 644 build/man/*.1 %{buildroot}%{_mandir}/man1/
popd
%endif

rm -rf %{buildroot}/var/lib/heat/.dummy
rm -f %{buildroot}/usr/bin/cinder-keystone-setup
rm -rf %{buildroot}/%{python_sitelib}/heat/tests

install -p -D -m 640 etc/heat/heat.conf.sample %{buildroot}/%{_sysconfdir}/heat/heat.conf
install -p -D -m 640 %{SOURCE20} %{buildroot}%{_datadir}/heat/heat-dist.conf
install -p -D -m 640 etc/heat/api-paste.ini %{buildroot}/%{_datadir}/heat/api-paste-dist.ini
install -p -D -m 640 etc/heat/policy.json %{buildroot}/%{_sysconfdir}/heat

# TODO: move this to setup.cfg
cp -vr etc/heat/templates %{buildroot}/%{_sysconfdir}/heat
cp -vr etc/heat/environment.d %{buildroot}/%{_sysconfdir}/heat

%description
Heat provides AWS CloudFormation and CloudWatch functionality for OpenStack.


%package common
Summary: Heat common
Group: System Environment/Base

Requires: python-argparse
Requires: python-eventlet
Requires: python-greenlet
Requires: python-httplib2
Requires: python-iso8601
Requires: python-kombu
Requires: python-lxml
Requires: python-netaddr
Requires: python-cinderclient
Requires: python-keystoneclient >= 0.3.1
Requires: python-memcached
Requires: python-novaclient
Requires: python-oslo-config >= 1:1.2.0
Requires: python-neutronclient
Requires: python-swiftclient
Requires: python-migrate
Requires: python-qpid
Requires: python-six
Requires: PyYAML
Requires: m2crypto
Requires: python-anyjson
Requires: python-paramiko
Requires: python-heatclient
Requires: python-babel

Requires: python-paste-deploy1.5
Requires: python-routes1.12
Requires: python-sqlalchemy0.7
Requires: python-webob1.2

Requires(pre): shadow-utils

%description common
Components common to all OpenStack Heat services

%files common
%doc LICENSE
%{_bindir}/heat-manage
%{_bindir}/heat-db-setup
%{_bindir}/heat-keystone-setup
%{python_sitelib}/heat*
%attr(-, root, heat) %{_datadir}/heat/heat-dist.conf
%attr(-, root, heat) %{_datadir}/heat/api-paste-dist.ini
%dir %attr(0755,heat,root) %{_localstatedir}/log/heat
%dir %attr(0755,heat,root) %{_localstatedir}/run/heat
%dir %attr(0755,heat,root) %{_sharedstatedir}/heat
%dir %attr(0755,heat,root) %{_sysconfdir}/heat
%config(noreplace) %{_sysconfdir}/logrotate.d/openstack-heat
%config(noreplace) %attr(-, root, heat) %{_sysconfdir}/heat/heat.conf
%config(noreplace) %attr(-, root, heat) %{_sysconfdir}/heat/policy.json
%config(noreplace) %attr(-,root,heat) %{_sysconfdir}/heat/environment.d/*
%config(noreplace) %attr(-,root,heat) %{_sysconfdir}/heat/templates/*
%if 0%{?with_doc}
%{_mandir}/man1/heat-db-setup.1.gz
%{_mandir}/man1/heat-keystone-setup.1.gz
%endif

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
%doc README.rst LICENSE
%if 0%{?with_doc}
%doc doc/build/html/man/heat-engine.html
%endif
%{_bindir}/heat-engine
%{_initrddir}/openstack-heat-engine
%if 0%{?with_doc}
%{_mandir}/man1/heat-engine.1.gz
%endif

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
%doc README.rst LICENSE
%if 0%{?with_doc}
%doc doc/build/html/man/heat-api.html
%endif
%{_bindir}/heat-api
%{_initrddir}/openstack-heat-api
%if 0%{?with_doc}
%{_mandir}/man1/heat-api.1.gz
%endif

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
%doc README.rst LICENSE
%if 0%{?with_doc}
%doc doc/build/html/man/heat-api-cfn.html
%endif
%{_bindir}/heat-api-cfn
%{_initrddir}/openstack-heat-api-cfn
%if 0%{?with_doc}
%{_mandir}/man1/heat-api-cfn.1.gz
%endif

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
%doc README.rst LICENSE
%if 0%{?with_doc}
%doc doc/build/html/man/heat-api-cloudwatch.html
%endif
%{_bindir}/heat-api-cloudwatch
%{_initrddir}/openstack-heat-api-cloudwatch
%if 0%{?with_doc}
%{_mandir}/man1/heat-api-cloudwatch.1.gz
%endif

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


%changelog
* Wed Feb 19 2014 Jeff Peeler <jpeeler@redhat.com> 2013.2.2-1
- update to 2013.2.2

* Fri Jan 03 2014 Pádraig Brady <pbrady@redhat.com> 2013.2.1-2
- Fix heat-manage to work with parallel installed packages

* Mon Dec 16 2013 Jeff Peeler <jpeeler@redhat.com> 2013.2.1-1
- update to 2013.2.1

* Thu Oct 17 2013 Jeff Peeler <jpeeler@redhat.com> 2013.2-1
- update to havana final

* Mon Oct 14 2013 Jeff Peeler <jpeeler@redhat.com> 2013.2-0.9.rc2
- rebase to havana-rc2

* Thu Oct 3 2013 Jeff Peeler <jpeeler@redhat.com> 2013.2-0.9.rc1
- update to rc1
- exclude doc builds if with_doc 0

* Mon Sep 23 2013 Jeff Peeler <jpeeler@redhat.com> 2013.2-0.9.b3
- changed webob requires to 1.0 -> 1.2

* Thu Sep 19 2013 Jeff Peeler <jpeeler@redhat.com> 2013.2-0.8.b3
- fix the python-oslo-config dependency to cater for epoch
- add api-paste-dist.ini to /usr/share/heat

*  Tue Sep 17 2013 Jeff Peeler <jpeeler@redhat.com> 2013.2-0.7.b3
- Depend on python-oslo-config >= 1.2 so it upgraded automatically
- Distribute dist defaults in heat-dist.conf separate to user heat.conf (rhbz 1008560)

* Wed Sep 11 2013 Jeff Peeler <jpeeler@redhat.com> 2013.2-0.6.b3
- fix init scripts (rhbz 1006868)
- added python-babel
- remove runtime pbr dependency (rhbz 1006911)

* Mon Sep 9 2013 Jeff Peeler <jpeeler@redhat.com> 2013.2-0.5.b3
- rebase to havana-3
- remove tests from common
- remove cli package and move heat-manage into common
- added requires for python-heatclient
- remove python-boto as boto has been moved to another repo
- remove heat-cfn bash completion
- add /var/run/heat directory

* Tue Jul 30 2013 Pádraig Brady <pbrady@redhat.com> 2013.2-0.4.b2
- avoid python runtime dependency management

* Mon Jul 22 2013 Jeff Peeler <jpeeler@redhat.com> 2013.2-0.3.b2
- rebase to havana-2

* Mon Jun 10 2013 Jeff Peeler <jpeeler@redhat.com> 2013.2-0.2.b1
- fix m2crypto patch

* Tue Jun  4 2013 Jeff Peeler <jpeeler@redhat.com> 2013.2-0.1.b1
- rebase to havana-1
- consolidate api-paste files into one file in common
- removed runner.py as it is no longer present
- added heat-manage
- added new buildrequires pbr and d2to1

* Tue May 28 2013 Jeff Peeler <jpeeler@redhat.com> 2013.1-1.3
- bumped obsoletes for f18 rebuilds of the old heat package
- added missing policy.json file (rhbz#965549)

* Wed May  8 2013 Jeff Peeler <jpeeler@redhat.com> 2013.1-1.2
- removed python-crypto require

* Wed May  8 2013 Jeff Peeler <jpeeler@redhat.com> 2013.1-1.1
- re-added m2crypto patch (rhbz960165)

* Mon Apr  8 2013 Jeff Peeler <jpeeler@redhat.com> 2013.1-1.0
- update to grizzly final

* Tue Apr  2 2013 Jeff Peeler <jpeeler@redhat.com> 2013.1-1.0.rc2
- added epel patch for dependencies
- added new buildrequires due to above patch
- changed requires to more recent versions

* Mon Apr  1 2013 Jeff Peeler <jpeeler@redhat.com> 2013.1-0.9.rc2
- add /var/run/heat so PID directory has correct permissions

* Thu Mar 28 2013 Jeff Peeler <jpeeler@redhat.com> 2013.1-0.8.rc2
- bump to rc2

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
