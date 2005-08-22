from unittest import TestCase, makeSuite
from canary.context import Context
from canary.report import CuratorActivity
from elementtree.ElementTree import Element, tostring

class ReportTests(TestCase):

    def setUp(self):
        self.context = Context()

    def testContext(self):
        self.assertTrue(isinstance(self.context,Context))

    def testCuratorActivity(self):
        r = CuratorActivity(self.context)
        self.assertTrue(isinstance(r,CuratorActivity))
        self.assertTrue(r.table != None)
        self.assertTrue(len(r.text()) > 0 )
        self.assertTrue("<tr>" in r.html())

def suite():
    return makeSuite( ReportTests, 'test' )
