import time
import traceback
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import admin
from django.conf import settings
from urllib.parse import urlencode
from django.urls import path
from django.shortcuts import render
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext_lazy as _
from query_inspector import query_debugger, trace

from .app_settings import QUERY_DEFAULT_LIMIT
from .models import Query
from .sql import perform_query



@admin.register(Query)
class QueryAdmin(admin.ModelAdmin):

    list_display = ("slug", "title", "list_parameters")
    prepopulated_fields = {"slug": ("title",)}
    save_on_top = True

    def list_parameters(self, obj):
        try:
            text = obj.extract_named_parameters()
        except Exception as e:
            text = _("ERROR") + ': ' + str(e)
        return text
    list_parameters.short_description = _('Parameters')

    def has_change_permission(self, request, obj=None):
        if obj is None:
            return True
        if request.user.is_superuser:
            return True
        return False

    def get_urls(self):
        urls = super().get_urls()
        info = self.model._meta.app_label, self.model._meta.model_name
        my_urls = [
            path('<int:object_id>/preview/', self.admin_site.admin_view(self.preview), name='%s_%s_preview' % info),
            path('<int:object_id>/duplicate/', self.admin_site.admin_view(self.duplicate), name='%s_%s_duplicate' % info),
        ]
        return my_urls + urls

    def duplicate(self, request, object_id):
        info = self.model._meta.app_label, self.model._meta.model_name
        viewname = 'admin:%s_%s_change' % info
        try:
            obj = self.model.objects.get(id=object_id)
            new_obj = obj.clone(request)
            messages.info(request, _('Query has been duplicated'))
            next = reverse(viewname, args=(new_obj.pk, ))
        except Exception as e:
            messages.error(request, 'ERROR: ' + (str(e) or repr(e)))
            if settings.DEBUG:
                messages.warning(request, traceback.format_exc())
            next = reverse(viewname, args=(obj.pk, ))
        return HttpResponseRedirect(next)

    def preview(self, request, object_id):

        modeladmin = self
        opts = modeladmin.model._meta
        obj = self.model.objects.get(id=object_id)

        if not obj.can_execute(request):
            raise PermissionDenied

        # Adapted from django-sql-dashboard
        parameters = []
        try:
            parameters = obj.extract_named_parameters()
        except ValueError as e:
            if "%" in obj.sql:
                messages.error(request, r"Invalid query - try escaping single '%' as double '%%'")
            else:
                messages.error(request, str(e))

        params = {
            parameter: request.POST.get(parameter, request.GET.get(parameter, ""))
            for parameter in parameters
        }

        # Load default parameters
        if request.method =="GET":
            for key, value in params.items():
                if not value:
                    params[key] = obj.default_parameters.get(key, '')
        # extra_qs = "&{}".format(urlencode(params)) if params else ""

        sql_limit = request.POST.get('sql_limit', request.GET.get('sql_limit', QUERY_DEFAULT_LIMIT))
        try:
            sql_limit = int(sql_limit)
        except:
            sql_limit = 0

        recordset = []
        elapsed = None
        if request.method == 'POST':
            try:
                start = time.perf_counter()

                sql = obj.sql
                if sql_limit > 0:
                    sql += ' limit %d' % sql_limit

                recordset = perform_query(sql, params, log=True, validate=True)

                # Save default parameters
                obj.default_parameters = params
                obj.save(update_fields=['default_parameters', ])

                end = time.perf_counter()
                elapsed = '%.2f' % (end - start)
            except Exception as e:
                recordset = []
                elapsed = ''
                messages.error(request, str(e))

        return render(
            request,
            'admin/query_inspector/query/preview.html', {
                'admin_site': self.admin_site,
                'title': _('Preview'),
                'opts': opts,
                'app_label': opts.app_label,
                'original': obj,
                'has_view_permission': self.has_view_permission(request, obj),
                'has_add_permission': self.has_add_permission(request),
                'has_change_permission': self.has_change_permission(request, obj),
                'has_delete_permission': self.has_delete_permission(request, obj),
                'params': params.items(),
                # 'extra_qs': extra_qs,
                'recordset': recordset,
                'elapsed': elapsed,
                'sql_limit': sql_limit,
            }
        )
