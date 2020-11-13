import uuid
import datetime
from django.db import models

################################################################################
# class XslxFile

def open_xlsx_file(filepath, mode="rb"):
    """
    Utility to open an archive supporting the "with" statement;
    Sample usage:

        with open_xlsx_file(filepath) as writer:
            self.export_queryset(writer, fields, queryset)
        assert writer.is_closed()
    """
    archive = XslxFile(filepath)
    archive.open()
    return archive


class XslxFile(object):
    """
    XSLX writer

    Requires: xlsxwriter
    """

    filepath = ''
    workbook = None
    worksheet = None
    options = {
        'remove_timezone': True,
        'in_memory': False,
    }
    row_index = 0
    column_widths = None

    def __init__(self, filepath, options=None):
        self.filepath = filepath
        if options is not None:
            self.options = options

    def __enter__(self):
        """
        Support "with" statement;
        see:
            - http://effbot.org/zone/python-with-statement.htm
            - https://preshing.com/20110920/the-python-with-statement-by-example/
        """
        return self

    def __exit__(self, type, value, traceback):
        """
        Support "with" statement
        """
        self.close()

    def is_open(self):
        return self.workbook != None

    def is_closed(self):
        return self.workbook == None

    def open(self):
        assert self.is_closed()
        self._new_workbook()

    def _new_workbook(self):
        import xlsxwriter
        self.workbook = xlsxwriter.Workbook(self.filepath, self.options)
        self.num_formats = {
            'datetime': self.workbook.add_format({'num_format': 'YYYY-MM-DD HH:MM:SS'}),
            'boolean': self.workbook.add_format({'num_format': 'BOOLEAN'}),
        }
        self._new_worksheet()

    def _new_worksheet(self):
        self.worksheet = self.workbook.add_worksheet()
        self.row_index = -1
        #worksheet.add_write_handler(uuid.UUID, XslxFile._xslx_write_uuid)

    def close(self):
        assert self.is_open()
        self.workbook.close()
        self.workbook = None

    def writerow(self, row):
        self.row_index += 1
        self.worksheet.write_row(self.row_index, 0, row)

        # Update estimation for column widths (only for some field types)
        if self.column_widths is not None:
            for i, column_width in enumerate(self.column_widths):
                if column_width > 0 and i < len(row):
                    width = len(str(row[i]))
                    if width > column_width:
                        self.column_widths[i] = width

        return self.row_index

    def write_headers_from_strings(self, headers):
        self.row_index = 0
        self.worksheet.write_row(self.row_index, 0, headers)
        self.column_widths = [0, ] * len(headers)
        for col, header in enumerate(headers):
            self.column_widths[col] = len(str(header))

    def write_headers_from_fields(self, fields):
        self.row_index = 0

        #self.worksheet.write_row(self.row_index, 0, [f.name for f in fields])
        self.worksheet.write_row(self.row_index, 0, [f['name'] for f in fields])

        self.column_widths = [0, ] * len(fields)
        for col, field in enumerate(fields):
            fname = field['name']
            ftype = field['type']

            # Set format of columns based on content type
            if ftype == 'DateTimeField':
                self.worksheet.set_column(col, col, width=20, cell_format=self.num_formats['datetime'])
            elif ftype == 'BooleanField':
                self.worksheet.set_column(col, col, width=10, cell_format=self.num_formats['boolean'])
            # Collect estimation for column widths (only for some field types)
            if ftype in [
                    'CharField',
                    'TextField',
                    'SlugField',
                    'UUIDField',
                    'ForeignKey',
                ]:
                self.column_widths[col] = len(fname)

    def apply_autofit(self):
        if self.column_widths is not None:
            for i, column_width in enumerate(self.column_widths):
                if column_width > 0:
                    self.worksheet.set_column(i, i, width=min(int(column_width * 1.0), 60))

    # # https://xlsxwriter.readthedocs.io/example_user_types1.html#example-writing-user-defined-types-1
    # @staticmethod
    # def _xslx_write_uuid(worksheet, row, col, token, format=None):
    #     return worksheet.write_string(row, col, str(token), format)


################################################################################
# Helpers

def fix_datetime(dt):
    if dt is None:
        return None
    # remove microseconds and timezone from datetime
    dt2 = datetime.datetime(
        dt.year, dt.month, dt.day,
        dt.hour, dt.minute, int(dt.second + dt.microsecond / 1E6 + 0.5) % 60
    )
    return dt2

