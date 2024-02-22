import math
import json
import re
import datetime
import io
import csv
import decimal
from django.urls.exceptions import NoReverseMatch
from django import template
from django.urls import reverse
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.utils import formats
from django.utils.text import slugify
from django.db import models
from django.contrib.humanize.templatetags.humanize import intcomma
from django.core import serializers
from django.utils.encoding import is_protected_type
from django.forms.models import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder

register = template.Library()


@register.filter
def pdb(element):
    """ Usage: {{ template_var|pdb }}
        then inspect 'element' from pdb
    """
    import pdb
    pdb.set_trace()
    return element


@register.filter
def ipdb(element):
    """ Usage: {{ template_var|pdb }}
        then inspect 'element' from pdb
    """
    import ipdb
    ipdb.set_trace()
    return element

@register.simple_tag
def obj_from_result_list(result_list, index):
    instance = result_list[index]
    return instance

@register.filter
def format_datetime(dt, include_time=True, include_seconds=False, exclude_date=False):
    """
    Apply datetime format suggested for all admin views.

    Here we adopt the following rule:
    1) format date according to active localization
    2) append time in military format
    """

    if dt is None:
        return ''

    if isinstance(dt, datetime.datetime):
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            # naive datetime
            pass
        else:
            dt = timezone.localtime(dt)
    else:
        assert isinstance(dt, datetime.date)
        include_time = False

    if exclude_date:
        text = ''
    else:
        text = formats.date_format(dt, use_l10n=True, format='SHORT_DATE_FORMAT')
    if include_time:
        if len(text):
            text += ' '
        text += dt.strftime('%H:%M')
        if include_seconds:
            text += dt.strftime(':%S')
    return text


@register.filter
def format_date(dt):
    return format_datetime(dt, include_time=False)


@register.filter
def format_datetime_with_seconds(dt):
    return format_datetime(dt, include_time=True, include_seconds=True)


@register.filter
def format_time(t, include_seconds=False):
    text = t.strftime('%H:%M')
    if include_seconds:
        text += t.strftime(':%S')
    return text


@register.filter
def format_time_with_seconds(t):
    return format_time(t, include_seconds=True)


@register.filter
def format_timedelta(td_object, include_seconds=True):
    """
    Sample results:
        - 01:43:17
        - 4 dd + 08:43:17
    """

    if td_object is None:
        return ''

    total_seconds = td_object.total_seconds()
    num_days = total_seconds // (60*60*24)
    num_seconds = total_seconds % (60*60*24)

    text = datetime.datetime.utcfromtimestamp(num_seconds).strftime(
        '%H:%M:%S' if include_seconds else '%H:%M'
    )
    if num_days > 0:
        text = "%d dd + %s" % (num_days, text)
    return text


@register.filter
def format_timediff(t1, t2, include_seconds=True):
    if t1 is None or t2 is None:
        dt = None
    else:
        dt = t2 - t1
    return format_timedelta(dt, include_seconds)


@register.filter('timeformat_seconds')
def timeformat_seconds(seconds):
    # Remove milliseconds
    return timeformat(int(seconds))
    #return timeformat(seconds)


@register.filter('timeformat')
def timeformat(seconds):
    """
        Sample usage:
            <div>duration: {{ nsecs|timeformat %}</div>
    """

    if seconds is None or seconds=='':
        return ''

    try:
        ms = None
        if type(seconds) == float:
            ms = math.floor((seconds * 1000) % 1000)
            seconds = int(seconds)

        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        if h > 0:
            text = '%d:%02d:%02d' % (h, m, s)
        else:
            text = '%02d:%02d' % (m, s)

        if ms is not None and ms > 0:
            text += '.%03d' % ms
    except:
        text = ''

    return text


