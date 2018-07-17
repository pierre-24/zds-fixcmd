all: help

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  install-dependencies        to install python dependencies through pip"
	@echo "  install-dependencies-dev    to install python dependencies (dev) through pip"
	@echo "  lint                        to lint backend code (flake8)"

install-dependencies:
	pip3 install --upgrade -r requirements.txt

install-dependencies-dev: install-dependencies
	pip3 install --upgrade -r requirements-dev.txt

lint:
	flake8 fix_cmd tests --max-line-length=120 --ignore=N802

