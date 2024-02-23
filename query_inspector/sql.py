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


def reload_stock_queries():

    from .models import Query

    # Build the list of slq_views if a suitable callback has been given
    sql_views = []
    f_list_sql_views = app_settings.QUERY_STOCK_VIEWS
    if f_list_sql_views is not None:
        sql_views = f_list_sql_views()

    # Build the list of sql_queries; it can be either a list ...
    sql_queries = app_settings.QUERY_STOCK_QUERIES
    # ... or a callable which returns a list
    if callable(sql_queries):
        sql_queries = sql_queries()

    # Cleanup
    stock_queries_slugs = [row['slug'] for row in sql_queries]
    sql_views_slugs = [klass._meta.db_table for klass in sql_views]
    slugs = stock_queries_slugs + sql_views_slugs
    #Query.objects.filter(slug__in=slugs, stock=False).delete()
    Query.objects.filter(stock=True).exclude(slug__in=slugs).delete()

    # Insert/update records as required
    n = 0
    for row in sql_queries:
        try:
            query = Query.objects.get(slug=row['slug'], stock=True)
        except Query.DoesNotExist:
            query = Query(slug=row['slug'], stock=True)
        query.title = row.get('title', '')
        query.sql = row['sql']
        query.notes = row.get('notes', '')
        query.save()
        n += 1

    # Also add sql views
    for sql_view in sql_views:
        slug = sql_view._meta.db_table
        try:
            query = Query.objects.get(slug=slug, stock=True)
        except Query.DoesNotExist:
            query = Query(slug=slug, stock=True)
        query.title = '%sVIEW "%s" (Model %s)' % (
            'MATERIALIZED ' if sql_view.materialized else '',
            slug,
            sql_view.__name__
        )
        query.sql = 'select * from ' + slug
        # query.notes = row['notes']
        query.from_view = True
        query.from_materialized_view = sql_view.materialized
        query.save()
        n += 1

    return n


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
