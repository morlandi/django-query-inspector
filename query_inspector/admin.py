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
from django.utils.translation import gettext_lazy as _
from query_inspector import query_debugger, trace

from .app_settings import QUERY_DEFAULT_LIMIT
from .models import Query
from .sql import perform_query
from .sql import reload_stock_queries
from .views import normalized_export_filename
from .views import export_any_dataset


@admin.register(Query)
class QueryAdmin(admin.ModelAdmin):

    list_display = ("slug", 'stock', "title", "list_parameters", )
    list_filter = ('stock', )
    save_on_top = True

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'sql', 'default_parameters', 'notes', )
        }),
    )

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
        if obj.stock:
            return False
        if request.user.is_superuser:
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.stock:
            return False
        return True

    def get_readonly_fields(self, request, obj=None):
        if obj is not None and obj.stock:
            return ['sql', 'slug', 'title', 'notes', 'default_parameters', ]
        return []

    def get_prepopulated_fields(self, request, obj=None):
        if obj is not None and obj.stock:
            return {}
        return {"slug": ("title",)}

    def get_urls(self):
        urls = super().get_urls()
        info = self.model._meta.app_label, self.model._meta.model_name
        my_urls = [
            path('reload_stock_queries/', self.admin_site.admin_view(self.reload_stock_queries), name='%s_%s_reload_stock_queries' % info),
            path('<int:object_id>/preview/', self.admin_site.admin_view(self.preview), name='%s_%s_preview' % info),
            path('<int:object_id>/duplicate/', self.admin_site.admin_view(self.duplicate), name='%s_%s_duplicate' % info),
        ]
        return my_urls + urls

    def reload_stock_queries(self, request):
        info = self.model._meta.app_label, self.model._meta.model_name
        next = reverse('admin:%s_%s_changelist' % info, args=())
        try:
            reload_stock_queries()
            messages.info(request, _('Stock queries reloaded'))
        except Exception as e:
            messages.error(request, 'ERROR: ' + (str(e) or repr(e)))
            if settings.DEBUG:
                messages.warning(request, traceback.format_exc())
        return HttpResponseRedirect(next)

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
                if 'btn-export-csv' in request.POST:
                    filename = normalized_export_filename(obj.slug, "csv")
                    response = export_any_dataset(request, "*", queryset=recordset, filename=filename)
                    return response
                elif 'btn-export-jsonl' in request.POST:
                    filename = normalized_export_filename(obj.slug, "jsonl")
                    response = export_any_dataset(request, "*", queryset=recordset, filename=filename)
                    return response
                elif 'btn-export-xlsx' in request.POST:
                    filename = normalized_export_filename(obj.slug, "xlsx")
                    response = export_any_dataset(request, "*", queryset=recordset, filename=filename)
                    return response

                # Save default parameters
                obj.default_parameters = params
                obj.save(update_fields=['default_parameters', ])

                end = time.perf_counter()
                elapsed = '%.2f' % (end - start)
            except Exception as e:
                recordset = []
                elapsed = ''
                messages.error(request, str(e))

        try:
            import xlsxwriter
            xlsxwriter_available = True
        except ModuleNotFoundError as e:
            xlsxwriter_available = False

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
                'xlsxwriter_available': xlsxwriter_available,
            }
        )
