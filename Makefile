.PHONY: deps

all: test

deps:
	pip install -r requirements.txt -r requirements_tests.txt

lint:
	flake8 ./libexp ./tests

test: lint
	nosetests -v --debug=test
