import pprint
from functools import partial
from .templatetags.query_inspector_tags import render_queryset_as_text


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



def prettyprint_query(query, colorize=True, prettify=True):

    def _str_query(sql):

        # Borrowed by morlandi from sant527
        # See: https://github.com/bradmontgomery/django-querycount/issues/22
        if prettify:
            sql = sqlparse.format(sql, reindent=True)

        if colorize and pygments:
            # Highlight the SQL query
            sql = pygments.highlight(
                sql,
                SqlLexer(),
                TerminalTrueColorFormatter(style='monokai')
                #TerminalTrueColorFormatter()
            )

        return sql

    sql = _str_query(query)
    print(sql)


def prettyprint_queryset(qs, colorize=True, prettify=True):
    prettyprint_query(str(qs.query), colorize=colorize, prettify=prettify)


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


def qsdump(*fields, queryset, max_rows=None):
    options = {
        'max_rows': max_rows,
    }
    prettyprint_queryset(queryset)
    trace(
        render_queryset_as_text(*fields, queryset=queryset, options=options),
        color='white'
    )
    trace('# records: %d' % queryset.count(), color='white', attrs=['reverse', ])


