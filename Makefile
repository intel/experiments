.PHONY: deps

VERSION := $(shell git describe --tags --always --dirty)

all: test

deps:
	pip3 install -r requirements.txt -r requirements_tests.txt

lint:
	flake8 ./libexp ./tests ./examples/

test: lint
	nosetests -v --debug=test

docker:
	docker build -t experiments:latest -t experiments:$(VERSION) .

e2e-env:
	docker-compose build
	docker-compose up -d
	docker-compose ps

test-e2e: e2e-env
	docker-compose exec test /experiments/resources/wait-for-socket-address kubernetes 8080
	docker-compose exec test make

debug: e2e-env
	docker-compose exec test /bin/bash
