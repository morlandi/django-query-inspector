import re
from django.db import models
from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext_lazy as _
from .app_settings import QUERY_SUPERUSER_ONLY


_named_parameters_re = re.compile(r"\%\(([^\)]+)\)s")


class Query(models.Model):
    title = models.CharField(blank=True, max_length=128)
    slug = models.SlugField(unique=True)
    sql = models.TextField(null=False, blank=True)
    default_parameters = models.JSONField(null=False, default=dict, blank=True)
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
        obj.save()
        return obj
