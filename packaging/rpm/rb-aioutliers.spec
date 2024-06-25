Name: rb-aioutliers
Version: %{__version}
Release: %{__release}%{?dist}
BuildArch: noarch
Summary: RedBorder Python AI Outliers Detection Service

License: AGPL 3.0
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

#Create outliers log file
install -d -m 0755 %{buildroot}/var/log/rb-aioutliers

# Install all files (including hidden ones) to the destination directory
cp -r * %{buildroot}/opt/rb-aioutliers
touch %{buildroot}/var/log/rb-aioutliers/outliers.log

# Create the systemd service directory and install the service file
install -d -m 0755 %{buildroot}/usr/lib/systemd/system/
install -m 0644 resources/systemd/rb-aioutliers.service %{buildroot}/usr/lib/systemd/system/
install -m 0644 resources/systemd/rb-aioutliers-train.service %{buildroot}/usr/lib/systemd/system/

%files
%defattr(-,root,root,-)
/usr/lib/systemd/system/rb-aioutliers.service
/usr/lib/systemd/system/rb-aioutliers-train.service
%defattr(-,rb-aioutliers,rb-aioutliers,-)
/opt/rb-aioutliers/*
/var/log/rb-aioutliers/*

%post
# Install Python dependencies
pip3 install virtualenv

# Create and activate the virtual environment
python3 -m venv /opt/rb-aioutliers/aioutliers
source /opt/rb-aioutliers/aioutliers/bin/activate

# Install project dependencies
pip3 install -r /opt/rb-aioutliers/resources/src/requirements.txt

# Add NVIDIA libraries to LD_LIBRARY_PATH (Necessary for using TensorFlow with GPU)
cp /opt/rb-aioutliers/resources/src/setup_tensorflow_and_cuda.sh /opt/rb-aioutliers/aioutliers/bin/setup_tensorflow_and_cuda.sh

# Append the sourcing of setup script to activate script
echo "source /opt/rb-aioutliers/aioutliers/bin/setup_tensorflow_and_cuda.sh" | tee -a /opt/rb-aioutliers/aioutliers/bin/activate

# Deactivate and reactivate to apply changes
deactivate
source /opt/rb-aioutliers/aioutliers/bin/activate

%changelog
* Tue Jan 30 2024 Miguel Álvarez <malvarez@redborder.com> - 0.0.3-1
- Adapt for rhel9 build and user/group creation
* Mon Sep 25 2023 Miguel Álvarez <malvarez@redborder.com> - 0.0.2-1
- Update AI model, create query builder and clean code
* Thu Sep 21 2023 Miguel Negrón <manegron@redborder.com> - 0.0.1-1
- First spec version
