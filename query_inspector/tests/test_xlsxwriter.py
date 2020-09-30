import os
import io
import xlsxwriter
from django.test import TestCase

INPUT_FOLDER = os.path.join(os.path.dirname(__file__), 'input')
OUTPUT_FOLDER = os.path.join(os.path.dirname(__file__), 'output')


class XlsxWriterTestCase(TestCase):

    def input(self, filename):
        return os.path.join(INPUT_FOLDER, filename)

    def output(self, filename):
        if not os.path.exists(OUTPUT_FOLDER):
            os.makedirs(OUTPUT_FOLDER)
        return os.path.join(OUTPUT_FOLDER, filename)

    def test_create(self):
        workbook = xlsxwriter.Workbook(self.output('hello.xlsx'))
        worksheet = workbook.add_worksheet()
        worksheet.write('A1', 'Hello world')
        workbook.close()

    def test_create_twice(self):
        filenames = [self.output('hello_%d.xlsx') % i for i in range(2)]
        for filename in filenames:
            workbook = xlsxwriter.Workbook(filename)
            worksheet = workbook.add_worksheet()
            worksheet.write('A1', 'Hello world')
            workbook.close()

    def test_create_twice_with_buffer(self):
        filenames = [self.output('hello_%d_buffer.xlsx') % i for i in range(2)]
        for filename in filenames:

            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output)
            worksheet = workbook.add_worksheet()
            worksheet.write('A1', 'Hello world')
            workbook.close()

            with open(filename, 'wb') as file:
                output.seek(0)
                file.write(output.read())
