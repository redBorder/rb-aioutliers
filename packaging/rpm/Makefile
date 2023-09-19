# Define variables
SERVICE_NAME = rb-aioutliers
VERSION = 1.0
RELEASE = 1
SPEC_FILE = $(SERVICE_NAME).spec
RPM_BUILD_DIR = ~/rpmbuild
RPM_OUTPUT_DIR = $(RPM_BUILD_DIR)/RPMS/noarch

# Build RPM package
rpm: $(SPEC_FILE)
	rpmbuild -ba --define "version $(VERSION)" --define "release $(RELEASE)" $(SPEC_FILE)

.PHONY: clean
clean:
	rm -rf $(SERVICE_NAME)-$(VERSION)
	rm -rf $(RPM_BUILD_DIR)

.PHONY: install
install:
	mkdir -p $(RPM_OUTPUT_DIR)
	cp $(RPM_OUTPUT_DIR)/$(SERVICE_NAME)-$(VERSION)-$(RELEASE).el7.noarch.rpm .
	sudo yum install $(SERVICE_NAME)-$(VERSION)-$(RELEASE).el7.noarch.rpm

.PHONY: all
all: rpm install