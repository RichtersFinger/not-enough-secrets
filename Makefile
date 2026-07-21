UID ?= $(shell id -u)
GID ?= $(shell id -g)

DEB_PACKAGE    := not-enough-secrets
DEB_VERSION    := 0.1.0
DEB_ARCH       := all
DEB_STAGE_ROOT := $(CURDIR)
DEB_STAGE      := $(DEB_STAGE_ROOT)/build/$(DEB_PACKAGE)
DEB_PKGDIR     := $(DEB_STAGE)/usr/lib/python3/dist-packages/not_enough_secrets
DEB_DOCDIR     := $(DEB_STAGE)/usr/share/doc/$(DEB_PACKAGE)
DEB_COMPDIR    := $(DEB_STAGE)/usr/share/bash-completion/completions
DEB_BINDIR     := $(DEB_STAGE)/usr/bin
DEB_OUT        := $(CURDIR)/dist/$(DEB_PACKAGE)_$(DEB_VERSION)_$(DEB_ARCH).deb

build-deb-docker:
	docker build \
		-t not-enough-secrets-deb:builder \
		-f Dockerfile.deb-build .
	docker run \
		--rm \
		-v "$(CURDIR):/app" \
		--user $(UID):$(GID) \
		not-enough-secrets-deb:builder \
		make build-deb DEB_STAGE_ROOT=/tmp

build-deb:
	mkdir -p "$(CURDIR)/dist"
	install -d "$(DEB_STAGE)/DEBIAN"
	install -m 0644 "$(CURDIR)/debian/control" "$(DEB_STAGE)/DEBIAN/control"
	install -d "$(DEB_PKGDIR)"
	cp -r "$(CURDIR)/src/not_enough_secrets/." "$(DEB_PKGDIR)/"
	chmod -R 644 "$(DEB_PKGDIR)"
	find "$(DEB_PKGDIR)" -type d -name __pycache__ -prune -exec rm -r {} +
	find "$(DEB_PKGDIR)" -type d -exec chmod 755 {} +
	install -d $(DEB_DOCDIR)
	install -m 0644 "$(CURDIR)/README.md" "$(DEB_DOCDIR)/readme"
	install -m 0644 "$(CURDIR)/LICENSE" "$(DEB_DOCDIR)/copyright"
	install -d "$(DEB_COMPDIR)"
	install -m 0644 "$(CURDIR)/completion.bash" "$(DEB_COMPDIR)/not-enough-secrets"
	install -d "$(DEB_BINDIR)"
	install -m 0755 "$(CURDIR)/not-enough-secrets.sh" "$(DEB_BINDIR)/not-enough-secrets"
	dpkg-deb --build --root-owner-group "$(DEB_STAGE)" "$(DEB_OUT)"

clean:
	@echo "The following files/directories will be permanently removed:"
	@git clean -dfXn
	@echo "--------------------------------------------------"
	@read -p "Are you sure you want to proceed? [y/N]: " ans; \
	if [ "$$ans" = "y" ] || [ "$$ans" = "Y" ]; then \
		git clean -dfX; \
		echo "Cleanup complete."; \
	else \
		echo "Cleanup aborted."; \
		exit 1; \
	fi
