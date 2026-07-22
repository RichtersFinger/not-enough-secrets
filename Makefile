SHELL := /bin/bash
PWD := $(CURDIR)

-include .env
UID ?= $(shell id -u)
GID ?= $(shell id -g)

PYTHON_CONTAINER_NAME := not-enough-secrets-dev
PYTHON_CONTAINER_START := docker run --rm -t -d \
	-v "${PWD}:${PWD}" \
	-w "${PWD}" \
	-e PYTHONUSERBASE=/tmp/docker-python-base \
	-e PIP_NO_CACHE_DIR=true \
	--user $(UID):$(GID) \
	--name ${PYTHON_CONTAINER_NAME} \
	python:3.12.13-alpine@sha256:aa679aa4eed6eb56c1dc6ad3f1b98b7d2d788fd961596779d188fdedad97fb38 \
	sleep infinity
PYTHON_CONTAINER_RUNNING := docker ps -q -f name=$(PYTHON_CONTAINER_NAME)
PYTHON_SHELL := docker exec -it ${PYTHON_CONTAINER_NAME}

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

up:
	@if [ -z "$$(${PYTHON_CONTAINER_RUNNING})" ]; then \
		$(PYTHON_CONTAINER_START) > /dev/null; \
		until [ -n "$$($(PYTHON_CONTAINER_RUNNING))" ]; do printf "."; sleep 0.2; done; \
		echo " Ready."; \
	fi

down:
	@if [ -n "$$($(PYTHON_CONTAINER_RUNNING))" ]; then \
		docker kill $(PYTHON_CONTAINER_NAME); \
	fi

shell: up
	${PYTHON_SHELL} sh

install: up
	${PYTHON_SHELL} pip install ".[cryptography]"

test:
	${PYTHON_SHELL} python3 -m unittest discover tests/ ${ARGS}

build-wheel: up
	${PYTHON_SHELL} sh -c "pip install --upgrade build==1.5.0 && python -m build --wheel --sdist"

publish-pypi: up
	${PYTHON_SHELL} sh -c "pip install --upgrade twine==6.2.0 && python3 -m twine upload dist/*"

build-deb:
	docker build \
		-t not-enough-secrets-deb:builder \
		-f Dockerfile.deb-build .
	docker run \
		--rm \
		-v "$(CURDIR):/app" \
		--user $(UID):$(GID) \
		not-enough-secrets-deb:builder \
		make build-deb-native DEB_STAGE_ROOT=/tmp

build-deb-native:
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
	install -m 0644 "$(CURDIR)/completion.bash" "$(DEB_COMPDIR)/$(DEB_PACKAGE)"
	install -d "$(DEB_BINDIR)"
	install -m 0755 "$(CURDIR)/not-enough-secrets.sh" "$(DEB_BINDIR)/$(DEB_PACKAGE)"
	install -d "$(DEB_PKGDIR)-$(DEB_VERSION).dist-info"
	echo "Metadata-Version: 2.1" > "$(DEB_PKGDIR)-$(DEB_VERSION).dist-info/METADATA"
	echo "Name: $(DEB_PACKAGE)" >> "$(DEB_PKGDIR)-$(DEB_VERSION).dist-info/METADATA"
	echo "Version: $(DEB_VERSION)" >> "$(DEB_PKGDIR)-$(DEB_VERSION).dist-info/METADATA"
	dpkg-deb --build --root-owner-group "$(DEB_STAGE)" "$(DEB_OUT)"

clean:
	@echo "The following files/directories will be permanently removed:"
	@git clean -dfXn -e !.env
	@echo "--------------------------------------------------"
	@read -p "Are you sure you want to proceed? [y/N]: " ans; \
	if [ "$$ans" = "y" ] || [ "$$ans" = "Y" ]; then \
		git clean -dfX -e !.env; \
		echo "Cleanup complete."; \
	else \
		echo "Cleanup aborted."; \
		exit 1; \
	fi
