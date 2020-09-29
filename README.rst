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

3. Add "QueryCountMiddleware" to your MIDDLEWARE setting like this::

    MIDDLEWARE = [
        ...
        'query_inspector.middleware.QueryCountMiddleware',
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

Query counting
--------------

A middleware that prints DB query counts in Django's runserver console output.

Adapted from: `Django Querycount <https://github.com/bradmontgomery/django-querycount>`_

by Brad Montgomery

=========================== =============================================================================================
Setting                     Meaning
--------------------------- ---------------------------------------------------------------------------------------------
IGNORE_ALL_REQUESTS         Disables query count
IGNORE_REQUEST_PATTERNS     A list of regexp patterns to bypass matching requests
IGNORE_SQL_PATTERNS         A list of regexp patterns to bypass matching queries
THRESHOLDS                  How many queries are interpreted as high or medium (and the color-coded output)
DISPLAY_ALL                 Trace all queries (even when not duplicated)
DISPLAY_PRETTIFIED          Use pygments and sqlparse for queries tracing
COLOR_FORMATTER_STYLE       Color formatter style for Pygments
RESPONSE_HEADER             Custom response header that contains the total number of queries executed (None = disabled)
DISPLAY_DUPLICATES          Controls how the most common duplicate queries are displayed (None = displayed)
=========================== =============================================================================================

Default settings (to be overridden in projects' settings)::

    QUERYCOUNT = {
        'IGNORE_ALL_REQUESTS': True,
        'IGNORE_REQUEST_PATTERNS': [],
        'IGNORE_SQL_PATTERNS': [],
        'THRESHOLDS': {
            'MEDIUM': 50,
            'HIGH': 200,
            'MIN_TIME_TO_LOG': 0,
            'MIN_QUERY_COUNT_TO_LOG': 0
        },
        'DISPLAY_ALL': True,
        'DISPLAY_PRETTIFIED': True,
        'COLOR_FORMATTER_STYLE': 'monokai',
        'RESPONSE_HEADER': 'X-DjangoQueryCount-Count',
        'DISPLAY_DUPLICATES': 0,
    }


@query_debugger
---------------

Decorator to check how many queries are executed when rendering a specific view.

Adapted from:

`Django select_related and prefetch_related: Checking how many queries reduce using these methods with an example <https://medium.com/better-programming/django-select-related-and-prefetch-related-f23043fd635d>`_

by Goutom Roy

Examples::

    from query_inspector import query_debugger

    @query_debugger
    def tracks_list_view(request):
        ...

    class TrackAjaxDatatableView(AjaxDatatableView):

        ...

        @query_debugger
        def dispatch(self, request, *args, **kwargs):
            ...
