======================
django-query-inspector
======================

.. image:: https://badge.fury.io/py/django-query-inspector.svg
    :target: https://badge.fury.io/py/django-query-inspector

A collection of tools to:

    - render a Queryset (or a list of dictionaries) in various formats
    - export a Queryset to a spreadsheet
    - inspect the SQL activity happening under the hood of a Django project

.. contents::

.. sectnum::

Quick start
-----------

1. Installation::

    pip install django-query-inspector

2. Add "query_inspector" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'query_inspector',
    ]

3. Add "QueryCountMiddleware" to your MIDDLEWARE setting like this::

    MIDDLEWARE = [
        ...
        'query_inspector.middleware.QueryCountMiddleware',
    ]

4. Optional dependencies:

    - sqlparse
    - termcolor
    - pygments
    - xlsxwriter

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

A middleware that prints DB query counts in Django's runserver console output (only in DEBUG mode).

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

Result:

.. figure:: screenshots/query_debugger.png

    query_debugger

Tracing
-------

Some helper functions are available to print formatted and colored text in the console.

Optional requirements:

    - sqlparse
    - termcolor
    - pygments
    - tabulate

Functions:

def trace(message, color='yellow', on_color=None, attrs=None, prompt='', prettify=False)
    Display 'message', optionally preceed by 'prompt';
    If 'prettify' is True, format message with pprint

    Color support provided by: https://pypi.org/project/termcolor/

def prettyprint_query(query, colorize=True, prettify=True)
    Display the specified SQL statement

def prettyprint_queryset(qs, colorize=True, prettify=True)
    Display the SQL statement implied by the given queryset

def trace_func(fn):
    Decorator to detect: function call, input parameters and return value

def qsdump( * fields, queryset, max_rows=None)
    See below

Results:

.. figure:: screenshots/prettyprint_queryset.png

    prettyprint_queryset

.. figure:: screenshots/trace_func.png

    trace_func


Inspect a queryset with qsdump
------------------------------

With qsdump you can:

- display the formatted SQL statement
- display the content of the queryset

Parameters:

    fields:
        one or more field names; '*' means 'all'

    queryset:
        the queryset to be inspected

    max_rows:
        optionally limit the numer of rows

    render_with_tabulate=True
        use "tabulate" when available

    title=""
        optional title

Example::

    qsdump('*', queryset=tracks, max_rows=10)

|

.. figure:: screenshots/qsdump.png

    qsdump


Queryset rendering
------------------

A few templatetags are available to render either a queryset or a list of dictionaries::

    def render_queryset_as_table(* fields, queryset, options={})
    def render_queryset_as_csv(* fields, queryset, options={})
    def render_queryset_as_text(* fields, queryset, options={})


Sample usage::

    {% load static query_inspector_tags %}

    <link href="{% static 'query_inspector.css' %}" rel="stylesheet" />

    <table class="simpletable smarttable">
        {% render_queryset_as_table "id" "last_name|Cognome" "first_name|Nome" ... queryset=operatori %}
    </table>


Parameters:

queryset: a queryset of a list of dictionaries with data to rendered

options:
    - max_rows: max n. of rows to be rendered (None=all)
    - format_date:  date formatting string; see:
        + https://docs.djangoproject.com/en/dev/ref/settings/#date-format
        + https://docs.djangoproject.com/en/dev/ref/templates/builtins/#date
    - add_totals: computes column totals and append results as bottom row

fields: a list of field specifiers, espressed as:
    - "fieldname", or
    - "fieldname|title", or
    - "fieldname|title|extra_classes"

    Field "extra classes" with special styles:
        - "percentage": render column as %
        - "enhanced"
        - "debug-only"

.. figure:: screenshots/render_queryset.png

    render_queryset

More templatetags::

    def pdb(element)
    def ipdb(element)
    def format_datetime(dt, include_time=True, include_seconds=False, exclude_date=False)
    def format_date(dt)
    def format_datetime_with_seconds(dt)
    def format_time(t, include_seconds=False)
    def format_time_with_seconds(t)
    def format_timedelta(td_object, include_seconds=True)
    def format_timediff(t1, t2, include_seconds=True)
    def timeformat_seconds(seconds)
    def timeformat(seconds)
    # def format_number(value, decimals, grouping )
    def queryset_as_json(qs)
    def object_as_dict(instance, fields=None, exclude=None)
    def object_as_json(instance, fields=None, exclude=None, indent=0)

Custom rendering
----------------

