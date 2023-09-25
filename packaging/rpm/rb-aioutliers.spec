Name: rb-aioutliers
Version: %{__version}
Release: %{__release}%{?dist}
BuildArch: noarch
Summary: RedBorder Python AI Outliers Detection Service

License: AGPL-3.0
URL: https://github.com/redBorder/rb-aioutliers
Source0: %{name}-%{version}.tar.gz

Requires: rh-python38

%description
This package provides the RedBorder Python AI Outliers Detection Service.

%exclude /opt/rb-aioutliers/.git

%prep
%setup -qn %{name}-%{version}

%build
cd %{_builddir}/%{name}-%{version}

%define __python %{_python_override}/python
%define _unpackaged_files_terminate_build 0

%install
# Create the destination directory for the installation
install -d -m 0755 %{buildroot}/opt/rb-aioutliers

# Enable the shell option to include hidden files
shopt -s dotglob

# Install all files (including hidden ones) to the destination directory
cp -r * %{buildroot}/opt/rb-aioutliers

# Create the systemd service directory and install the service file
install -d -m 0755 %{buildroot}/usr/lib/systemd/system/
install -m 0644 resources/systemd/rb-aioutliers.service %{buildroot}/usr/lib/systemd/system/

%files
%defattr(-,root,root,-)
/opt/rb-aioutliers/*
/usr/lib/systemd/system/rb-aioutliers.service

%post
# Activate the Python virtual environment
source /opt/rh/rh-python38/enable

# Install Python dependencies
pip install -r /opt/rb-aioutliers/resources/src/requirements.txt

%changelog
* Thu Sep 21 2023 Miguel Negrón <manegron@redborder.com> - 0.0.1-1
- First spec version
* Mon Sep 25 2023 Miguel Álvarez <malvarez@redborder.com> - 0.0.2-1
- Update AI model, create query builder and clean code

