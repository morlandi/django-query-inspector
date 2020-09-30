from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.db.models import Max
from query_inspector import trace, qsdump


User = get_user_model()


class BasicTestCase(TestCase):

    def setUp(self):
        self.users = []
        for i in range(20):
            self.users = User.objects.create_user(
                username='user_%d' % i,
                is_active=bool(i % 3),
                is_staff=bool(i % 4),
                first_name='name_%d' % i,
                last_name='surname_%d' % i,
            )

    def prompt(self, message):
        print('\n')
        print('*' * 80)
        print(message)
        print('*' * 80)

    def test_qsdump(self):

        ########################################################################
        self.prompt('The whole User table')
        queryset = (User.objects
            .all()
        )
        qsdump("id", "username", "is_active", "is_staff", queryset=queryset)

        ########################################################################
        self.prompt('How to Use Aggregate Function')
        qs_dict = (User.objects
            .aggregate(
                total=Count('id'),
            )
        )
        trace(qs_dict)

        ########################################################################
        self.prompt('How to Group By')
        queryset = (User.objects
            .values(
                'is_active',
            )
            .annotate(
                total=Count('id'),
            )
            .order_by()
        )
        qsdump("is_active", "total", queryset=queryset)

        ########################################################################
        self.prompt('How to Filter and Sort a QuerySet With Group By')
        queryset = (User.objects
            .values(
                'is_active',
            )
            .filter(
                is_staff=True,
            )
            .annotate(
                total=Count('id'),
            )
            .order_by(
                'is_staff',
                'total',
            )
        )
        qsdump("is_active", "total", queryset=queryset)

        ########################################################################
        self.prompt('How to Combine Multiple Aggregations')
        queryset = (User.objects
            .values(
                'is_active',
            )
            .annotate(
                total=Count('id'),
                last_joined=Max('date_joined'),
            )
            .order_by()
        )
        qsdump("is_active", "total", "last_joined", queryset=queryset)

        ########################################################################
        self.prompt('How to Group by Multiple Fields')
        queryset = (User.objects
            .values(
                'is_active',
                'is_staff',
            )
            .annotate(
                total=Count('id'),
            )
            .order_by()
        )
        qsdump("is_active", "is_staff", "total", queryset=queryset)
