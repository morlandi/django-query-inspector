import re
from django.db import models
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from .app_settings import QUERY_SUPERUSER_ONLY


_named_parameters_postgresql_re = re.compile(r"\%\(([^\)]+)\)s")
_named_parameters_sqlite_re = re.compile(r"\$([^ )]+)")


class QueryManager(models.Manager):

    def get_active_query_from_slug(self, slug):
        """
        Since slug is no longer unique, you can use this helper to identify the active query
        associated with a certain slug (thus excluding all disabled queries);
        in case of ambiguity it returns None

        Example:

            my_query = Query.objects.get_query_for_slug(query_name)

        """
        queryset = (
            self.get_queryset()
            .filter(
                enabled=True,
                #slug=slug,
            )
        )
        return queryset.get(slug=slug)
        # if queryset.count() == 1:
        #     return queryset.first()
        # return None


class Query(models.Model):
    title = models.CharField(blank=True, max_length=128)
    slug = models.SlugField(unique=False)
    enabled = models.BooleanField(null=False, default=True)
    sql = models.TextField(null=False, blank=True)
    default_parameters = models.JSONField(null=False, default=dict, blank=True)
    notes = models.TextField(null=False, blank=True)
    stock = models.BooleanField(null=False, default=False, editable=False)
    from_view = models.BooleanField(null=False, default=False, editable=False)
    from_materialized_view = models.BooleanField(null=False, default=False, editable=False)

    objects = QueryManager()

    class Meta:
        abstract = False
        verbose_name = _("Query")
        verbose_name_plural = _("Queries")
        ordering = ('-stock', 'slug', )

    def __str__(self):
        return self.title or self.slug

    # def get_absolute_url(self):
    #     return reverse("django_sql_dashboard-dashboard", args=[self.slug])

    # def get_edit_url(self):
    #     return reverse("admin:django_sql_dashboard_dashboard_change", args=(self.id,))

    def can_execute(self, request):
        if request.user.is_superuser or not QUERY_SUPERUSER_ONLY:
            return True
        return False

    @property
    def is_duplicated(self):
        """
        Returns True iif this query is enabled, and another enabled query
        having the same slug has been detected
        """
        duplicated = False
        if self.enabled:
            try:
                the_query = Query.objects.get_active_query_from_slug(self.slug)
            except Query.MultipleObjectsReturned:
                duplicated = True
            except Exception as e:
                pass
        return duplicated

    def extract_named_parameters(self):

        def is_sqlite_engine():
            """
            TODO: find a better way
            """
            return 'sqlite3' in settings.DATABASES['default']['ENGINE']

        if is_sqlite_engine():
            _named_parameters_re = _named_parameters_sqlite_re
        else:
            _named_parameters_re = _named_parameters_postgresql_re

        params = _named_parameters_re.findall(self.sql)
        # Validation step: after removing params, are there
        # any single `%` symbols that will confuse psycopg2?
        without_params = _named_parameters_re.sub("", self.sql)
        without_double_percents = without_params.replace("%%", "")
        if "%" in without_double_percents:
            raise ValueError(r"Found a single % character")

        # Remove duplicates
        params = list(set(params))

        return params

    def clone(self, request=None):

        def new_slug(slug):
            # split name part and trailing version number;
            # i.e.:  "sample2" --> ['sample', 2]
            #        "sample" --> ['sample', 0]
            groups = re.match('.*?([0-9]+)$', slug)
            if groups is None:
                radix = slug
                version = 0
            else:
                radix = slug[0:-len(groups[1])]
                version = int(groups[1])

            # Increment version until we find a suitable name
            while True:
                version += 1
                new_text = radix + str(version)
                if not Query.objects.filter(slug=new_text).exists():
                    return new_text

        info = self._meta.app_label, self._meta.model_name
        required_permission = '%s.add_%s' % info
        if request and not request.user.has_perm(required_permission):
            raise PermissionDenied
        obj = self._meta.model.objects.get(pk=self.pk)
        obj.pk = None
        obj.slug = new_slug(obj.slug)
        obj.title = obj.slug
        obj.stock = False
        obj.from_view = False
        obj.from_materialized_view = False
        obj.save()
        return obj
