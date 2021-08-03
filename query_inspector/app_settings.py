from django.conf import settings

QUERY_SUPERUSER_ONLY = getattr(settings, 'QUERY_INSPECTOR_QUERY_SUPERUSER_ONLY', True)
QUERY_DEFAULT_LIMIT = getattr(settings, 'QUERY_INSPECTOR_QUERY_DEFAULT_LIMIT', '0')
SQL_BLACKLIST = getattr(
    settings, 'QUERY_INSPECTOR_SQL_BLACKLIST',
    (
        'ALTER',
        'RENAME ',
        'DROP',
        'TRUNCATE',
        'INSERT INTO',
        'UPDATE',
        'REPLACE',
        'DELETE',
        'CREATE TABLE',
        'GRANT',
        'OWNER TO'
    )
)
SQL_WHITELIST = getattr(
    settings,
    'QUERY_INSPECTOR_SQL_WHITELIST',
    (
        'CREATED',
        'UPDATED',
        'DELETED',
        'REGEXP_REPLACE'
    )
)
