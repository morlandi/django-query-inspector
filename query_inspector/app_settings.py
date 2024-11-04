from django.conf import settings

QUERY_SUPERUSER_ONLY = getattr(settings, 'QUERY_INSPECTOR_QUERY_SUPERUSER_ONLY', True)
QUERY_DEFAULT_LIMIT = getattr(settings, 'QUERY_INSPECTOR_QUERY_DEFAULT_LIMIT', '0')
QUERY_STOCK_QUERIES = getattr(settings, 'QUERY_INSPECTOR_QUERY_STOCK_QUERIES', [])
QUERY_STOCK_VIEWS = getattr(settings, 'QUERY_INSPECTOR_QUERY_STOCK_VIEWS', None)
DEFAULT_CSV_FIELD_DELIMITER = getattr(settings, 'QUERY_INSPECTOR_DEFAULT_CSV_FIELD_DELIMITER', ';')


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

REMOTE_HOST = getattr(settings, 'SITECOPY_REMOTE_HOST', '')
REMOTE_PROJECT_INSTANCE = getattr(settings, 'SITECOPY_REMOTE_PROJECT_INSTANCE', '')
REMOTE_MEDIA_FOLDER = getattr(settings, 'SITECOPY_REMOTE_MEDIA_FOLDER', '')  # /home/%s/public/media/' % PROJECT)
PRE_CUSTOM_ACTIONS = getattr(settings, 'SITECOPY_PRE_CUSTOM_ACTIONS', [])
POST_CUSTOM_ACTIONS = getattr(settings, 'SITECOPY_POST_CUSTOM_ACTIONS', [])

