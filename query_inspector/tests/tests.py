import datetime
import django
from django.conf import settings
from django.test import TestCase
from query_inspector.tests.models import Sample
import query_inspector

NUM_RECORDS = 100



class BaseTestCase(TestCase):

    #fixtures = [os.path.join(FIXTURES_DIR, 'workflows.json'), ]

    def setUp(self):
        self.populateModels()

    def tearDown(self):
        pass

    def populateModels(self):
        now = datetime.datetime.now().date()
        for i in range(NUM_RECORDS):
            Sample.objects.create(
                created=now - datetime.timedelta(days=i)
            )


class SimpleTestCase(BaseTestCase):

    def test_simple(self):

        self.assertEqual(NUM_RECORDS, Sample.objects.count())
