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

from repoze.catalog.query import Eq
from souper.soup import get_soup

from genweb.core.utils import reset_user_catalog
from genweb.core.utils import add_user_to_catalog

from ulearn.core.tests import uLearnTestBase
from ulearn.core.browser.searchuser import searchUsersFunction
from ulearn.core.testing import ULEARN_CORE_INTEGRATION_TESTING
from mrs.max.utilities import IMAXClient

import json

DP_USER_PROPERTIES = ['id', 'fullname', 'email', 'company', 'area', 'department', 'function']


class TestExample(uLearnTestBase):

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

    def test_default_search(self):
        login(self.portal, u'ulearn.testuser1')
        users = searchUsersFunction(self.portal, self.request, '')
        logout()
        # self.assertTrue(len(users['content']) == 2)
        # self.assertEqual(users['content'][0]['id'], u'janet.dura')
        # Refer i repensar la cerca de tots els usuaris

        # Three users with mutable_properties
        self.assertTrue(len(users['content']) == 3)
        self.assertEqual(users['content'][0]['id'], u'janet.dura')

    def test_search_portal_with_search_string(self):
        search_string = 'janet'
        login(self.portal, u'ulearn.testuser1')
        users = searchUsersFunction(self.portal, self.request, search_string)
        logout()

        self.assertTrue(len(users['content']) == 1)
        self.assertEqual(users['content'][0]['id'], u'janet.dura')

    def test_search_portal_with_search_string_not_username(self):
        search_string = u'654321'
        login(self.portal, u'ulearn.testuser1')
        users = searchUsersFunction(self.portal, self.request, search_string)
        logout()

        self.assertTrue(len(users['content']) == 1)
        self.assertEqual(users['content'][0]['id'], u'janet.dura')

    def test_search_portal_with_search_string_unicode(self):
        search_string = u'Durà'
        login(self.portal, u'ulearn.testuser1')
        users = searchUsersFunction(self.portal, self.request, search_string)
        logout()

        self.assertTrue(len(users['content']) == 1)
        self.assertEqual(users['content'][0]['id'], u'janet.dura')

    def test_search_community(self):
        login(self.portal, u'ulearn.testuser1')
        community = self.create_test_community(id='community-testsearch', community_type='Closed')

        users = searchUsersFunction(community, self.request, '')

        self.assertTrue(len(users['content']) == 1)
        self.assertEqual(users['content'][0]['id'], u'ulearn.testuser1')

        users = searchUsersFunction(community, self.request, 'janet')

        self.assertTrue(len(users['content']) == 0)

        # community.subscribed = [u'janet.dura', u'ulearn.testuser1']

        # users = searchUsersFunction(community, self.request, '')
        # self.assertTrue(len(users['content']) == 2)

        # users = searchUsersFunction(community, self.request, 'janet')
        # self.assertTrue(len(users['content']) == 1)

        logout()

    def test_search_community_with_additional_fields(self):
        """ This is the case when a client has customized user properties """
        login(self.portal, u'ulearn.testuser1')
        community = self.create_test_community(id='community-testsearch', community_type='Closed')

        users = searchUsersFunction(community, self.request, '', user_properties=DP_USER_PROPERTIES)

        self.assertTrue(len(users['content']) == 1)
        self.assertEqual(users['content'][0]['id'], u'ulearn.testuser1')

        logout()

    def test_user_search_on_acl(self):
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

        self.assertTrue(result['last_query_count'] > 5)
        self.assertEqual(result['last_query'], 'victor.fer')

        soup = get_soup('user_properties', self.portal)
        self.assertTrue(len([r for r in soup.query(Eq('username', 'victor fer*'))]) > 5)

        # Amb un altre usuari (janet)
        add_user_to_catalog(u'janet.dura', dict(fullname=u'Janet'))
        self.request.form = dict(q='janet', last_query='', last_query_count=0)
        result = search_view.render()
        result = json.loads(result)

        self.assertEqual(result['last_query_count'], 1)
        self.assertEqual(result['results'], [{u'displayName': u'Janet', u'id': u'janet.dura'}])

        self.request.form = dict(q='janeth', last_query='janet', last_query_count=1)
        result = search_view.render()
        result = json.loads(result)
        self.assertEqual(result['last_query_count'], 0)

        self.request.form = dict(q='janeth.tosca', last_query='janeth', last_query_count=0)
        result = search_view.render()
        result = json.loads(result)

        self.assertEqual(result['last_query_count'], 1)
        self.assertEqual(result['results'], [{"displayName": "janeth.toscana", "id": "janeth.toscana"}])

        logout()

        login(self.portal, 'admin')
        self.delete_default_test_users()
        logout()

    def test_group_search_on_acl(self):
        setRoles(self.portal, u'ulearn.testuser1', ['Manager'])
        login(self.portal, u'ulearn.testuser1')
        sync_view = getMultiAdapter((self.portal, self.request), name='syncldapgroups')
        sync_view.render()
        logout()

        login(self.portal, u'ulearn.testuser2')
        search_view = getMultiAdapter((self.portal, self.request), name='omega13groupsearch')
        self.request.form = dict(q='pas')
        result = search_view.render()
        result = json.loads(result)

        self.assertTrue(len(result) > 5)
        self.assertTrue('PAS' in [r['id'] for r in result])
