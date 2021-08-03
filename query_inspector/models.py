import re
#from django.conf import settings
from django.db import models
# from django.urls import reverse
# from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from .app_settings import QUERY_SUPERUSER_ONLY


_named_parameters_re = re.compile(r"\%\(([^\)]+)\)s")


class Query(models.Model):
    title = models.CharField(blank=True, max_length=128)
    slug = models.SlugField(unique=True)
    sql = models.TextField(null=False, blank=True)
    notes = models.TextField(null=False, blank=True)

    class Meta:
        abstract = False
        verbose_name = _("Query")
        verbose_name_plural = _("Queries")

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

    def extract_named_parameters(self):
        params = _named_parameters_re.findall(self.sql)
        # Validation step: after removing params, are there
        # any single `%` symbols that will confuse psycopg2?
        without_params = _named_parameters_re.sub("", self.sql)
        without_double_percents = without_params.replace("%%", "")
        if "%" in without_double_percents:
            raise ValueError(r"Found a single % character")
        return params
