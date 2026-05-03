publish:
	rm -rf build/ dist/ *.egg-info
	pip install build twine
	python -m build
#	twine upload dist/* --verbose
