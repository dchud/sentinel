# $Id$

from unittest import TestCase
from canary.context import Context
from canary.search import SearchIndex, RecordSearcher, StudySearcher


class SearchTests (TestCase):

    context = Context()
    
    def test_context (self):
        self.assertEquals(isinstance(self.context,Context), True)
        
    def test_simple_search (self):
        try:
            search_index = SearchIndex(self.context)
            hits, searcher = search_index.search('test')
            for i, doc in hits:
                foo, bar = doc.get('uid'), hits.score(i)
            if searcher:
                searcher.close()
        except Exception, e:
            self.fail('Error searching: %s' % e)

    def test_report_searcher (self):
        try:
            searcher = RecordSearcher(self.context)
            records = searcher.search('connecticut')
        except Exception, e:
            self.fail('Error searching: %s' % e)

    def test_study_searcher (self):
        try:
            searcher = StudySearcher(self.context)
            studies = searcher.search('connecticut')
        except Exception, e:
            self.fail('Error searching: %s' % e)

