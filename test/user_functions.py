# $Id$

from unittest import TestCase

from canary.context import Context
from canary import user

class UserFunctionTests (TestCase):

    context = Context()
        
    def test_userset (self):
        set = user.UserSet()
        set.user_id = 6
        set.name = 'test'
        set.save(self.context)
        loaded_set = user.UserSet(self.context, set.uid)
        self.assertEquals(loaded_set.name, set.name)
