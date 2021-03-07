import os

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

SECRET_KEY = 'fake-key'
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    "query_inspector.tests",
]

#BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        #'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        'NAME': ':memory:',
    }
}

QUERYCOUNT = {
    'IGNORE_ALL_REQUESTS': False,
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
    'RESPONSE_HEADER': 'X-DjangoQueryCount-Count'
}

MIDDLEWARE = [
    'query_inspector.middleware.QueryCountMiddleware',
]
