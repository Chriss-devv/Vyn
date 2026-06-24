.PHONY: install dev lint test compile run

install:
	pip install -r requirements.txt

dev:
	pip install -r requirements.txt -r requirements-dev.txt

lint:
	ruff check .

test:
	pytest -q

compile:
	python -m compileall core modules ui *.py

run:
	python vyn.py
