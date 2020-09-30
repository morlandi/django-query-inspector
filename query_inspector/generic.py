import uuid
import json
from django.http import Http404
from django.utils.safestring import mark_safe
from django.shortcuts import get_object_or_404


def get_object_by_uuid_or_404(model, uuid_pk):
    """
    Calls get_object_or_404(model, pk=uuid_pk)
    but also prevents "badly formed hexadecimal UUID string" unhandled exception
    """
    if isinstance(uuid_pk, str):
        try:
            uuid.UUID(uuid_pk)
        except Exception as e:
            raise Http404(str(e))
    return get_object_or_404(model, pk=uuid_pk)


def prettify_json(data):
    """
    Given a JSON string, returns it as a safe formatted HTML

    Sample usage in Model:

        def summary_prettified(self):
            return prettify_json(self.summary)

    then add it to the list of readonly_fields in the ModelAdmin
    """
    if isinstance(data, str):
        data = json.loads(data)
    html = '<pre>' + json.dumps(data, sort_keys=True, indent=4) + '</pre>'
    return mark_safe(html)


def cleanup_queryset(queryset):
    """
    Remove multiple joins on the same table, if any

    WARNING: can alter the origin queryset order
    """
    return queryset.model.objects.filter(pk__in=[instance.pk for instance in queryset.all()])
