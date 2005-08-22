from unittest import TestCase, makeSuite
from canary.context import Context
from canary.report import CuratorActivity
from elementtree.ElementTree import Element, tostring

class ReportTests(TestCase):

    def setUp(self):
        self.context = Context()

    def testContext(self):
        self.assertEquals(isinstance(self.context,Context),True)

    def testCuratorActivity(self):
        r = CuratorActivity(self.context)
        self.assertEquals(isinstance(r,CuratorActivity),True)
        self.assertNotEquals(r.table,None)
        self.assertEquals(len(r.text())>0, True)
        self.assertEquals("<tr>" in r.html(), True)

def suite():
    return makeSuite( ReportTests, 'test' )
