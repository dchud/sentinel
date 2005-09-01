# $Id$

from canary.context import Context
from elementtree.ElementTree import Element,SubElement,tostring

class Table:

    def __init__ (self):
        self.table = Element('table')

    def html (self):
        return tostring(self.table)

    def text (self):
        text = self.row_format % self.col_headers 
        for row in self.table.findall('tr'):
            cells = [cell.text for cell in row.findall('td')]
            text += self.row_format % tuple(cells)
        return text

 
class CuratorActivity(Table):

    def __init__ (self,context):
        Table.__init__(self)
        self.con = context 
        self.row_format = '%-20s %20s\n'
        self.col_headers = ('name', 'curated')
        self.run()

    def run (self):
        cursor = self.con.get_cursor()
        cursor.execute("""
            SELECT users.name, count(*)
            FROM users, studies, queued_records
            WHERE users.id = studies.curator_user_id
            AND studies.record_id = queued_records.uid
            AND queued_records.status = 2
            GROUP BY users.name
            ORDER BY users.name
           """)
        for row in cursor:
            r = SubElement(self.table, 'tr')
            SubElement(r, 'td').text = str(row[0])
            SubElement(r, 'td').text = str(row[1])


class StudyTypes (Table):

    from canary.study import Study, Methodology

    def __init__ (self, context, records):
        Table.__init__(self)
        self.con = context
        self.row_format = '%-20s %20s\n'
        self.col_headers = ('type', 'count')
        self.run(records)

    def run (self, records):
        types = {}