# def format_number(value, decimals, grouping ):
#     locale.setlocale(locale.LC_NUMERIC, ("en", "utf8"))
#     text = ''
#     if value > 0.0:
#         try:
#             format_string = "%%.%df" % decimals
#             text = locale.format(format_string, value, grouping)
#         except:
#             text = ''
#     return text


################################################################################
# Share queryset between Django and javascript
# See:
# https://brainstorm.it/snippets/share-queryset-between-django-and-javascript/


@register.filter
def queryset_as_json(qs):
    """
    Sample usage:
        {{user.list_tipi_movimento|queryset_as_json}}
    """
    json_data = serializers.serialize("json", qs)
    return mark_safe(json_data)


def object_as_dict(instance, fields=None, exclude=None):
    # data = {}
    # for field in instance._meta.local_fields:
    #     # Code stolen from Serializer
    #     value = field.value_from_object(instance)
    #     # Protected types (i.e., primitives like None, numbers, dates,
    #     # and Decimals) are passed through as is. All other values are
    #     # converted to string first.
    #     if is_protected_type(value):
    #         data[field.name] = value
    #     else:
    #         data[field.name] = field.value_to_string(instance)
    # return data
    return model_to_dict(instance, fields, exclude)


@register.filter
def object_as_json(instance, fields=None, exclude=None, indent=0):
    """
    Sample usage:
        {{original|object_as_json}}
    """

    try:
        data = object_as_dict(instance, fields, exclude)
    except Exception as e:
        data = {}

    json_data = json.dumps(data, indent=indent, cls=DjangoJSONEncoder)
    return mark_safe(json_data)

