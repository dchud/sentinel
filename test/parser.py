# $Id: parser.py 237 2005-09-21 22:21:40Z dlc33 $

from unittest import TestCase

from canary.context import Context
from canary.loader import Parser

class ParserTests (TestCase):

    def setUp (self):
        self.context = Context()
        self.source_catalog = self.context.get_source_catalog()

    def test_pubmed_5 (self):
        source = self.source_catalog.get_source_by_name('pubmed-medline')
        mapped_terms = self.source_catalog.get_mapped_terms(source_id=source.uid)
        parser = Parser(source)

        # parse 5 records from disk
        records = parser.parse(file_name='test/data/pubmed_5',
            mapped_terms=mapped_terms, is_email=False)

        # make sure we have 5
        self.assertTrue("got 5 records", len(records) == 5)

        # check the title
        metadata = records[0].get_mapped_metadata(mapped_terms)
        self.assertTrue("title", metadata['title'] == 
            "ERGDB: Estrogen Responsive Genes Database.")

        # check multivalued author
        self.assertTrue("authors", metadata['author'] == 
            ['Tang S', 'Han H', 'Bajic VB'])

