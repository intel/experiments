.PHONY: all deps lint test docker pydist e2e-env test-e2e debug push-to-gcr \
	verify-gcr-image push-to-pypi verify-pypi-wheels valid-release release \
	valid-circlci-config

VERSION := $(shell git describe --tags --always --dirty)
GCR_PROJECT := $(shell gcloud config get-value project 2> /dev/null)
IMG := "gcr.io/$(GCR_PROJECT)/experiments:$(VERSION)"

all: test

deps:
	pip3 install -r requirements.txt -r requirements-dev.txt

lint:
	flake8 . --exclude ./venv

test:
	mkdir -p test-reports
	nosetests -v --debug=test --with-xunit --xunit-file=test-reports/nosetests.xml

docker:
	docker build -t experiments:latest -t experiments:$(VERSION) .

pydist: deps
	pip3 wheel --wheel-dir=wheels -r requirements.txt .

e2e-env:
	docker-compose build
	docker-compose up -d
	docker-compose ps

test-e2e: e2e-env
	docker-compose exec test /experiments/resources/wait-for-socket-address kubernetes 8080
	docker-compose exec test make
	docker cp $(shell docker-compose ps -q test):/experiments/test-reports .

debug: e2e-env
	docker-compose exec test /bin/bash

push-to-gcr: docker
	docker tag experiments:$(VERSION) $(IMG)
	gcloud docker -- push $(IMG)

verify-gcr-image:
	gcloud container images describe $(IMG) >/dev/null 2>&1

push-to-pypi: pydist
	if [ -r ~/.pypirc ]; then \
		echo "Uploading $(VERSION)" ; \
		twine upload wheels/experiments-$(VERSION)* ; \
	else \
		echo "~/.pypirc not found" ; \
	fi;

verify-pypi-wheels:
	curl -I https://pypi.org/pypi/experiments/$(VERSION)/json 2>/dev/null | head -1 | grep 200 >/dev/null

# note: can't do strict `setup.py check -s` (long_description_content_type not
# yet understood in distutils).  See:
# https://dustingram.com/articles/2018/03/16/markdown-descriptions-on-pypi
# https://packaging.python.org/specifications/core-metadata/#description-content-type
valid-release:
	@echo "Ensuring a tagged, clean checkout for release..."
	[[ "$(VERSION)" == $(shell git describe --abbrev=0 --tags) ]]
	@echo "Ensuring valid setup.py format..."
	python setup.py check

release: valid-release push-to-gcr push-to-pypi

# requires circleci CLI: https://circleci.com/docs/2.0/local-cli/
valid-circleci-config:
	circleci config validate -c .circleci/config.yml
