# $Id$

from unittest import TestCase

from canary.context import Context
from canary.resolver import find_resolver, Resolver

class ResolverTests (TestCase):

    context = Context()
    
    OCLC_GATEWAY_URL = 'http://worldcatlibraries.org/registry/gateway'
        
    def test_default (self):
        r = find_resolver(self.context, '999.9.9.9')
        self.assertEqual(self.OCLC_GATEWAY_URL, r.base_url)

    def test_default_text (self):
        r = find_resolver(self.context, '999.9.9.9')
        self.assertEqual('Find in a library', r.link_text)

    def test_simple (self):
        # curtis.med.yale.edu
        r = find_resolver(self.context, '128.36.123.51')
        self.failIfEqual(self.OCLC_GATEWAY_URL, r.base_url)

    def test_yale (self):
        # NOTE: this will fail if YUL's resolver location changes
        r = find_resolver(self.context, '128.36.123.51')
        self.assertEqual('http://sfx.library.yale.edu/sfx_local', r.base_url)

    def test_umich (self):
        # NOTE: this will fail if UMich resolver location changes
        r = find_resolver(self.context, '141.211.2.202')
        self.assertEqual('http://sfx.lib.umich.edu:9003/sfx_locater', r.base_url)
        
