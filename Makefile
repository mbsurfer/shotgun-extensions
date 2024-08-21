# Ensure the build target is always executed
.PHONY: build

# Build the Python package
build:
	rm -rf build/ dist/ *.egg-info
	python setup.py sdist bdist_wheel
	pip install .
