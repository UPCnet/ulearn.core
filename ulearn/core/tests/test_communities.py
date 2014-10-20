import unittest2 as unittest
from AccessControl import Unauthorized
from zope.event import notify
from zope.lifecycleevent import ObjectAddedEvent
from zope.lifecycleevent import ObjectModifiedEvent
from zope.component import getUtility
from zope.component import getMultiAdapter

from plone.app.testing import login
from plone.app.testing import logout
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID

from Products.CMFCore.utils import getToolByName

from mrs.max.utilities import IMAXClient
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
        self.maxclient.contexts['http://nohost/plone/community-test2'].delete()
        self.maxclient.contexts['http://nohost/plone/community-test-open'].delete()
        self.maxclient.contexts['http://nohost/plone/community-test-notify'].delete()

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

    def test_community_creation(self):
        nom = u'community-test'
        description = 'Blabla'
        subscribed = [u'usuari.iescude']
        image = None
        community_type = 'Closed'
        twitter_hashtag = 'helou'

        login(self.portal, 'usuari.iescude')

        self.portal.invokeFactory('ulearn.community', 'community-test',
                                 title=nom,
                                 description=description,
                                 subscribed=subscribed,
                                 image=image,
                                 community_type=community_type,
                                 twitter_hashtag=twitter_hashtag)

        new_comunitat = self.portal['community-test']

        logout()

        self.assertEquals(new_comunitat.objectIds(), ['documents', 'links', 'media', 'events', 'discussion'])

    def test_community_creation_not_allowed(self):
        nom = u'community-test'
        description = 'Blabla'
        subscribed = [u'usuari.iescude']
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
        subscribed = [u'usuari.iescude']
        image = None
        community_type = 'Closed'
        twitter_hashtag = 'helou'

        login(self.portal, 'usuari.iescude')

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
        subscribed = [u'usuari.iescude']
        image = None
        community_type = 'Open'
        twitter_hashtag = 'helou'

        login(self.portal, 'usuari.iescude')

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
        subscribed = [u'usuari.iescude']
        image = None
        community_type = 'Open'
        twitter_hashtag = 'helou'

        login(self.portal, 'usuari.iescude')

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

        login(self.portal, 'usuari.iescude')

        new_comunitat.community_type = 'Closed'
        notify(ObjectModifiedEvent(new_comunitat))

        logout()

        login(self.portal, 'user')

        self.assertFalse(pc.searchResults(portal_type='Event'))
        self.assertRaises(Unauthorized, self.portal.restrictedTraverse, 'community-test/events/test-event')

    def test_newcommunities_getters_setters(self):
        readers = [u'victor.fernandez']
        subscribed = [u'janet.dura']
        community = self.create_test_community(id='community-test2', readers=readers, subscribed=subscribed)

        max_subs = self.get_max_subscribed_users(community)

        self.assertTrue(readers[0] in max_subs)
        self.assertTrue(subscribed[0] in max_subs)
        self.assertTrue(u'usuari.iescude' in max_subs)

        self.assertEqual(readers, community.readers)
        self.assertEqual(subscribed, community.subscribed)
        self.assertEqual([u'usuari.iescude'], community.owners)

    def test_newcommunities_getters_setters_modify_subscriptions(self):
        readers = [u'victor.fernandez']
        subscribed = [u'janet.dura']
        community = self.create_test_community(id='community-test3', readers=readers, subscribed=subscribed)

        max_subs = self.get_max_subscribed_users(community)

        self.assertTrue(readers[0] in max_subs)
        self.assertTrue(subscribed[0] in max_subs)
        self.assertTrue(u'usuari.iescude' in max_subs)

        self.assertEqual(readers, community.readers)
        self.assertEqual(subscribed, community.subscribed)
        self.assertEqual([u'usuari.iescude'], community.owners)

        readers_state2 = [u'victor.fernandez', u'janet.dura']
        subscribed_state2 = []

        community.readers = readers_state2
        community.subscribed = subscribed_state2

        max_subs_state2 = self.get_max_subscribed_users(community)

        self.assertTrue(readers_state2[0] in max_subs_state2)
        self.assertTrue(readers_state2[1] in max_subs_state2)
        self.assertTrue(u'usuari.iescude' in max_subs_state2)

        readers_state3 = []
        subscribed_state3 = []

        community.readers = readers_state3
        community.subscribed = subscribed_state3

        max_subs_state3 = self.get_max_subscribed_users(community)

        self.assertEqual([u'usuari.iescude'], max_subs_state3)
        self.assertEqual(readers_state3, community.readers)
        self.assertEqual(subscribed_state3, community.subscribed)

    def test_newcommunities_getters_setters_corner1(self):
        owners = [u'usuari.iescude']
        community = self.create_test_community(id='community-test4', owners=owners)

        max_subs = self.get_max_subscribed_users(community)

        self.assertTrue(u'usuari.iescude' in max_subs)

        self.assertEqual([u'usuari.iescude'], community.owners)

    def test_open_community_join_getters_setters(self):
        subscribed = [u'janet.dura']
        community = self.create_test_community(id='community-test-open', community_type='Open', subscribed=subscribed)

        login(self.portal, 'victor.fernandez')

        toggle_subscribe = getMultiAdapter((community, self.request), name='toggle-subscribe')
        toggle_subscribe.render()

        max_subs = self.get_max_subscribed_users(community)
        self.assertTrue(u'victor.fernandez' in max_subs)

        toggle_subscribe.render()

        max_subs = self.get_max_subscribed_users(community)
        self.assertTrue(u'victor.fernandez' not in max_subs)

        logout()

    def test_notify_posts_comments(self):
        subscribed = [u'janet.dura']
        community = self.create_test_community(id='community-test-notify', community_type='Open', subscribed=subscribed)

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
