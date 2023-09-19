Name: rb-aioutliers
Version: 1.0
Release: 1%{?dist}
Summary: RedBorder Python AI Outliers Detection Service
License: AGPL-3.0
Source0: %{name}-%{version}.tar.gz

Requires: rh-python38

%description
This package provides the RedBorder Python AI Outliers Detection Service.

%exclude /opt/rb-aioutliers/.git

%prep
%setup -q -n %{name}

%build
cd %{_builddir}/%{name}

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
# Change log entries (optional)
