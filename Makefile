.PHONY: docs

env:
	pip install virtualenv && \
	virtualenv venv && \
	. venv/bin/activate && \
	make deps

deps:
	pip install -r requirements/dev.txt

clean:
	find . -name '*.pyc' -exec rm -f {} \;
	find . -name '*.pyo' -exec rm -f {} \;
	find . -name '*~' -exec rm -f {} \;

test: test-py

test-py:
	DJANGO_SETTINGS_MODULE=settings.test python manage.py test

test-py-debug:
	DJANGO_SETTINGS_MODULE=settings.test python manage.py test -s

test-acceptance:
	node_modules/protractor/bin/protractor protractor.conf.js

release:
	pandoc --from=markdown --to=rst README.md -o README.rst
	python setup.py bdist_egg upload
	python setup.py sdist upload
	rm README.rst
