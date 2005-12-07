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


class PubmedMedlineTests (ParserTests):

    def __init__ (self, name):
        ParserTests.__init__(self, name, 'pubmed-medline')

    def test_length (self):
        records = self.parse('test/data/pubmed-medline-5.txt')
        self.assertTrue(len(records) == 5)

    def test_single_value (self):
        records = self.parse('test/data/pubmed-medline-5.txt')
        metadata = self.get_mapped_metadata(records[0])
        self.assertTrue(metadata['title'] == \
            "ERGDB: Estrogen Responsive Genes Database.")

    def test_multi_value (self):
        records = self.parse('test/data/pubmed-medline-5.txt')
        metadata = self.get_mapped_metadata(records[0])
        self.assertTrue(metadata['author'] == ['Tang S', 'Han H', 'Bajic VB'])


class OvidMedlineTests (ParserTests):

    def __init__ (self, name):
        ParserTests.__init__(self, name, 'ovid-medline')

    def test_length (self):
        records = self.parse('test/data/ovid-medline-200.txt')
        self.assertTrue(len(records) == 200)

    def test_single_value (self):
        records = self.parse('test/data/ovid-medline-200.txt')
        metadata = self.get_mapped_metadata(records[199])
        self.assertTrue(metadata['source'] == 
            'Clin Infect Dis. 2001 Feb 1;32(3):446-56')

    def test_multi_value (self):
        records = self.parse('test/data/ovid-medline-200.txt')
        metadata = self.get_mapped_metadata(records[199])
        self.assertTrue(len(metadata['author']) == 2)
        self.assertTrue(metadata['author'] == ['Weber DJ', 'Rutala WA'])


class OvidCabAbstractsTests (ParserTests):
    
    def __init__ (self, name):
        ParserTests.__init__(self, name, 'ovid-cababstracts')

    def test_length (self):
        records = self.parse('test/data/ovid-cababstracts-1.txt')
        self.assertTrue(len(records) == 1)
        
    def test_length20 (self):
        records = self.parse('test/data/ovid-cababstracts-20.txt')
        self.assertTrue(len(records) == 20)

    def test_length99 (self):
        records = self.parse('test/data/ovid-cababstracts-99.txt')
        self.assertTrue(len(records) == 99)

    def test_single_value (self):
        records = self.parse('test/data/ovid-cababstracts-99.txt')
        metadata = self.get_mapped_metadata(records[98])
        self.assertTrue(metadata['pubdate'] == '1972',
            'metadata[pubdate] == %s' % metadata['pubdate'])

    def test_multi_value (self):
        records = self.parse('test/data/ovid-cababstracts-20.txt')
        metadata = self.get_mapped_metadata(records[19])
        self.assertTrue(len(metadata['subject']) == 13,
            'len(metadata[subject]) == %s' % len(metadata['subject']))
        self.assertTrue(metadata['author'] == ['Moscona, A.'],
            'metadata[author] == %s' %metadata['author'])


class OvidBiosisTests (ParserTests):

    def __init__ (self, name):
        ParserTests.__init__(self, name, 'ovid-biosis')

    def test_length (self):
        records = self.parse('test/data/ovid-biosis-200.txt')
        self.assertTrue(len(records) == 200)

    def test_length20 (self):
        records = self.parse('test/data/ovid-biosis-20.txt')
        self.assertTrue(len(records) == 20)

    def test_single_value (self):
        records = self.parse('test/data/ovid-biosis-200.txt')
        metadata = self.get_mapped_metadata(records[110])
        self.assertTrue(metadata['title'] == 
            'PCR Strategy for Identification and Differentiation of ' + 
            'Smallpox and Other orthopoxviruses')

    def test_multi_value (self):
        records = self.parse('test/data/ovid-biosis-200.txt')
        metadata = self.get_mapped_metadata(records[110])
        self.assertTrue(len(metadata['author']) == 5)
        self.assertTrue(metadata['author'] == [ \
            'Ropp, Susan L. [Author]', 
            'Jin, Qi [Author]', 
            'Knight, Janice C. [Author]', 
            'Massung, Robert F. [Author]', 
            'Esposito, Joseph J. [Reprint author]' ])
