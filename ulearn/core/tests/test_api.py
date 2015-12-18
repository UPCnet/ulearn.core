# -*- coding: utf-8 -*-
from plone import api
from zope.component import getUtility
from zope.component import getMultiAdapter
from zope.publisher.browser import TestRequest
from zope.component import getAdapter

from plone.app.testing import login
from plone.app.testing import logout

from mrs.max.utilities import IMAXClient
from genweb.core.gwuuid import IGWUUID

from ulearn.core.content.community import ICommunityTyped
from ulearn.core.tests import uLearnTestBase
from ulearn.core.content.community import ICommunityACL
from ulearn.core.testing import ULEARN_CORE_FUNCTIONAL_TESTING
from ulearn.core.content.community import OPEN_PERMISSIONS
from ulearn.core.content.community import CLOSED_PERMISSIONS
from ulearn.core.api import queryRESTComponent
from ulearn.core.tests.mockers import http_mock_hub_syncacl

import httpretty
import json


class TestAPI(uLearnTestBase):

    layer = ULEARN_CORE_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer['app']
        self.portal = self.layer['portal']
        self.request = self.layer['request']

        self.maxclient, self.settings = getUtility(IMAXClient)()
        self.username = self.settings.max_restricted_username
        self.token = self.settings.max_restricted_token

        self.maxclient.setActor(self.settings.max_restricted_username)
        self.maxclient.setToken(self.settings.max_restricted_token)

    def tearDown(self):
        httpretty.disable()
        httpretty.reset()

        self.maxclient.contexts['http://localhost:55001/plone/community-test'].delete()

    def request_API_endpoint(self, username, traversal, body=None):
        """ Get the API endpoint given a list with the traversal to be done. """
        fake_environ = self.max_headers(username)
        if body is not None:
            fake_environ.update(dict(BODY=json.dumps(body)))
        fake_request = TestRequest(environ=fake_environ)

        api_root = getMultiAdapter((self.portal, fake_request), name=traversal[0])
        traversal.pop(0)
        previous_view = api_root
        for name in traversal:
            partial_view = queryRESTComponent((previous_view, self.portal), (self.portal, fake_request), name=name, parent=previous_view)
            placeholder = getattr(previous_view, 'placeholder_type', None)

            if partial_view is None and placeholder is not None:
                placeholder_id = getattr(previous_view, 'placeholder_id')
                partial_view = queryRESTComponent((previous_view, self.portal), (self.portal, fake_request), name=placeholder, parent=previous_view, placeholder={placeholder_id: name})

            previous_view = partial_view

        return partial_view

    def test_people_post(self):
        username_plone = 'ulearn.testuser1'
        login(self.portal, username_plone)
        username = 'usertest'
        perfil = dict(fullname=u'Test User',
                      password=u'test123',
                      alias=u'testUser',
                      email_bqn=u'test@blanquerna.es',
                      email=u'test@email.es',
                      phone=u'96 234 02 23',
                      collectiveFaculty='PAS&&BQN||EST&&BQN',
                      degree=u'Informática',
                      description=u'Información personal y biografía',
                      office_location=u'Nexus',
                      office_phone=u'54560',
                      department=u'Sistemas y seguridad',
                      personalized_attention=u'Lunes a viernes de 8:00 a 15:00',
                      social_networks=u'www.link.com/twitter')

        people_view = self.request_API_endpoint(username_plone, ['api', 'people', username], body=perfil)
        response = people_view.POST()
        response = json.loads(response)
        self.assertEqual(response['message'], 'User {} created'.format(username))

    def test_people_delete(self):
        """ Delete the given user. """
        username_plone = 'ulearn.testuser1'
        login(self.portal, username_plone)
        username = 'ulearn.testuser2'

        user_view = self.request_API_endpoint(username, ['api', 'people', username])
        user_view.DELETE()

        self.assertIsNone(api.user.get('ulearn.testuser2'))

    def test_news_post(self):
        username_plone = 'ulearn.testuser1'
        login(self.portal, username_plone)
        newid = u'noticia-prueba'
        new = dict(title=u'Noticia de Prueba',
                   description=u'Noticia prueba test',
                   start=u'18/10/2015/09:00',
                   end=u'18/10/2015/09:00',
                   imgUrl='http://www.janquim.cat/wp-content/uploads/2012/05/LogoBlanquerna.jpg',
                   body=u'Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor. Aenean massa. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Donec quam felis, ultricies nec, pellentesque eu, pretium quis, sem. Nulla consequat massa quis enim. Donec pede justo, fringilla vel, aliquet nec, vulputate eget, arcu. In enim justo, rhoncus ut, imperdiet a, venenatis vitae, justo. Nullam dictum felis eu pede mollis pretium. Integer tincidunt. Cras dapibus.')

        new_view = self.request_API_endpoint(username_plone, ['api', 'news', newid], body=new)
        response = new_view.POST()
        response = json.loads(response)
        self.assertEqual(response['message'], 'News Item {} created'.format(newid))

    def test_community_subscribe_post(self):
        username = 'ulearn.testuser1'
        login(self.portal, username)
        community = self.create_test_community()
        gwuuid = IGWUUID(community).get()

        acl = dict(users=[dict(id=u'janet.dura', displayName=u'Janet Durà', role=u'writer'),
                          dict(id=u'victor.fernandez', displayName=u'Víctor Fernández de Alba', role=u'reader')],
                   groups=[dict(id=u'PAS', displayName=u'PAS UPC', role=u'writer'),
                           dict(id=u'UPCnet', displayName=u'UPCnet', role=u'reader')]
                   )

        subscriptions_view = self.request_API_endpoint(username, ['api', 'communities', gwuuid, 'subscriptions'], body=acl)
        httpretty.enable()
        http_mock_hub_syncacl(acl, self.settings.hub_server)
        response = subscriptions_view.POST()

        response = json.loads(response)
        self.assertEqual(subscriptions_view.request.response.getStatus(), 200)
        self.assertTrue('message' in response)
        self.assertEqual(ICommunityACL(community)().attrs['acl'], acl)
        self.assertEqual(ICommunityACL(community)().attrs['groups'], ['PAS', 'UPCnet'])
        logout()

        # Not allowed to change ACL
        username_not_allowed = 'ulearn.testuser2'
        login(self.portal, username_not_allowed)
        subscriptions_view = self.request_API_endpoint(username_not_allowed, ['api', 'communities', gwuuid, 'subscriptions'], body=acl)
        response = subscriptions_view.POST()
        response = json.loads(response)

        self.assertEqual(subscriptions_view.request.response.getStatus(), 404)
        logout()

        # Subscribed to community but not Owner
        login(self.portal, username)
        acl = dict(users=[dict(id=username_not_allowed, displayName=u'Test', role=u'writer'),
                          dict(id=u'victor.fernandez', displayName=u'Víctor Fernández de Alba', role=u'reader')],
                   groups=[dict(id=u'PAS', displayName=u'PAS UPC', role=u'writer'),
                           dict(id=u'UPCnet', displayName=u'UPCnet', role=u'reader')]
                   )
        subscriptions_view = self.request_API_endpoint(username, ['api', 'communities', gwuuid, 'subscriptions'], body=acl)
        response = subscriptions_view.POST()
        response = json.loads(response)
        logout()

        login(self.portal, username_not_allowed)
        subscriptions_view = self.request_API_endpoint(username_not_allowed, ['api', 'communities', gwuuid, 'subscriptions'], body=acl)
        response = subscriptions_view.POST()
        response = json.loads(response)

        self.assertEqual(subscriptions_view.request.response.getStatus(), 404)
        logout()

        httpretty.disable()
        httpretty.reset()

    def test_community_subscribe_get(self):
        username = 'ulearn.testuser1'
        login(self.portal, username)
        community = self.create_test_community()
        gwuuid = IGWUUID(community).get()

        subscriptions_view = self.request_API_endpoint(username, ['api', 'communities', gwuuid, 'subscriptions'])
        response = subscriptions_view.GET()
        response = json.loads(response)

        self.assertEqual(ICommunityACL(community)().attrs['acl'], {'users': [{'role': 'owner', 'id': u'ulearn.testuser1'}]})

    def test_community_put_permissions(self):
        """ Used when changing the community type. """
        username = 'ulearn.testuser1'
        login(self.portal, username)
        community = self.create_test_community()
        gwuuid = IGWUUID(community).get()

        data = dict(community_type='Open')
        community_view = self.request_API_endpoint(username, ['api', 'communities', gwuuid], body=data)
        response = community_view.PUT()
        response = json.loads(response)

        self.assertEqual(community_view.request.response.getStatus(), 200)
        self.assertEqual(community.community_type, 'Open')

        self.assertTrue('Reader' in community.get_local_roles_for_userid(userid='AuthenticatedUsers'))

        max_community_info = self.get_max_context_info(community)
        for key in OPEN_PERMISSIONS:
            self.assertEqual(max_community_info['permissions'].get(key, ''), OPEN_PERMISSIONS[key])

        # To closed again
        data = dict(community_type='Closed')
        community_view = self.request_API_endpoint(username, ['api', 'communities', gwuuid], body=data)
        response = community_view.PUT()
        response = json.loads(response)

        self.assertEqual(community_view.request.response.getStatus(), 200)
        self.assertEqual(community.community_type, 'Closed')

        self.assertTrue('Reader' not in community.get_local_roles_for_userid(userid='AuthenticatedUsers'))

        max_community_info = self.get_max_context_info(community)
        for key in CLOSED_PERMISSIONS:
            self.assertEqual(max_community_info['permissions'].get(key, ''), CLOSED_PERMISSIONS[key])

        # Try to make it again closed
        community_view = self.request_API_endpoint(username, ['api', 'communities', gwuuid], body=data)
        response = community_view.PUT()
        response = json.loads(response)

        self.assertEqual(community_view.request.response.getStatus(), 400)
        self.assertEqual(community.community_type, 'Closed')

        # Try to change it to an unknown type
        data = dict(community_type='Bullshit')
        community_view = self.request_API_endpoint(username, ['api', 'communities', gwuuid], body=data)
        response = community_view.PUT()
        response = json.loads(response)

        self.assertEqual(community_view.request.response.getStatus(), 400)
        self.assertEqual(community.community_type, 'Closed')

        # Try to change it to Organizative
        data = dict(community_type='Organizative')
        community_view = self.request_API_endpoint(username, ['api', 'communities', gwuuid], body=data)
        response = community_view.PUT()
        response = json.loads(response)

        self.assertEqual(community_view.request.response.getStatus(), 200)
        self.assertEqual(community.community_type, 'Organizative')

    def test_community_subscribe_post_user_not_found(self):
        """ Try to subscribe principals to a community which the user has no permissions at all. """
        username = 'ulearn.testuser1'
        login(self.portal, username)
        community = self.create_test_community()
        gwuuid = IGWUUID(community).get()

        acl = dict(users=[dict(id=u'janet.dura', displayName=u'Janet Durà', role=u'writer'),
                          dict(id=u'victor.fernandez', displayName=u'Víctor Fernández de Alba', role=u'reader')],
                   groups=[dict(id=u'PAS', displayName=u'PAS UPC', role=u'writer'),
                           dict(id=u'UPCnet', displayName=u'UPCnet', role=u'reader')]
                   )

        subscriptions_view = self.request_API_endpoint(username, ['api', 'communities', gwuuid, 'subscriptions'], body=acl)
        httpretty.enable()
        http_mock_hub_syncacl(acl, self.settings.hub_server)
        login(self.portal, 'ulearn.testuser2')

        response = subscriptions_view.POST()
        response = json.loads(response)
        self.assertTrue(response['status_code'] == 404)

    def test_community_subscribe_post_user_not_allowed(self):
        username = 'ulearn.testuser1'
        login(self.portal, username)
        community = self.create_test_community(community_type='Open')
        gwuuid = IGWUUID(community).get()

        acl = dict(users=[dict(id=u'janet.dura', displayName=u'Janet Durà', role=u'writer'),
                          dict(id=u'victor.fernandez', displayName=u'Víctor Fernández de Alba', role=u'reader')],
                   groups=[dict(id=u'PAS', displayName=u'PAS UPC', role=u'writer'),
                           dict(id=u'UPCnet', displayName=u'UPCnet', role=u'reader')]
                   )

        subscriptions_view = self.request_API_endpoint(username, ['api', 'communities', gwuuid, 'subscriptions'], body=acl)
        httpretty.enable()
        http_mock_hub_syncacl(acl, self.settings.hub_server)
        login(self.portal, 'ulearn.testuser2')

        response = subscriptions_view.POST()
        response = json.loads(response)

        self.assertTrue(response['status_code'] == 403)

    def test_communities_get(self):
        """ Gets all communities and its properties for the requester user. """
        username = 'ulearn.testuser1'
        login(self.portal, username)
        self.create_test_community(community_type='Open')

        communities_view = self.request_API_endpoint(username, ['api', 'communities'])
        response = communities_view.GET()
        response = json.loads(response)

        self.assertEqual(len(response), 1)
        self.assertEqual(response[0]['id'], 'community-test')
        self.assertTrue(response[0]['favorited'])
        self.assertTrue(response[0]['can_manage'])

    def test_communities_post(self):
        """ Post to add new community. """
        username = 'ulearn.testuser1'
        login(self.portal, username)
        data = {'title': 'prova1', 'community_type': 'Open'}
        community_view = self.request_API_endpoint(username, ['api', 'communities'], body=data)
        response = community_view.POST()
        response = json.loads(response)
        self.assertEqual(community_view.request.response.getStatus(), 201)
        self.assertTrue('message' in response)

    def test_communities_delete(self):
        """ Delete the given community. """
        username = 'ulearn.testuser1'
        login(self.portal, username)
        community = self.create_test_community(community_type='Open')
        gwuuid = IGWUUID(community).get()

        community_view = self.request_API_endpoint(username, ['api', 'communities', gwuuid])
        community_view.DELETE()

        self.assertTrue('community-test' not in self.portal.objectIds())

    def test_groups_get(self):
        """ Get the communities by the given group. """
        username = 'ulearn.testuser1'
        login(self.portal, username)
        community = self.create_test_community(community_type='Closed')
        gwuuid = IGWUUID(community).get()
        acl = dict(users=[dict(id=u'janet.dura', displayName=u'Janet Durà', role=u'writer'),
                          dict(id=u'victor.fernandez', displayName=u'Víctor Fernández de Alba', role=u'reader')],
                   groups=[dict(id=u'PAS', displayName=u'PAS UPC', role=u'writer'),
                           dict(id=u'UPCnet', displayName=u'UPCnet', role=u'reader')]
                   )

        adapter = getAdapter(community, ICommunityTyped, name=community.community_type)
        adapter.update_acl(acl)

        group = u'UPCnet'

        group_view = self.request_API_endpoint(username, ['api', 'groups', group, 'communities'])
        response = group_view.GET()
        response = json.loads(response)

        self.assertTrue(group in response[0]['groups'])
        self.assertTrue('janet.dura' in response[0]['users'])
        self.assertTrue('victor.fernandez' in response[0]['users'])
