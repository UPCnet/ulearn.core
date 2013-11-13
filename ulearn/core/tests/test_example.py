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
        self.qi_tool = getToolByName(self.portal, 'portal_quickinstaller')

    def test_product_is_installed(self):
        """ Validate that our products GS profile has been run and the product
            installed
        """
        pid = 'ulearn.core'
        installed = [p['id'] for p in self.qi_tool.listInstalledProducts()]
        self.assertTrue(pid in installed,
                        'package appears not to have been installed')

    def test_permissions_on_homepage_and_frontpage(self):
        self.assertTrue(self.portal['front-page'].get_local_roles()[0][0], 'AuthenticatedUsers')
        self.assertTrue(self.portal.get_local_roles()[0][0], 'AuthenticatedUsers')

    def test_community_creation(self):
        # httpretty.enable()
        # httpretty.register_uri(
        #     httpretty.GET,
        #     re.compile("https://max.upc.edu/.*"),
        #     body='{"success": false}',
        #     status=200,
        #     content_type='text/json',
        # )
        # httpretty.register_uri(
        #     httpretty.PUT,
        #     re.compile("https://max.upc.edu/.*"),
        #     body='{"success": false}',
        #     status=200,
        #     content_type='text/json',
        # )
        # httpretty.register_uri(
        #     httpretty.POST,
        #     re.compile("https://max.upc.edu/.*"),
        #     body='{"success": false}',
        #     status=200,
        #     content_type='text/json',
        # )

        nom = u'community-test'
        description = 'Blabla'
        subscribed = []
        image = None
        community_type = 'Closed'
        twitter_hashtag = 'helou'

        login(self.portal, 'poweruser')

        self.portal.invokeFactory('ulearn.community', 'community-test',
                                 title=nom,
                                 description=description,
                                 subscribed=subscribed,
                                 image=image,
                                 community_type=community_type,
                                 twitter_hashtag=twitter_hashtag)

        new_comunitat = self.portal['community-test']

        logout()

        self.assertTrue(new_comunitat.objectIds(), ['documents', 'links', 'media', 'events'])
        # httpretty.disable()
        # httpretty.reset()

    def test_community_creation_not_allowed(self):
        nom = u'community-test'
        description = 'Blabla'
        subscribed = []
        image = None
        community_type = 'Closed'
        twitter_hashtag = 'helou'

        login(self.portal, 'user')

        self.assertRaises(Unauthorized, self.portal.invokeFactory,
                          'ulearn.community', 'community-test',
                          title=nom,
                          description=description,
                          subscribed=subscribed,
                          image=image,
                          community_type=community_type,
                          twitter_hashtag=twitter_hashtag)

    def test_events_visibility(self):
        nom = u'community-test'
        description = 'Blabla'
        subscribed = []
        image = None
        community_type = 'Closed'
        twitter_hashtag = 'helou'

        login(self.portal, 'poweruser')

        self.portal.invokeFactory('ulearn.community', 'community-test',
                                 title=nom,
                                 description=description,
                                 subscribed=subscribed,
                                 image=image,
                                 community_type=community_type,
                                 twitter_hashtag=twitter_hashtag)

        new_comunitat = self.portal['community-test']

        new_comunitat['events'].invokeFactory('Event', 'test-event', title="Da event")
        logout()

        login(self.portal, 'user')

        pc = getToolByName(self.portal, 'portal_catalog')

        self.assertFalse(pc.searchResults(portal_type='Event'))
        self.assertRaises(Unauthorized, self.portal.restrictedTraverse, 'community-test/events/test-event')

    def test_events_visibility_open_communities(self):
        nom = u'community-test'
        description = 'Blabla'
        subscribed = []
        image = None
        community_type = 'Open'
        twitter_hashtag = 'helou'

        login(self.portal, 'poweruser')

        self.portal.invokeFactory('ulearn.community', 'community-test',
                                 title=nom,
                                 description=description,
                                 subscribed=subscribed,
                                 image=image,
                                 community_type=community_type,
                                 twitter_hashtag=twitter_hashtag)

        new_comunitat = self.portal['community-test']

        new_comunitat['events'].invokeFactory('Event', 'test-event', title="Da event")
        logout()

        login(self.portal, 'user')

        pc = getToolByName(self.portal, 'portal_catalog')

        self.assertEquals(len(pc.searchResults(portal_type='Event')), 1)

    def test_events_visibility_open_communities_switch_to_closed(self):
        nom = u'community-test'
        description = 'Blabla'
        subscribed = []
        image = None
        community_type = 'Open'
        twitter_hashtag = 'helou'

        login(self.portal, 'poweruser')

        self.portal.invokeFactory('ulearn.community', 'community-test',
                                 title=nom,
                                 description=description,
                                 subscribed=subscribed,
                                 image=image,
                                 community_type=community_type,
                                 twitter_hashtag=twitter_hashtag)

        new_comunitat = self.portal['community-test']

        new_comunitat['events'].invokeFactory('Event', 'test-event', title="Da event")
        logout()

        login(self.portal, 'user')

        pc = getToolByName(self.portal, 'portal_catalog')

        self.assertEquals(len(pc.searchResults(portal_type='Event')), 1)

        logout()

        login(self.portal, 'poweruser')

        new_comunitat.community_type = 'Closed'
        notify(ObjectModifiedEvent(new_comunitat))

        logout()

        login(self.portal, 'user')

        self.assertFalse(pc.searchResults(portal_type='Event'))
        self.assertRaises(Unauthorized, self.portal.restrictedTraverse, 'community-test/events/test-event')
