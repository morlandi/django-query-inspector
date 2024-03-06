import pprint
import json
import uuid
from functools import partial
from django.db.models.query import QuerySet
from .templatetags.query_inspector_tags import render_queryset_as_text
from .templatetags.query_inspector_tags import render_queryset_as_data

# Check if sqlparse is available for indentation
try:
    import sqlparse
except ImportError:
    class sqlparse:
        @staticmethod
        def format(text, *args, **kwargs):
            return text

# Check if termcolor is available for coloring
try:
    import termcolor
except ImportError:
    termcolor = None


# Check if Pygments is available for coloring
try:
    import pygments
    from pygments.lexers import SqlLexer
    from pygments.formatters import TerminalTrueColorFormatter
except ImportError:
    pygments = None


# Check if tabulate is available for formatting
try:
    import tabulate
except ImportError:
    tabulate = None


def trace(message, color='yellow', on_color=None, attrs=None, prompt='', prettify=False):
    if prompt:
        text = prompt + ': \n' + message
    else:
        text = message

    if prettify:
        text = pprint.pformat(text)

    if termcolor and (color or on_color):
        termcolor.cprint(text, color=color, on_color=on_color, attrs=attrs)
    else:
        print(text)


def prettyprint_query(query, params=None, colorize=True, prettify=True, reindent=True):

    def _str_query(sql, params):

        def escape(v):
            if type(v) in [uuid.UUID, str, ]:
                return "'%s'" % v
            return v

        if type(params) == dict:
            params_ex = {
                k: escape(v) for k, v in params.items()
            }
            sql = sql % params_ex

        # Borrowed by morlandi from sant527
        # See: https://github.com/bradmontgomery/django-querycount/issues/22
        if prettify:
            sql = sqlparse.format(sql, reindent=reindent)

        if colorize and pygments:
            # Highlight the SQL query
            sql = pygments.highlight(
                sql,
                SqlLexer(),
                TerminalTrueColorFormatter(style='monokai')
                #TerminalTrueColorFormatter()
            )

        return sql

    sql = _str_query(query.replace('\n', ' '), params).strip()
    print(sql)
    if params is not None:
        trace('params[]: ' + str(params), color='black', on_color='on_white')
    print("-" * 80)


def prettyprint_queryset(qs, colorize=True, prettify=True, reindent=True):
    prettyprint_query(str(qs.query), colorize=colorize, prettify=prettify, reindent=reindent)


def trace_func(fn):
    """
    Sample usage:

        class MyClass(object):
            ...

            @trace_func
            def myfunc(self, user, obj):
                ...
    """
    def func_wrapper(*args, **kwargs):

        mytrace = partial(trace, color='grey', on_color='on_white')

        mytrace('>>> %s()' % fn.__name__)
        mytrace('> args:')
        mytrace(args)
        mytrace('> kwargs:')
        mytrace(kwargs)
        ret = fn(*args, **kwargs)
        mytrace('> return value:')
        mytrace(ret)
        mytrace('<<< %s()' % fn.__name__)
        return ret
    return func_wrapper


def qsdump(*fields, queryset, max_rows=None, render_with_tabulate=True, title=""):

    if title:
        spaces = int((80 - len(title)) / 2)
        trace(' '*spaces + title + ' '*spaces, color='yellow', attrs=['reverse', ])

    is_queryset = isinstance(queryset, QuerySet)
    if is_queryset:
        prettyprint_queryset(queryset)

    options = {
        'max_rows': max_rows,
    }

    headers, rows = render_queryset_as_data(*fields, queryset=queryset, options=options)

    if tabulate and render_with_tabulate:
        tablefmt = "fancy_grid"
        trace(
            tabulate.tabulate(rows, headers=headers, tablefmt=tablefmt),
            color='white'
        )
    else:

        # render as text
        text = render_queryset_as_text(*fields, queryset=queryset, options=options)

        # Display headers (enhanced)
        trace(json.dumps(headers), color='white', attrs=['reverse', ])

        # Display rows
        for row in rows:
            trace(json.dumps(row), color='white')

    # Table summary
    num_records = queryset.count() if is_queryset else len(queryset)
    summary = '# records: %d/%d' % (len(rows), num_records)
    trace(summary, color='white', attrs=['reverse', ])


def qsdump2(queryset, include=[], exclude=[], max_rows=None, render_with_tabulate=True, title=""):

    if isinstance(queryset, QuerySet):
        all_fields = [f.name for f in queryset.model._meta.fields]
    elif len(queryset)>0 and isinstance(queryset[0], dict):
        all_fields = list(queryset[0].keys())
    else:
        all_fields = []

    assert not (include and exclude)

    fields = all_fields
    if include:
        fields = [f for f in include if f in all_fields]
    elif exclude:
        fields = [f for f in all_fields if f not in exclude]

    trace(str(fields), prompt='fields')
    if len(fields) <= 0:
        fields = ['*', ]
    qsdump(*fields, queryset=queryset, max_rows=max_rows, render_with_tabulate=render_with_tabulate, title=title)
