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

from ulearn.core.tests import uLearnTestBase
from ulearn.core.content.community import ICommunityACL
from ulearn.core.testing import ULEARN_CORE_FUNCTIONAL_TESTING

import requests
import transaction


class TestAPI(uLearnTestBase):

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
        self.maxclient.contexts['http://localhost:55001/plone/community-test'].delete()

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
        resp = requests.post(url, json=acl, headers=self.max_headers(username))

        self.assertEqual(resp.status_code, 200)
        transaction.commit()
        self.assertEqual(ICommunityACL(community).attrs['acl'], acl)
        self.assertEqual(ICommunityACL(community).attrs['groups'], ['PAS', 'UPCnet'])
        logout()

        # Not allowed to change ACL
        username_not_allowed = 'ulearn.testuser2'
        resp = requests.post(url, json=acl, headers=self.max_headers(username_not_allowed))
        self.assertEqual(resp.status_code, 404)

        # Subscribed to community but not Owner
        acl = dict(users=[dict(id=username_not_allowed, displayName=u'Test', role=u'writer'),
                          dict(id=u'victor.fernandez', displayName=u'Víctor Fernández de Alba', role=u'reader')],
                   groups=[dict(id=u'PAS', displayName=u'PAS UPC', role=u'writer'),
                           dict(id=u'UPCnet', displayName=u'UPCnet', role=u'reader')]
                   )
        resp = requests.post(url, json=acl, headers=self.max_headers(username))
        transaction.commit()

        resp = requests.post(url, json=acl, headers=self.max_headers(username_not_allowed))
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
