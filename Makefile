# This is a template `Makefile` file for snaps
# This file is managed by bootstack-charms-spec and should not be modified
# within individual snap repos. https://launchpad.net/bootstack-charms-spec

PYTHON := /usr/bin/python3

PROJECTPATH=$(dir $(realpath ${MAKEFILE_LIST}))
SNAP_NAME=$(shell cat ${PROJECTPATH}/snap/snapcraft.yaml | grep -E '^name:' | awk '{print $$2}')
SNAP_FILE=${PROJECTPATH}/${SNAP_NAME}.snap

help:
	@echo "This project supports the following targets"
	@echo ""
	@echo " make help - show this text"
	@echo " make clean - remove unneeded files"
	@echo " make dev-environment - setup the development environment"
	@echo " make build - build the snap"
	@echo " make lint - run lint checkers"
	@echo " make reformat - run lint tools to auto format code"
	@echo " make unittests - run the tests defined in the unittest subdirectory"
	@echo " make functional - run the tests defined in the functional subdirectory"
	@echo " make test - run lint, proof, unittests and functional targets"
	@echo " make pre-commit - run pre-commit checks on all the files"
	@echo ""

lint:
	@echo "Running lint checks"
	@tox -e lint

unittests:
	@echo "Running unit tests"
	@tox -e unit -- ${UNIT_ARGS}

test: lint unittests functional
	@echo "Tests completed for the snap."

reformat:
	@echo "Reformat files with black and isort"
	@tox -e reformat

build:
	@echo "Building the snap"
	@snapcraft --use-lxd
	@bash -c ./rename.sh

clean:
	@echo "Cleaning snap"
	@snapcraft clean --use-lxd
	@echo "Cleaning existing snap builds"
	@rm -rf ${SNAP_FILE}

dev-environment:
	@echo "Creating virtualenv and installing pre-commit"
	@tox -r -e dev-environment

functional: build
	@echo "Executing functional tests using built snap"
	@TEST_SNAP=${SNAP_FILE} tox -e func -- ${FUNC_ARGS}

pre-commit:
	@tox -e pre-commit

# The targets below don't depend on a file
.PHONY: help clean dev-environment build lint reformat unittests functional test pre-commit
