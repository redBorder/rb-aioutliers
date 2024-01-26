Name: rb-aioutliers
Version: %{__version}
Release: %{__release}%{?dist}
BuildArch: noarch
Summary: RedBorder Python AI Outliers Detection Service

License: GPL-2.0
URL: https://github.com/redBorder/rb-aioutliers
Source0: %{name}-%{version}.tar.gz

Requires: python3.9-pip

%description
This package provides the RedBorder Python AI Outliers Detection Service.

%exclude /opt/rb-aioutliers/.git

%pre
getent group %{name} >/dev/null || groupadd -r %{name}
getent passwd %{name} >/dev/null || \
    useradd -r -g %{name} -d / -s /sbin/nologin \
    -c "User of %{name} service" %{name}
exit 0

%prep
%setup -qn %{name}-%{version}

%build
cd %{_builddir}/%{name}-%{version}

%define __python %{_python_override}/python
%define _unpackaged_files_terminate_build 0

%install
# Create the destination directory for the installation
install -d -m 0755 %{buildroot}/opt/rb-aioutliers

# Install all files (including hidden ones) to the destination directory
cp -r * %{buildroot}/opt/rb-aioutliers

# Create the systemd service directory and install the service file
install -d -m 0755 %{buildroot}/usr/lib/systemd/system/
install -m 0644 resources/systemd/rb-aioutliers.service %{buildroot}/usr/lib/systemd/system/
install -m 0644 resources/systemd/rb-aioutliers-train.service %{buildroot}/usr/lib/systemd/system/
install -m 0644 resources/systemd/rb-aioutliers-rq.service %{buildroot}/usr/lib/systemd/system/

%files
%defattr(-,root,root,-)
/usr/lib/systemd/system/rb-aioutliers.service
/usr/lib/systemd/system/rb-aioutliers-train.service
/usr/lib/systemd/system/rb-aioutliers-rq.service
%defattr(-,rb-aioutliers,rb-aioutliers,-)
/opt/rb-aioutliers/*
/var/log/rb-aioutliers/outliers.log

%post
# Install Python dependencies
pip3 install virtualenv

# Create and activate the virtual environment
python3 -m venv /opt/rb-aioutliers/aioutliers
source /opt/rb-aioutliers/aioutliers/bin/activate

# Install project dependencies
pip3 install -r /opt/rb-aioutliers/resources/src/requirements.txt

%changelog
* Mon Sep 25 2023 Miguel Álvarez <malvarez@redborder.com> - 0.0.2-1
- Update AI model, create query builder and clean code
* Thu Sep 21 2023 Miguel Negrón <manegron@redborder.com> - 0.0.1-1
- First spec version
