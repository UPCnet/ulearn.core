# -*- coding: utf-8 -*-
import unittest2 as unittest
from hashlib import sha1
from plone import api
from AccessControl import Unauthorized
from zope.event import notify
from zope.lifecycleevent import ObjectAddedEvent
from zope.lifecycleevent import ObjectModifiedEvent
from zope.component import getUtility
from zope.component import getMultiAdapter
from zope.component import getAdapter

from plone.app.testing import login
from plone.app.testing import logout
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID

from Products.CMFCore.utils import getToolByName

from repoze.catalog.query import Eq
from souper.soup import get_soup
from souper.soup import Record

from genweb.core.gwuuid import IGWUUID

from mrs.max.utilities import IMAXClient
from ulearn.core.content.community import ICommunityTyped
from ulearn.core.testing import ULEARN_CORE_INTEGRATION_TESTING


class TestExample(unittest.TestCase):

    layer = ULEARN_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.app = self.layer['app']
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.qi_tool = getToolByName(self.portal, 'portal_quickinstaller')

        self.maxclient, settings = getUtility(IMAXClient)()
        self.username = settings.max_restricted_username
        self.token = settings.max_restricted_token

        self.maxclient.setActor(settings.max_restricted_username)
        self.maxclient.setToken(settings.max_restricted_token)

    def tearDown(self):
        self.maxclient.contexts['http://nohost/plone/community-test'].delete()
        self.maxclient.contexts['http://nohost/plone/community-test2'].delete()
        self.maxclient.contexts['http://nohost/plone/community-test-open'].delete()
        self.maxclient.contexts['http://nohost/plone/community-test-notify'].delete()

    def create_test_community(self, id='community-test', name=u'community-test', community_type='Closed', readers=[], writers=[], owners=[]):
        """ Creates the community as ulearn.testuser1 """
        login(self.portal, 'ulearn.testuser1')

        self.portal.invokeFactory('ulearn.community', id,
                                  title=name,
                                  community_type=community_type,)
        logout()

        return self.portal[id]

    def get_max_subscribed_users(self, community):
        return [user.get('username', '') for user in self.maxclient.contexts[community.absolute_url()].subscriptions.get(qs={'limit': 0})]

    def get_max_context_info(self, community):
        return self.maxclient.contexts[community.absolute_url()].get()

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

    def test_community_creation_closed(self):
        CLOSED_PERMISSIONS = dict(read='subscribed',
                                  write='restricted',
                                  subscribe='restricted',
                                  unsubscribe='public')
        nom = u'community-test'
        description = 'Blabla'
        image = None
        community_type = 'Closed'
        twitter_hashtag = 'helou'

        login(self.portal, 'ulearn.testuser1')

        self.portal.invokeFactory('ulearn.community', 'community-test',
                                 title=nom,
                                 description=description,
                                 image=image,
                                 community_type=community_type,
                                 twitter_hashtag=twitter_hashtag)

        community = self.portal['community-test']

        logout()

        # Test for the acl registry
        soup = get_soup('communities_acl', self.portal)
        # By the gwuuid
        records = [r for r in soup.query(Eq('gwuuid', IGWUUID(community)))]
        self.assertEquals(len(records), 1)
        self.assertEquals(records[0].attrs.get('gwuuid', ''), IGWUUID(community))
        self.assertEquals(records[0].attrs.get('path', ''), '/'.join(community.getPhysicalPath()))
        self.assertEquals(records[0].attrs.get('hash', ''), sha1(community.absolute_url()).hexdigest())
        self.assertEquals(records[0].attrs.get('acl', '').get('users', [])[0]['role'], u'owner')
        self.assertEquals(records[0].attrs.get('acl', '').get('users', [])[0]['id'], u'ulearn.testuser1')

        # Test for internal objects
        self.assertEquals(community.objectIds(), ['documents', 'links', 'media', 'events', 'discussion'])

        # Test for subscribed users
        self.assertTrue(u'ulearn.testuser1' in self.get_max_subscribed_users(community))

        # Test for Plone permissions/local roles
        self.assertTrue('Reader' not in community.get_local_roles_for_userid(userid='AuthenticatedUsers'))
        self.assertTrue('Editor' in community.get_local_roles_for_userid(userid='ulearn.testuser1'))
        self.assertTrue('Owner' in community.get_local_roles_for_userid(userid='ulearn.testuser1'))
        self.assertTrue('Reader' in community.get_local_roles_for_userid(userid='ulearn.testuser1'))

        # Test the initial MAX properties
        max_community_info = self.get_max_context_info(community)
        self.assertEqual('helou', max_community_info.get(u'twitterHashtag', ''))
        self.assertFalse(max_community_info.get(u'notifications', False))
        self.assertTrue(u'[COMMUNITY]' in max_community_info.get('tags', []))

        for key in max_community_info.get('permissions', []):
            self.assertEqual(max_community_info['permissions'].get(key, ''), CLOSED_PERMISSIONS[key])

    def test_community_creation_open(self):
        OPEN_PERMISSIONS = dict(read='subscribed',
                                write='subscribed',
                                subscribe='public',
                                unsubscribe='public')
        nom = u'community-test'
        description = 'Blabla'
        image = None
        community_type = 'Open'
        twitter_hashtag = 'helou'

        login(self.portal, 'ulearn.testuser1')

        self.portal.invokeFactory('ulearn.community', 'community-test',
                                 title=nom,
                                 description=description,
                                 image=image,
                                 community_type=community_type,
                                 twitter_hashtag=twitter_hashtag)

        community = self.portal['community-test']

        logout()

        # Test for the acl registry
        soup = get_soup('communities_acl', self.portal)
        # By the gwuuid
        records = [r for r in soup.query(Eq('gwuuid', IGWUUID(community)))]
        self.assertEquals(len(records), 1)
        self.assertEquals(records[0].attrs.get('gwuuid', ''), IGWUUID(community))
        self.assertEquals(records[0].attrs.get('path', ''), '/'.join(community.getPhysicalPath()))
        self.assertEquals(records[0].attrs.get('hash', ''), sha1(community.absolute_url()).hexdigest())
        self.assertEquals(records[0].attrs.get('acl', '').get('users', [])[0]['role'], u'owner')
        self.assertEquals(records[0].attrs.get('acl', '').get('users', [])[0]['id'], u'ulearn.testuser1')

        # Test for internal objects
        self.assertEquals(community.objectIds(), ['documents', 'links', 'media', 'events', 'discussion'])

        # Test for subscribed users
        self.assertTrue(u'ulearn.testuser1' in self.get_max_subscribed_users(community))

        # Test for Plone permissions/local roles
        self.assertTrue('Reader' in community.get_local_roles_for_userid(userid='AuthenticatedUsers'))
        self.assertTrue('Editor' in community.get_local_roles_for_userid(userid='ulearn.testuser1'))
        self.assertTrue('Owner' in community.get_local_roles_for_userid(userid='ulearn.testuser1'))
        self.assertTrue('Reader' in community.get_local_roles_for_userid(userid='ulearn.testuser1'))

        # Test the initial MAX properties
        max_community_info = self.get_max_context_info(community)
        self.assertEqual('helou', max_community_info.get(u'twitterHashtag', ''))
        self.assertFalse(max_community_info.get(u'notifications', False))
        self.assertTrue(u'[COMMUNITY]' in max_community_info.get('tags', []))

        for key in max_community_info.get('permissions', []):
            self.assertEqual(max_community_info['permissions'].get(key, ''), OPEN_PERMISSIONS[key])

    def test_community_creation_organizative(self):
        ORGANIZATIVE_PERMISSIONS = dict(read='subscribed',
                                        write='restricted',
                                        subscribe='restricted',
                                        unsubscribe='restricted')
        nom = u'community-test'
        description = 'Blabla'
        image = None
        community_type = 'Organizative'
        twitter_hashtag = 'helou'

        login(self.portal, 'ulearn.testuser1')

        self.portal.invokeFactory('ulearn.community', 'community-test',
                                 title=nom,
                                 description=description,
                                 image=image,
                                 community_type=community_type,
                                 twitter_hashtag=twitter_hashtag)

        community = self.portal['community-test']

        logout()

        # Test for the acl registry
        soup = get_soup('communities_acl', self.portal)
        # By the gwuuid
        records = [r for r in soup.query(Eq('gwuuid', IGWUUID(community)))]
        self.assertEquals(len(records), 1)
        self.assertEquals(records[0].attrs.get('gwuuid', ''), IGWUUID(community))
        self.assertEquals(records[0].attrs.get('path', ''), '/'.join(community.getPhysicalPath()))
        self.assertEquals(records[0].attrs.get('hash', ''), sha1(community.absolute_url()).hexdigest())
        self.assertEquals(records[0].attrs.get('acl', '').get('users', [])[0]['role'], u'owner')
        self.assertEquals(records[0].attrs.get('acl', '').get('users', [])[0]['id'], u'ulearn.testuser1')

        # Test for internal objects
        self.assertEquals(community.objectIds(), ['documents', 'links', 'media', 'events', 'discussion'])

        # Test for subscribed users
        self.assertTrue(u'ulearn.testuser1' in self.get_max_subscribed_users(community))

        # Test for Plone permissions/local roles
        self.assertTrue('Reader' not in community.get_local_roles_for_userid(userid='AuthenticatedUsers'))
        self.assertTrue('Editor' in community.get_local_roles_for_userid(userid='ulearn.testuser1'))
        self.assertTrue('Owner' in community.get_local_roles_for_userid(userid='ulearn.testuser1'))
        self.assertTrue('Reader' in community.get_local_roles_for_userid(userid='ulearn.testuser1'))

        # Test the initial MAX properties
        max_community_info = self.get_max_context_info(community)
        self.assertEqual('helou', max_community_info.get(u'twitterHashtag', ''))
        self.assertFalse(max_community_info.get(u'notifications', False))
        self.assertTrue(u'[COMMUNITY]' in max_community_info.get('tags', []))

        for key in max_community_info.get('permissions', []):
            self.assertEqual(max_community_info['permissions'].get(key, ''), ORGANIZATIVE_PERMISSIONS[key])

    def test_community_creation_not_allowed(self):
        nom = u'community-test'
        description = 'Blabla'
        image = None
        community_type = 'Closed'
        twitter_hashtag = 'helou'

        login(self.portal, 'user')

        self.assertRaises(Unauthorized, self.portal.invokeFactory,
                          'ulearn.community', 'community-test',
                          title=nom,
                          description=description,
                          image=image,
                          community_type=community_type,
                          twitter_hashtag=twitter_hashtag)
        logout()

    def test_edit_community(self):
        community = self.create_test_community()
        community.twitter_hashtag = 'Modified'
        notify(ObjectModifiedEvent(community))
        max_community_info = self.get_max_context_info(community)
        self.assertEquals('modified', max_community_info.get(u'twitterHashtag', ''))

        community.notify_activity_via_push = True
        notify(ObjectModifiedEvent(community))
        max_community_info = self.get_max_context_info(community)
        self.assertEquals('posts', max_community_info.get(u'notifications', ''))

        community.notify_activity_via_push_comments_too = True
        notify(ObjectModifiedEvent(community))
        max_community_info = self.get_max_context_info(community)
        self.assertEquals('comments', max_community_info.get(u'notifications', ''))

        community.notify_activity_via_push = False
        community.notify_activity_via_push_comments_too = False
        notify(ObjectModifiedEvent(community))
        max_community_info = self.get_max_context_info(community)
        self.assertEquals('', max_community_info.get(u'notifications', ''))

    def test_edit_acl(self):
        community = self.create_test_community()
        acl = dict(users=[dict(id=u'janet.dura', displayName=u'Janet Durà', role=u'writer'),
                          dict(id=u'victor.fernandez', displayName=u'Víctor Fernández de Alba', role=u'reader')],
                   groups=[dict(id=u'PAS', displayName=u'PAS UPC', role=u'writer'),
                           dict(id=u'UPCnet', displayName=u'UPCnet', role=u'reader')]
                   )

        adapter = getAdapter(community, ICommunityTyped, name=community.community_type)
        adapter.update_acl(acl)

        soup = get_soup('communities_acl', self.portal)
        records = [r for r in soup.query(Eq('gwuuid', IGWUUID(community)))]

        self.assertEqual(cmp(records[0].attrs['acl'], acl), 0)

    def test_events_visibility(self):
        community = self.create_test_community()

        login(self.portal, 'ulearn.testuser1')
        community['events'].invokeFactory('Event', 'test-event', title="Da event")
        logout()

        login(self.portal, 'user')

        pc = api.portal.get_tool('portal_catalog')

        self.assertFalse(pc.searchResults(portal_type='Event'))
        self.assertRaises(Unauthorized, self.portal.restrictedTraverse, 'community-test/events/test-event')

    def test_events_visibility_open_communities(self):
        community = self.create_test_community(community_type='Open')

        login(self.portal, 'ulearn.testuser1')
        community['events'].invokeFactory('Event', 'test-event', title="Da event")
        logout()

        login(self.portal, 'user')

        pc = api.portal.get_tool('portal_catalog')

        self.assertEquals(len(pc.searchResults(portal_type='Event')), 1)

    # def test_events_visibility_open_communities_switch_to_closed(self):
    #     community = self.create_test_community(community_type='Open')

    #     login(self.portal, 'ulearn.testuser1')
    #     community['events'].invokeFactory('Event', 'test-event', title="Da event")
    #     logout()

    #     login(self.portal, 'user')

    #     pc = api.portal.get_tool('portal_catalog')

    #     self.assertEquals(len(pc.searchResults(portal_type='Event')), 1)

    #     logout()

    #     login(self.portal, 'ulearn.testuser1')

    #     community.community_type = 'Closed'
    #     notify(ObjectModifiedEvent(community))

    #     logout()

    #     login(self.portal, 'user')

    #     self.assertFalse(pc.searchResults(portal_type='Event'))
    #     self.assertRaises(Unauthorized, self.portal.restrictedTraverse, 'community-test/events/test-event')

    # def test_newcommunities_getters_setters(self):
    #     readers = [u'victor.fernandez']
    #     subscribed = [u'janet.dura']
    #     community = self.create_test_community(id='community-test2', readers=readers, subscribed=subscribed)

    #     max_subs = self.get_max_subscribed_users(community)

    #     self.assertTrue(readers[0] in max_subs)
    #     self.assertTrue(subscribed[0] in max_subs)
    #     self.assertTrue(u'ulearn.testuser1' in max_subs)

    #     self.assertEqual(readers, community.readers)
    #     self.assertEqual(subscribed, community.subscribed)
    #     self.assertEqual([u'ulearn.testuser1'], community.owners)

    # def test_newcommunities_getters_setters_modify_subscriptions(self):
    #     readers = [u'victor.fernandez']
    #     subscribed = [u'janet.dura']
    #     community = self.create_test_community(id='community-test3', readers=readers, subscribed=subscribed)

    #     max_subs = self.get_max_subscribed_users(community)

    #     self.assertTrue(readers[0] in max_subs)
    #     self.assertTrue(subscribed[0] in max_subs)
    #     self.assertTrue(u'ulearn.testuser1' in max_subs)

    #     self.assertEqual(readers, community.readers)
    #     self.assertEqual(subscribed, community.subscribed)
    #     self.assertEqual([u'ulearn.testuser1'], community.owners)

    #     readers_state2 = [u'victor.fernandez', u'janet.dura']
    #     subscribed_state2 = []

    #     community.readers = readers_state2
    #     community.subscribed = subscribed_state2

    #     max_subs_state2 = self.get_max_subscribed_users(community)

    #     self.assertTrue(readers_state2[0] in max_subs_state2)
    #     self.assertTrue(readers_state2[1] in max_subs_state2)
    #     self.assertTrue(u'ulearn.testuser1' in max_subs_state2)

    #     readers_state3 = []
    #     subscribed_state3 = []

    #     community.readers = readers_state3
    #     community.subscribed = subscribed_state3

    #     max_subs_state3 = self.get_max_subscribed_users(community)

    #     self.assertEqual([u'ulearn.testuser1'], max_subs_state3)
    #     self.assertEqual(readers_state3, community.readers)
    #     self.assertEqual(subscribed_state3, community.subscribed)

    # def test_newcommunities_getters_setters_corner1(self):
    #     owners = [u'ulearn.testuser1']
    #     community = self.create_test_community(id='community-test4', owners=owners)

    #     max_subs = self.get_max_subscribed_users(community)

    #     self.assertTrue(u'ulearn.testuser1' in max_subs)

    #     self.assertEqual([u'ulearn.testuser1'], community.owners)

    # def test_open_community_join_getters_setters(self):
    #     subscribed = [u'janet.dura']
    #     community = self.create_test_community(id='community-test-open', community_type='Open', subscribed=subscribed)

    #     login(self.portal, 'victor.fernandez')

    #     toggle_subscribe = getMultiAdapter((community, self.request), name='toggle-subscribe')
    #     toggle_subscribe.render()

    #     max_subs = self.get_max_subscribed_users(community)
    #     self.assertTrue(u'victor.fernandez' in max_subs)

    #     toggle_subscribe.render()

    #     max_subs = self.get_max_subscribed_users(community)
    #     self.assertTrue(u'victor.fernandez' not in max_subs)

    #     logout()

    # def test_open_community_already_in_MAX_getters_setters(self):
    #     subscribed = [u'janet.dura']
    #     community = self.create_test_community(id='community-test-open-exist', community_type='Open', subscribed=subscribed)

    #     login(self.portal, 'victor.fernandez')

    #     toggle_subscribe = getMultiAdapter((community, self.request), name='toggle-subscribe')
    #     toggle_subscribe.render()

    #     max_subs = self.get_max_subscribed_users(community)
    #     self.assertTrue(u'victor.fernandez' in max_subs)
    #     self.assertTrue(u'janet.dura' in community.subscribed and u'victor.fernandez' in community.subscribed)
    #     self.assertTrue(u'ulearn.testuser1' in community.owners)

    #     toggle_subscribe.render()

    #     max_subs = self.get_max_subscribed_users(community)
    #     self.assertTrue(u'victor.fernandez' not in max_subs)
    #     self.assertTrue(u'janet.dura' in community.subscribed)
    #     self.assertTrue(u'ulearn.testuser1' in community.owners)

    #     logout()

    def test_notify_posts_comments(self):
        community = self.create_test_community(id='community-test-notify', community_type='Open')

        info = self.get_max_context_info(community)

        self.assertEquals(info['notifications'], False)

        community.notify_activity_via_push = True

        notify(ObjectModifiedEvent(community))

        info = self.get_max_context_info(community)
        self.assertEquals(info['notifications'], u'posts')

        community.notify_activity_via_push_comments_too = True

        notify(ObjectModifiedEvent(community))

        info = self.get_max_context_info(community)
        self.assertEquals(info['notifications'], u'comments')

    def test_community_type_adapters(self):
        community = self.create_test_community(id='community-test-notify', community_type='Closed')
        adapter = getAdapter(community, ICommunityTyped, name='Closed')
