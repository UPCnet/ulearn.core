# -*- coding: utf-8 -*-
import unittest2 as unittest
from AccessControl import Unauthorized
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent
from zope.component import getUtility

from plone.app.testing import login
from plone.app.testing import logout
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID

from plone.dexterity.utils import createContentInContainer

from Products.CMFCore.utils import getToolByName

from ulearn.core.browser.searchuser import searchUsersFunction
from ulearn.core.testing import ULEARN_CORE_INTEGRATION_TESTING
from mrs.max.utilities import IMAXClient

DP_USER_PROPERTIES = ['id', 'fullname', 'email', 'company', 'area', 'department', 'function']


class TestExample(unittest.TestCase):

    layer = ULEARN_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.app = self.layer['app']
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.maxclient, settings = getUtility(IMAXClient)()
        self.username = settings.max_restricted_username
        self.token = settings.max_restricted_token

        self.maxclient.setActor(settings.max_restricted_username)
        self.maxclient.setToken(settings.max_restricted_token)

    def tearDown(self):
        self.maxclient.contexts['http://nohost/plone/community-testsearch'].delete()

    def create_test_community(self, id='community-test', name=u'community-test', community_type='Closed', readers=[], subscribed=[], owners=[]):
        login(self.portal, 'usuari.iescude')

        self.portal.invokeFactory('ulearn.community', id,
                                 title=name,
                                 readers=readers,
                                 subscribed=subscribed,
                                 owners=owners,
                                 community_type=community_type,)
        logout()

        # transaction.commit()  # This is for not conflict with each other
        # TODO: Do the teardown properly
        return self.portal[id]

    def test_search(self):
        login(self.portal, u'usuari.iescude')
        users = searchUsersFunction(self.portal, self.request, '')
        logout()
        self.assertTrue(len(users['content']) == 2)
        self.assertEqual(users['content'][0]['id'], u'janet.dura')

    def test_search_portal_with_search_string(self):
        search_string = 'janet'
        login(self.portal, u'usuari.iescude')
        users = searchUsersFunction(self.portal, self.request, search_string)
        logout()

        self.assertTrue(len(users['content']) == 1)
        self.assertEqual(users['content'][0]['id'], u'janet.dura')

    def test_search_portal_with_search_string_not_username(self):
        search_string = u'654321'
        login(self.portal, u'usuari.iescude')
        users = searchUsersFunction(self.portal, self.request, search_string)
        logout()

        self.assertTrue(len(users['content']) == 1)
        self.assertEqual(users['content'][0]['id'], u'janet.dura')

    def test_search_portal_with_search_string_unicode(self):
        search_string = u'Durà'
        login(self.portal, u'usuari.iescude')
        users = searchUsersFunction(self.portal, self.request, search_string)
        logout()

        self.assertTrue(len(users['content']) == 1)
        self.assertEqual(users['content'][0]['id'], u'janet.dura')

    def test_search_community(self):
        subscribed = [u'janet.dura']
        community = self.create_test_community(id='community-testsearch', community_type='Closed', subscribed=subscribed)

        login(self.portal, u'usuari.iescude')
        users = searchUsersFunction(community, self.request, '')

        self.assertTrue(len(users['content']) == 1)
        self.assertEqual(users['content'][0]['id'], u'janet.dura')

        users = searchUsersFunction(community, self.request, 'ulearn')

        self.assertTrue(len(users['content']) == 0)

        community.subscribed = [u'janet.dura', u'ulearn.testuser1']

        users = searchUsersFunction(community, self.request, '')
        self.assertTrue(len(users['content']) == 2)

        users = searchUsersFunction(community, self.request, 'janet')
        self.assertTrue(len(users['content']) == 1)

        logout()

    def test_search_community_with_additional_fields(self):
        """ This is the case when a client has customized user properties """
        subscribed = [u'janet.dura']
        community = self.create_test_community(id='community-testsearch', community_type='Closed', subscribed=subscribed)

        login(self.portal, u'usuari.iescude')
        users = searchUsersFunction(community, self.request, '', user_properties=DP_USER_PROPERTIES)

        self.assertTrue(len(users['content']) == 1)
        self.assertEqual(users['content'][0]['id'], u'janet.dura')

        logout()
