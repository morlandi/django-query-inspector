======================
django-query-inspector
======================

**PRELIMINARY: NOTHING REALLY USEFUL HERE, YET. STAY TUNED**


A collection of tools to inspect the SQL activity happening under the hood of a Django project

Quick start
-----------

1. Installation::

    pip install django-query-inspector

2. Add "quary_inspector" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'quary_inspector',
    ]


Does it work?
-------------

Running the unit tests from your project::

    python manage.py test -v 2 query_inspector --settings=query_inspector.tests.test_settings

Running the unit tests from your local fork::

    cd django-query-inspector
    ./runtests.py

or::

    coverage run --source='.' runtests.py
    coverage report
