import time
import functools
import re
from django.db import connection
from django.forms import ValidationError
from query_inspector import prettyprint_queryset, prettyprint_query, trace, qsdump
from . import app_settings


def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


# borrowed from django-sql-explorer
def passes_blacklist(sql):
    clean = functools.reduce(
        lambda s, term: s.upper().replace(term, ''),
        [t.upper() for t in app_settings.SQL_WHITELIST],
        sql
    )
    regex_blacklist = [
        (
            bl_word,
            re.compile(
                r'(^|\W){}($|\W)'.format(bl_word),
                flags=re.IGNORECASE
            )
        )
        for bl_word in app_settings.SQL_BLACKLIST
    ]
    fails = [
        bl_word
        for bl_word, bl_regex in regex_blacklist
        if bl_regex.findall(clean)
    ]
    return not any(fails), fails


def perform_query(sql, params, log=False, validate=True):
    start = time.perf_counter()
    if log:
        print('')
        trace(sql)
        print('')
        prettyprint_query(sql, params=params, reindent=False)

    # borrowed from django-sql-explorer
    if validate:
        passed_blacklist, failing_words = passes_blacklist(sql)
        error = "Query failed the SQL blacklist: %s" % ', '.join(failing_words) if not passed_blacklist else None
        if error:
            raise ValidationError(
                error,
                code="InvalidSql"
            )

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        rows = dictfetchall(cursor)

    end = time.perf_counter()
    if log:
        trace(' query time: {elapsed:.2f}s '.format(
            elapsed=end - start,
        ), color='white', on_color='on_blue', attrs=['bold'])
    return rows
