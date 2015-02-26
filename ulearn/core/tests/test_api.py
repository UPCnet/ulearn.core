import unittest2 as unittest
from hashlib import sha1
from plone import api
from zope.component import getUtility
from plone.testing.z2 import Browser
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from plone.app.testing import login
from plone.app.testing import logout

from mrs.max.utilities import IMAXClient
from genweb.core.gwuuid import IGWUUID
from ulearn.core.browser.helpers import POST
from ulearn.core.testing import ULEARN_CORE_FUNCTIONAL_TESTING
from ulearn.core.testing import ULEARN_CORE_INTEGRATION_TESTING

import requests


class TestAPI(unittest.TestCase):

    layer = ULEARN_CORE_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer['app']
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        # self.browser = Browser(self.app)

        self.maxclient, settings = getUtility(IMAXClient)()
        self.username = settings.max_restricted_username
        self.token = settings.max_restricted_token

        self.maxclient.setActor(settings.max_restricted_username)
        self.maxclient.setToken(settings.max_restricted_token)

    def tearDown(self):
        self.maxclient.people[u'leonard.nimoy'].delete()
        self.maxclient.contexts['http://localhost:55001/plone/community-test'].delete()

    def create_test_community(self, id='community-test', name=u'community-test', community_type='Closed'):
        """ Creates the community as ulearn.testuser1 """
        login(self.portal, 'ulearn.testuser1')

        self.portal.invokeFactory('ulearn.community', id,
                                  title=name,
                                  community_type=community_type,)
        logout()

        return self.portal[id]

    def max_headers(self, username):
        token = api.user.get(username).getProperty('oauth_token')
        return {'X-Oauth-Username': username,
                'X-Oauth-Token': token,
                'X-Oauth-Scope': 'widgetcli'}

    def test_myapi(self):
        username = 'ulearn.testuser2'
        login(self.portal, username)
        portal_url = self.portal.absolute_url()
        community = self.create_test_community()

        gwuuid = IGWUUID(community)
        url = portal_url + '/api/communities/{}/subscriptions'.format(gwuuid)
        data = ''
        resp = requests.post(url, data, headers=self.max_headers(username))
        # resp = POST(portal_url + '/communities/{}/subscriptions'.format(gwuuid), data, headers=self.max_headers(username))
        logout()
