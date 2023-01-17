from django.apps import AppConfig


class   QueryInspectorConfig(AppConfig):
    name = 'query_inspector'
    # See:
    # "https://stackoverflow.com/questions/67006488/migrating-models-of-dependencies-when-changing-default-auto-field"
    # https://stackoverflow.com/questions/67006488/migrating-models-of-dependencies-when-changing-default-auto-field#67007098
    default_auto_field = 'django.db.models.AutoField'
