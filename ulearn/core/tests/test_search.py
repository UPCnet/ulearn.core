# -*- coding: utf-8 -*-
import unittest2 as unittest
from plone import api
from AccessControl import Unauthorized
from zope.event import notify
from zope.component import getMultiAdapter
from zope.lifecycleevent import ObjectModifiedEvent
from zope.component import getUtility

from plone.app.testing import login
from plone.app.testing import logout
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID

from plone.dexterity.utils import createContentInContainer

from Products.CMFCore.utils import getToolByName

from repoze.catalog.query import Eq
from souper.soup import get_soup

from genweb.core.utils import reset_user_catalog
from genweb.core.utils import add_user_to_catalog

from ulearn.core.browser.searchuser import searchUsersFunction
from ulearn.core.testing import ULEARN_CORE_INTEGRATION_TESTING
from mrs.max.utilities import IMAXClient

import json

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

    def create_default_test_users(self):
        for suffix in range(1, 15):
            api.user.create(email='test@upcnet.es', username='victor.fernandez.' + unicode(suffix),
                            properties=dict(fullname=u'Víctor' + unicode(suffix),
                                            location=u'Barcelona',
                                            ubicacio=u'NX',
                                            telefon=u'44002, 54390'))

    def delete_default_test_users(self):
        for suffix in range(1, 15):
            api.user.delete(username='victor.fernandez.' + unicode(suffix))

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

    def test_user_search_ajax(self):
        """
            cas 1: Primer caràcter (només 1) is_useless_request == False too_much_results ? searching_surname == False
            cas 2.1: Segona lletra en endavant i not searching_surname i is_useless_request i too_much_results ==> soup
            cas 2.1: Segona lletra en endavant i not searching_surname i is_useless_request i not too_much_results ==> MAX
            cas 2.2: Segona lletra en endavant i not searching_surname i not is_useless_request ==> Seguim filtrant query soup
            cas 3: Segona lletra  en endavant i searching_surname i not is_useless_request ==> soup
            cas 3: Segona lletra  en endavant i searching_surname i is_useless_request ==> MAX

            First request, no additional last_query nor last_query_count
            Create a bunch of users into the system, but clearing the catalog
            Only one remains
        """
        self.create_default_test_users()
        reset_user_catalog()
        add_user_to_catalog(u'victor.fernandez', dict(fullname=u'Víctor'))

        login(self.portal, u'ulearn.testuser1')

        search_view = getMultiAdapter((self.portal, self.request), name='omega13usersearch')
        self.request.form = dict(q='v')
        result = search_view.render()
        result = json.loads(result)
        self.assertEqual(result['last_query_count'], 1)
        self.assertEqual(result['last_query'], 'v')

        # Force the search to be useless to force a MAX update
        self.request.form = dict(q='victor.fer', last_query='v', last_query_count=1)
        result = search_view.render()
        result = json.loads(result)

        self.assertEqual(result['last_query_count'], 15)
        self.assertEqual(result['last_query'], 'victor.fer')

        soup = get_soup('user_properties', self.portal)
        self.assertEqual(len([r for r in soup.query(Eq('username', 'victor fer*'))]), 15)

        logout()

        login(self.portal, 'admin')
        self.delete_default_test_users()
        logout()
