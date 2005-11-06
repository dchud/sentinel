# $Id: parser.py 237 2005-09-21 22:21:40Z dlc33 $

"""
These are tests that exercise both parsing and the metadata mappings
for common citation formats.
"""

from unittest import TestCase

from canary.context import Context
from canary.loader import Parser

class ParserTests (TestCase):
    """A fixture for setting up common tangle of objects used during parsing.
    Hopefully this will change (or go away) as parsing is refactored.
    """

    def __init__ (self, name, source_name):
        TestCase.__init__(self, name)
        context = Context()
        source_catalog = context.get_source_catalog()
        source = source_catalog.get_source_by_name(source_name)
        self.mapped_terms = source_catalog.get_mapped_terms(source.uid)
        self.parser = Parser(source)

    def parse (self, file_name):
        return self.parser.parse(file_name, self.mapped_terms, False)

    def parse_email(self, file_name):
        return self.parser.parse(file_name, self.mapped_terms, True)

    def get_mapped_metadata(self, record):
        return record.get_mapped_metadata(self.mapped_terms)


class PubmedTests (ParserTests):

    def __init__ (self, name):
        ParserTests.__init__(self, name, 'pubmed-medline')

    def test_length (self):
        records = self.parse('test/data/pubmed5.txt')
        self.assertTrue("got 5 records", len(records) == 5)

    def test_single_value (self):
        records = self.parse('test/data/pubmed5.txt')
        metadata = self.get_mapped_metadata(records[0])
        self.assertTrue("title", metadata['title'] == 
            "ERGDB: Estrogen Responsive Genes Database.")

    def test_multi_value (self):
        records = self.parse('test/data/pubmed5.txt')
        metadata = self.get_mapped_metadata(records[0])
        self.assertTrue("authors", metadata['author'] == 
            ['Tang S', 'Han H', 'Bajic VB'])




