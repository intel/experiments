.PHONY: all deps lint test docker e2e-env test-e2e debug push-to-gcr

VERSION := $(shell git describe --tags --always --dirty)
GCR_PROJECT := $(shell gcloud config get-value project 2> /dev/null)
IMG := "gcr.io/$(GCR_PROJECT)/experiments:$(VERSION)"

all: test

deps:
	pip3 install -r requirements.txt -r requirements_tests.txt

lint:
	flake8 . --exclude ./venv

test:
	mkdir -p test-reports
	nosetests -v --debug=test --with-xunit --xunit-file=test-reports/nosetests.xml

docker:
	docker build -t experiments:latest -t experiments:$(VERSION) .

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