def render_queryset(*fields, queryset, mode, options):
    """
        mode:
            - "as_table"
            - "as_csv"
            - "as_text"

        fields, queryset, options:
            see render_queryset_as_table()
    """

    def remove_duplicates(l):
        """
        but keep the original order
        """
        l2 = []
        for item in l:
            if not item in l2:
                l2.append(item)
        return l2

    def build_columns(*fields):
        """
        From the sequence of supplied parameters, we build a list columns as follows:
            [{
                'name': name1,
                'title': title1,
                'classes': ['debug', ...]
            }, {
                ...
            ]
        """
        columns = []
        for field in fields:
            tokens = [t.strip() for t in field.split('|')]
            n = len(tokens)
            column = {
                'name': '',
                'title': '',
                'classes': '',
            }
            if n == 1:
                column.update({
                    'name': tokens[0],
                    'title': tokens[0].replace('_', ' '),
                })
            elif n >= 2:
                column.update({
                    'name': tokens[0],
                    'title': tokens[1],
                })
            if n > 2:
                column.update({
                    'classes': tokens[2]
                })
            columns.append(column)

        return columns

    def get_field_css_classes(field):
        css_classes = ['field-' + slugify(field['name']), ]
        if field['classes']:
            css_classes += field['classes'].split(' ')
        return css_classes

    def get_foreign_value(obj, column_name):
        """
        Borrowed from django-ajax-datatable
        """
        current_value = obj
        path_items = column_name.split('__')
        path_item_count = len(path_items)
        for current_path_item in path_items:
            try:
                current_value = getattr(current_value, current_path_item)
            except:
                # TODO: check this
                try:
                    current_value = [
                        getattr(current_value, current_path_item)
                        for current_value in current_value.get_queryset()
                    ]
                except:
                    try:
                        current_value = [getattr(f, current_path_item) for f in current_value]
                    except:
                        current_value = None

            if current_value is None:
                return None
        return current_value

    def get_cell_value(row, column):
        if type(row) == dict:
            value = row.get(column['name'])
        else:
            if '__' not in column['name']:
                value = getattr(row, column['name'])
            else:
                value = get_foreign_value(row, column['name'])
        return value

    def get_cell_value_as_numeric(row, column):
        value = get_cell_value(row, column)
        t = type(value)
        if t == int:
            return int(value)
        elif t == float:
            return float(value)
        return None

    def render_value_as_text(row, column, options, preserve_numbers=False):
        """
        Given a queryet row and the column spec,
        we render the cell content
        """
        # if type(row) == dict:
        #     value = row.get(column['name'])
        # else:
        #     value = getattr(row, column['name'])
        value = get_cell_value(row, column)

        #t = column.get('type', type(value))
        t = type(value)

        if value is None:
            text = ''
        elif t == datetime.date:
            if 'format_date' in options:
                text = formats.date_format(value, use_l10n=True, format=options.get('format_date'))
            else:
                text = format_datetime(value)
        elif t == datetime.datetime:
            text = format_datetime(value)
        elif t == datetime.time:
            text = format_time(value)
        elif t == int:
            if preserve_numbers:
                text = value
            else:
                text = '%d' % value
        elif t in [decimal.Decimal, float]:
            if preserve_numbers:
                text = float(value)
            else:
                text = str(value)
        else:
            text = str(value)

        return text

    def render_value_as_td(row, column, options):
        """
        Given a queryet row and the column spec,
        we render the cell content (as text) and wrap it in a '<td>' element
        """
        css_classes = get_field_css_classes(column)

        # if type(row) == dict:
        #     value = row.get(column['name'])
        # else:
        #     value = getattr(row, column['name'])
        value = get_cell_value(row, column)

        t = column.get('type', type(value))
        text = render_value_as_text(row, column, options)
        if t == int:
            text = intcomma(value)
            css_classes.append("numeric")
            if value == 0:
                css_classes.append("discreet")
        elif t == datetime.time:
            css_classes.append("numeric")
        else:
            if value is None:
                css_classes.append("discreet")

        #css_classes = list(set(css_classes))
        css_classes = remove_duplicates(css_classes)
        html = '<td class="%s">%s</td>' % (
            ' '.join(css_classes),
            text
        )

        return html

    # Sanity check
    if len(fields) <= 0:
        return ''

    # Collect the rows from the queryset (or list of dictionaries);
    #rows = queryset if type(queryset) == list else queryset.all()
    if type(queryset) == list:
        rows = queryset
        num_rows = len(rows)
    else:
        rows = queryset.all()
        num_rows = rows.count()

    # Experimental: detect all fields
    if '*' in fields and num_rows > 0:
        if type(rows[0]) == dict:
            fields = tuple(rows[0].keys())
        else:
            fields = [f.name for f in rows[0]._meta.fields]

    # If required (option "max_rows") limit the number of rows
    max_rows = options.get('max_rows', None)
    if max_rows is not None:
        rows = rows[:max_rows]

    # Build the list of columns
    columns = build_columns(*fields)

    # Sum column totals
    totals = None
    if options.get('add_totals', False):
        totals = ['', ] * len(columns)
        for row in rows:
            for index, column in enumerate(columns):
                value = get_cell_value_as_numeric(row, column)
                if value is not None:
                    if totals[index] == '':
                        totals[index] = 0
                    totals[index] += value

    # "percentage" columns: replace sum with average
    for index, column in enumerate(columns):
        if 'percentage' in column['classes']:
            totals[index] = int(float(totals[index]) / len(rows)) if len(rows) else ''

    # Render the rows as table
    if mode == "as_table":

        # render table head
        html = '<thead>'
        for column in columns:
            css_classes = get_field_css_classes(column)
            #css_classes = list(set(css_classes))
            css_classes = remove_duplicates(css_classes)
            html += '<th class="{css_classes}">{title}</th>'.format(
                css_classes=' '.join(css_classes),
                title=column['title'],
            )
        html += '</thead>'

        # render table body
        html += '<tbody>'
        for row in rows:
            html += '<tr>'
            for column in columns:
                html += render_value_as_td(row, column, options)
            html += '</tr>'

        # In case, add totals
        if totals is not None:
            totals = [intcomma(t) for t in totals]
            html += '<tr class="totals">'
            for index, column in enumerate(columns):
                css_classes = get_field_css_classes(column) + ['numeric', ]
                #css_classes = list(set(css_classes))
                css_classes = remove_duplicates(css_classes)
                html += '<td class="{css_classes}">{value}</th>'.format(
                    css_classes=' '.join(css_classes),
                    value=totals[index]
                )
            html += '</tr>'

        html += '</tbody>'

        text = mark_safe(html)

    # Render the rows as text
    elif mode in ["as_text", "as_csv", ]:

        # we'll collect all rendered rows in a data[] list
        data = []

        # first, the column heading
        data.append([c['title'] for c in columns])

        # then proceed the data rows
        for row in rows:
            data.append([render_value_as_text(row, column, options) for column in columns])

        # In case, add totals
        if totals is not None:
            totals = [str(t) for t in totals]
            data.append(totals)

        # export data[] as either csv of textfile content
        if mode == "as_csv":
            output = io.StringIO()
            writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
            for row in data:
                writer.writerow(row)
            text = output.getvalue()
        elif mode == "as_text":
            text = '\r\n'.join(['|'.join(row) for row in data])

    elif mode in ["as_data", ]:

        headers = [c['title'] for c in columns]
        data = []
        for row in rows:
            data.append([render_value_as_text(row, column, options, preserve_numbers=True) for column in columns])

        if options.get('transpose', False):
            headers2 = [headers[0], ] + [r[0] for r in data]
            data2 = []
            n = len(headers)
            for j in range(1, n):
                data2.append(
                    [headers[j], ] + [r[j] for r in data]
                )
            return headers2, data2

        return headers, data

    else:

        raise Exception('Unknown mode "%s"' % mode)

    return text


