import unittest2 as unittest
from hashlib import sha1

from zope.component import getUtility
from plone.testing.z2 import Browser
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from plone.app.testing import login
from plone.app.testing import logout

from Products.CMFCore.utils import getToolByName

from ulearn.core.testing import ULEARN_CORE_FUNCTIONAL_TESTING

from mrs.max.utilities import IMAXClient
from ulearn.core.testing import set_browserlayer

import plone.api
import transaction


class TestAPI(unittest.TestCase):

    layer = ULEARN_CORE_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer['app']
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.browser = Browser(self.app)
        set_browserlayer(self.request)

        self.maxclient, settings = getUtility(IMAXClient)()
        self.username = settings.max_restricted_username
        self.token = settings.max_restricted_token

        self.maxclient.setActor(settings.max_restricted_username)
        self.maxclient.setToken(settings.max_restricted_token)

    def tearDown(self):
        self.maxclient.people[u'leonard.nimoy'].delete()
        self.maxclient.contexts['http://localhost:55001/plone/community-test'].delete()

