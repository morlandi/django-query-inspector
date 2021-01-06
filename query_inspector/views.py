import io
import os
import csv
from django.utils import timezone
from django.template.defaultfilters import slugify
from django.http import StreamingHttpResponse
from .exporters import open_xlsx_file, SpreadsheetQuerysetExporter
from .templatetags.query_inspector_tags import render_queryset_as_data


def normalized_export_filename(title, extension):
    """
    Provides a default filename; "%Y-%m-%d_%H-%M-%S__TITLE.EXTENNSION"
    """
    filename = timezone.localtime().strftime('%Y-%m-%d_%H-%M-%S__') + slugify(title)
    if extension.startswith(os.path.extsep):
        filename += extension
    else:
        filename += os.path.extsep + extension
    return filename


def export_any_queryset(request, queryset, filename, excluded_fields=[], included_fields=[], csv_field_delimiter = ";"):
    """
    Export queryset using SpreadsheetQuerysetExporter()
    """

    name, extension = os.path.splitext(filename)
    file_format = extension[1:]

    output = None
    if file_format == 'csv':
        content_type = 'text/csv'
        output = io.StringIO()
        writer = csv.writer(output, delimiter=csv_field_delimiter, quoting=csv.QUOTE_MINIMAL)
        exporter = SpreadsheetQuerysetExporter(writer, file_format=file_format)
        exporter.export_queryset(queryset)
    elif file_format == 'xlsx':
        content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        #content_type = 'application/vnd.ms-excel'
        output = io.BytesIO()
        with open_xlsx_file(output) as writer:
            # # Write Spreadsheet
            # writer.write_headers_from_strings(
            #     ['Cliente', 'Commessa', 'Progetto', 'Attività', ] +
            #     ['Totale', ],
            # )
            # writer.apply_autofit()
            exporter = SpreadsheetQuerysetExporter(writer, file_format=file_format)
            exporter.export_queryset(queryset, excluded_fields=excluded_fields, included_fields=included_fields)
            writer.apply_autofit()
        assert writer.is_closed()
    else:
        raise Exception('Wrong export file format "%s"' % file_format)

    # send "output" object to stream with mimetype and filename
    assert output is not None
    output.seek(0)
    # response = HttpResponse(
    #     output.read(),
    response = StreamingHttpResponse(
        output,
        content_type=content_type,
    )
    #response['Content-Disposition'] = 'inline; filename="%s"' % filename
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename

    return response


def export_any_dataset(request, *fields, queryset, filename, csv_field_delimiter = ";"):
    """
    Export queryset using render_queryset_as_data()
    """

    name, extension = os.path.splitext(filename)
    file_format = extension[1:]
    headers, rows = render_queryset_as_data(*fields, queryset=queryset)

    output = None
    if file_format == 'csv':
        content_type = 'text/csv'
        output = io.StringIO()
        writer = csv.writer(output, delimiter=csv_field_delimiter, quoting=csv.QUOTE_MINIMAL)

        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)

    elif file_format == 'xlsx':
        content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        #content_type = 'application/vnd.ms-excel'
        output = io.BytesIO()
        with open_xlsx_file(output) as writer:

            writer.write_headers_from_strings(headers)
            for row in rows:
                writer.writerow(row)
            writer.apply_autofit()

        assert writer.is_closed()
    else:
        raise Exception('Wrong export file format "%s"' % file_format)

    # send "output" object to stream with mimetype and filename
    assert output is not None
    output.seek(0)
    # response = HttpResponse(
    #     output.read(),
    response = StreamingHttpResponse(
        output,
        content_type=content_type,
    )
    #response['Content-Disposition'] = 'inline; filename="%s"' % filename
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename

    return response
