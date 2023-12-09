# import os
# import sys
import signal
# import datetime
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import (
    DEFAULT_DB_ALIAS, DatabaseError, IntegrityError, connections, router,
    transaction,
)
from query_inspector.sql import reload_stock_queries


class Command(BaseCommand):
    help = 'Load stock (readonly) queries from settings.QUERY_INSPECTOR_QUERY_STOCK_QUERIES list'

    def __init__(self, logger=None, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        signal.signal(signal.SIGINT, lambda signum, frame: sys.exit(0))

    def add_arguments(self, parser):
        parser.add_argument(
            '--database', default=DEFAULT_DB_ALIAS,
            help='Nominates a specific database to load fixtures into. Defaults to the "default" database.',
        )

    def handle(self, *args, **options):
        self.using = options['database']

        with transaction.atomic(using=self.using):
            n = reload_stock_queries()
            print('%d stock queries have been created or updated' % n)

        # Close the DB connection -- unless we're still in a transaction. This
        # is required as a workaround for an edge case in MySQL: if the same
        # connection is used to create tables, load data, and query, the query
        # can return incorrect results. See Django #7572, MySQL #37735.
        if transaction.get_autocommit(self.using):
            connections[self.using].close()