For greated control of the final rendering, you can retrieve headers and data rows separately (as lists)
using:


    def render_queryset_as_table(* fields, queryset, options={})

For example, the equivalent of:

.. code:: python

        print(render_queryset_as_text(*fields, queryset=queryset, options=options))

can be reproduced as follows:

.. code:: python

        headers, rows = render_queryset_as_data(*fields, queryset=queryset, options=options)

        print('|'.join(headers))
        for row in rows:
            print('|'.join(row))
        print("")

Download the queryset as CSV or Excel file (xlsx)
-------------------------------------------------

For historical reasons, we provide two different approaches to export the queryset as a spreadsheet:

1) with the class SpreadsheetQuerysetExporter (see `Exporters`_ below)

2) parsing the queryset with the aid of `render_queryset_as_table`

The first requires a proper Queryset, while the second should work with either a Queryset
or a dictionary.

In both cases, two helper functions are available to build the HTTP response
required for attachment download:

- export_any_queryset
- export_any_dataset

Sample usage:

.. code:: python

    from django.utils import timezone
    from query_inspector.views import export_any_queryset
    from query_inspector.views import export_any_dataset


    def export_tracks_queryset(request, file_format='csv'):
        queryset = Track.objects.select_related('album', 'album__artist', )
        filename = '%s_%s.%s' % (
            timezone.localtime().strftime('%Y-%m-%d_%H-%M-%S'),
            "tracks",
            file_format,
        )

        return export_any_queryset(request, queryset, filename)


    def export_tracks_dataset(request, file_format='csv'):
        queryset = Track.objects.select_related('album', 'album__artist', )
        filename = '%s_%s.%s' % (
            timezone.localtime().strftime('%Y-%m-%d_%H-%M-%S'),
            "tracks",
            file_format,
        )
        fields = [
            "id",
            "name|Track",
            "album|Album",
        ]

        return export_any_dataset(request, *fields, queryset=queryset, filename=filename)

then in your template:

.. code:: html

    <div style="text-align: right;">
        <div class="toolbar">
            <label>Export Tracks queryset:</label>
            <a href="/tracks/download_queryset/xlsx/" class="button">Download (Excel)</a>
            <a href="/tracks/download_queryset/csv/" class="button">Download (CSV)</a>
        </div>
        <br />
        <div class="toolbar">
            <label>Export Tracks dataset:</label>
            <a href="/tracks/download_dataset/xlsx/" class="button">Download (Excel)</a>
            <a href="/tracks/download_dataset/csv/" class="button">Download (CSV)</a>
        </div>
    </div>

where:

.. code:: python

    urlpatterns = [
        ...
        path('tracks/download_queryset/csv/', views.export_tracks_queryset, {'file_format': 'csv', }),
        path('tracks/download_queryset/xlsx/', views.export_tracks_queryset, {'file_format': 'xlsx', }),
        path('tracks/download_dataset/csv/', views.export_tracks_dataset, {'file_format': 'csv', }),
        path('tracks/download_dataset/xlsx/', views.export_tracks_dataset, {'file_format': 'xlsx', }),
        ...
    ]


Generic helpers
---------------

def get_object_by_uuid_or_404(model, uuid_pk)

    Calls get_object_or_404(model, pk=uuid_pk)
    but also prevents "badly formed hexadecimal UUID string" unhandled exception

def prettify_json(data)

    Given a JSON string, returns it as a safe formatted HTML
    Sample usage in Model::

        def summary_prettified(self):
            return prettify_json(self.summary)

    then add it to the list of readonly_fields in the ModelAdmin

def cleanup_queryset(queryset)

    Remove multiple joins on the same table, if any

    WARNING: can alter the origin queryset order

Exporters
---------

def open_xlsx_file(filepath, mode="rb")
    Utility to open an archive supporting the "with" statement

class XslxFile(object)
    XSLX writer

    Requires: xlsxwriter

class SpreadsheetQuerysetExporter(object)
    Helper class to export a queryset to a spreadsheet.

Requirements:

    - xlsxwriter

Sample usage::

    with open_xlsx_file(filepath) as writer:
        self.export_queryset(writer, fields, queryset)
    assert writer.is_closed()

Sample usage::

    writer = csv.writer(output, delimiter=field_delimiter, quoting=csv.QUOTE_MINIMAL)
    exporter = SpreadsheetQuerysetExporter(writer, file_format='csv')
    exporter.export_queryset(
        queryset,
        included_fields=[
            'id',
            'description',
            'category__id',
            'created_by__id',
        ]
    )

