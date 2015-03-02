# -*- coding: utf-8 -*-
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

from ulearn.core.content.community import ICommunityACL
from ulearn.core.testing import ULEARN_CORE_FUNCTIONAL_TESTING

import json
import requests
import transaction


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
        """ Creates the community, it assumes the current logged in user """
        if api.user.is_anonymous():
            self.assertTrue(False, msg='Tried to create a community but no user logged in.')

        if 'WebMaster' not in api.user.get_roles():
            self.assertTrue(False, msg='Tried to create a community but the user has not enough permissions to do so.')

        self.portal.invokeFactory('ulearn.community', id,
                                  title=name,
                                  community_type=community_type,)

        return self.portal[id]

    def max_headers(self, username):
        token = api.user.get(username).getProperty('oauth_token')
        return {'X-Oauth-Username': username,
                'X-Oauth-Token': token,
                'X-Oauth-Scope': 'widgetcli'}

    def test_community_subscribe_post(self):
        username = 'ulearn.testuser1'
        login(self.portal, username)
        portal_url = self.portal.absolute_url()
        community = self.create_test_community()
        # Needed for the 'external' request with requests
        transaction.commit()
        gwuuid = IGWUUID(community)
        url = portal_url + '/api/communities/{}/subscriptions'.format(gwuuid)
        acl = dict(users=[dict(id=u'janet.dura', displayName=u'Janet Durà', role=u'writer'),
                          dict(id=u'victor.fernandez', displayName=u'Víctor Fernández de Alba', role=u'reader')],
                   groups=[dict(id=u'PAS', displayName=u'PAS UPC', role=u'writer'),
                           dict(id=u'UPCnet', displayName=u'UPCnet', role=u'reader')]
                   )
        resp = requests.post(url, data=json.dumps(acl), headers=self.max_headers(username))

        self.assertEqual(resp.status_code, 200)
        transaction.commit()
        self.assertEqual(ICommunityACL(community).attrs['acl'], acl)
        self.assertEqual(ICommunityACL(community).attrs['groups'], ['PAS', 'UPCnet'])
        logout()

        # Not allowed to change ACL
        username_not_allowed = 'ulearn.testuser2'
        resp = requests.post(url, data=json.dumps(acl), headers=self.max_headers(username_not_allowed))
        self.assertEqual(resp.status_code, 404)

        # Subscribed to community but not Owner
        acl = dict(users=[dict(id=username_not_allowed, displayName=u'Test', role=u'writer'),
                          dict(id=u'victor.fernandez', displayName=u'Víctor Fernández de Alba', role=u'reader')],
                   groups=[dict(id=u'PAS', displayName=u'PAS UPC', role=u'writer'),
                           dict(id=u'UPCnet', displayName=u'UPCnet', role=u'reader')]
                   )
        resp = requests.post(url, data=json.dumps(acl), headers=self.max_headers(username))
        transaction.commit()

        resp = requests.post(url, data=json.dumps(acl), headers=self.max_headers(username_not_allowed))
        self.assertEqual(resp.status_code, 401)

    def test_community_subscribe_get(self):
        username = 'ulearn.testuser1'
        login(self.portal, username)
        portal_url = self.portal.absolute_url()
        community = self.create_test_community()

        transaction.commit()
        gwuuid = IGWUUID(community)
        url = portal_url + '/api/communities/{}/subscriptions'.format(gwuuid)

        resp = requests.get(url, headers=self.max_headers(username))

        self.assertEqual(ICommunityACL(community).attrs['acl'], {'users': [{'role': 'owner', 'id': u'ulearn.testuser1'}]})