################################################################################
# class SpreadsheetQuerysetExporter

class SpreadsheetQuerysetExporter(object):
    """
    Helper class to export a queryset to a spreadsheet.

    Sample usage:

        writer = csv.writer(output, delimiter=field_delimiter, quoting=csv.QUOTE_MINIMAL)
        exporter = SpreadsheetQuerysetExporter(writer, file_format='csv')
        exporter.export_queryset(
            queryset,
            included_fields=[
                'id',
                'description',
                'category__id',
                'created_by__id',
            ]
        )
    """
    writer = None
    file_format = None

    def __init__(self, writer, file_format):
        """
        <writer>: a csv.writer or XslxFile() object to write into
        <file_format>: either 'csv' or 'xlsx'
        """
        self.writer = writer
        self.file_format = file_format
        assert self.file_format in ['csv', 'xlsx', ]

    def export_queryset(self, queryset, excluded_fields=[], included_fields=[]):
        """
        <queryset>: the queryset to be exported
        <excluded_fields>: the list of fieldnames to be excluded
        <included_fields>: the list of fieldnames to be included;  'parent_field__child_field' syntax allowed

        Notes:
            - if neither <excluded_fields> not <included_fields> are supplied,
              all fields in queryset's model will be exported
            - you can't supply both <excluded_fields> and <included_fields>
        """

        fields = SpreadsheetQuerysetExporter._get_fields(
            queryset.model,
            excluded_fields,
            included_fields
        )

        # Write headers
        if self.file_format == 'csv':
            self.writer.writerow([f['name'] for f in fields])
        elif self.file_format == 'xlsx':
            self.writer.write_headers_from_fields(fields)

        # Scan queryset
        for obj in queryset.iterator():

            row = []
            # build row
            for field in fields:
                data = SpreadsheetQuerysetExporter._get_field_data(field, obj)
                row.append(data)

            self.writer.writerow(row)

    # helpers ...

    @staticmethod
    def _get_field_type(model, fieldname):
        if '__' in fieldname:
            parent_fieldname, child_fieldname = fieldname.split('__', 1)
            child_model = model._meta.get_field(parent_fieldname).related_model
            ftype = SpreadsheetQuerysetExporter._get_field_type(child_model, child_fieldname)
        else:
            f = model._meta.get_field(fieldname)
            ftype = f.__class__.__name__
        return ftype

    @staticmethod
    def _get_fields(model, excluded_fields=[], included_fields=[]):
        if excluded_fields and included_fields:
            raise Exception('Either specify "excluded_fields" or "included_fields"')
        if included_fields:
            fieldnames = included_fields
        else:
            fieldnames = [
                f.name for f in model._meta.fields
                if not(excluded_fields) or (f.name not in excluded_fields)
            ]

        fields = [{
                'name': fieldname,
                'type': SpreadsheetQuerysetExporter._get_field_type(model, fieldname),
            } for fieldname in fieldnames]

        return fields

    @staticmethod
    def _get_field_data(field, obj):

        fname = field['name']
        if '__' in fname:
            parent_fieldname, child_fieldname = fname.split('__', 1)
            if not hasattr(obj, parent_fieldname):
                raise Exception('Model object has no attribute "{0}"'.format(parent_fieldname))
            child_obj = getattr(obj, parent_fieldname, None)
            child_field = {'name': child_fieldname, 'type': field['type']}
            data = SpreadsheetQuerysetExporter._get_field_data(child_field, child_obj)
        else:

            fdisplay = 'get_%s_display' % fname
            if hasattr(obj, fdisplay):
                data = getattr(obj, fdisplay)()
            else:
                data = getattr(obj, fname, None)
                ftype = field['type']
                if ftype == 'DateTimeField':
                    data = fix_datetime(data)
                elif ftype in ['UUIDField', 'ForeignKey', ]:
                    data = str(data) if data is not None else ''

        return data

    # def _retrieve_and_normalize_latest_by(model):
    #     latest_by = getattr(model._meta, 'get_latest_by', None)
    #     if isinstance(latest_by, (list, tuple)):
    #         latest_by = latest_by[0] if len(latest_by) > 0 else ''
    #     if latest_by:
    #         if latest_by.startswith('-'):
    #             latest_by = latest_by[1:]
    #     return latest_by
