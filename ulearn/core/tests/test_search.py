import unittest2 as unittest
from AccessControl import Unauthorized
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent

from plone.app.testing import login
from plone.app.testing import logout
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID

from plone.dexterity.utils import createContentInContainer

from Products.CMFCore.utils import getToolByName

from ulearn.core.testing import ULEARN_CORE_INTEGRATION_TESTING

import httpretty
import re


class TestExample(unittest.TestCase):

    layer = ULEARN_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.app = self.layer['app']
        self.portal = self.layer['portal']
        self.request = self.layer['request']

    def test_search(self):
        from ulearn.core.browser.searchuser import searchUsersFunction
        search_string = 'usuari.ie'
        login(self.portal, u'usuari.iescude')
        users = searchUsersFunction(self.portal, self.request, search_string)
        logout()

        self.assertTrue(len(users['content']) == 1)
        self.assertEqual(users['content'][0]['id'], u'usuari.iescude')