@register.simple_tag
def render_queryset_as_table(*fields, queryset, options={}):
    """
    Sample usage:

        <table class="simpletable smarttable">
            {% render_queryset_as_table "id" "last_name|Cognome" "first_name|Nome" ... queryset=operatori %}
        </table>

    queryset: a queryset of a list of dictionaries with data to rendered

    options:
        - max_rows: max n. of rows to be rendered (None=all)
        - format_date:  date formatting string; see:
            + https://docs.djangoproject.com/en/dev/ref/settings/#date-format
            + https://docs.djangoproject.com/en/dev/ref/templates/builtins/#date
        - add_totals: computes column totals and append results as bottom row

    fields: a list of field specifiers, espressed as:
        - "fieldname", or
        - "fieldname|title", or
        - "fieldname|title|extra_classes"

        Field "extra classes" with special styles:
            - "percentage": render column as %
            - "enhanced"
            - "debug-only"
    """

    transpose = options.get('transpose', False)
    if transpose:
        headers, data = render_queryset(*fields, mode="as_data", queryset=queryset, options=options)
        queryset2 = [dict(zip(headers, row)) for row in data]
        return render_queryset(*headers, mode="as_table", queryset=queryset2, options=options)

    return render_queryset(*fields, mode="as_table", queryset=queryset, options=options)


@register.simple_tag
def render_queryset_as_csv(*fields, queryset, options={}):
    return render_queryset(*fields, mode="as_csv", queryset=queryset, options=options)


@register.simple_tag
def render_queryset_as_text(*fields, queryset, options={}):
    return render_queryset(*fields, mode="as_text", queryset=queryset, options=options)


@register.simple_tag
def render_queryset_as_data(*fields, queryset, options={}):
    """
    For greated control of the final rendering,
    you can retrieve headers and data rows separately (as lists)

    For example, the equivalent of:

        print(render_queryset_as_text(*fields, queryset=queryset, options=options))

    can be reproduced as follows:

        headers, rows = render_queryset_as_data(*fields, queryset=queryset, options=options)

        print('|'.join(headers))
        for row in rows:
            print('|'.join(row))
        print("")
    """
    return render_queryset(*fields, mode="as_data", queryset=queryset, options=options)
