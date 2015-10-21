# -*- coding: utf-8 -*-
from five import grok
from zope.component import getAdapter
from zope.component import getAdapters

from Products.CMFPlone.interfaces import IPloneSiteRoot
from plone import api

from ulearn.core.api import ApiResponse
from ulearn.core.api import BadParameters
from ulearn.core.api import ObjectNotFound
from ulearn.core.api import REST
from ulearn.core.api import api_resource
from ulearn.core.api import logger
from ulearn.core.api.root import APIRoot
from ulearn.core.content.community import ICommunityACL
from ulearn.core.content.community import ICommunityTyped

from repoze.catalog.query import Eq
from souper.soup import get_soup


class CommunityMixin(object):
    def lookup_community(self):
        pc = api.portal.get_tool(name='portal_catalog')
        result = pc.searchResults(community_hash=self.params['community'])

        if not result:
            # Fallback search by gwuuid
            result = pc.searchResults(gwuuid=self.params['community'])

            if not result:
                # Not found either by hash nor by gwuuid
                error_message = 'Community with has {} not found.'.format(self.params['community'])
                logger.error(error_message)
                raise ObjectNotFound(error_message)

        self.community = result[0].getObject()
        return True


class Communities(REST):
    """
        /api/communities
    """

    placeholder_type = 'community'
    placeholder_id = 'community'

    grok.adapts(APIRoot, IPloneSiteRoot)
    grok.require('genweb.authenticated')

    @api_resource()
    def GET(self):
        """ Returns all the user communities and the open ones. """

        # Hard security validation as the view is soft checked
        check_permission = self.check_roles(roles=['Member', 'Manager'])
        if check_permission is not True:
            return check_permission

        # Get all communities for the current user
        pc = api.portal.get_tool('portal_catalog')
        r_results = pc.searchResults(portal_type='ulearn.community', community_type=[u'Closed', u'Organizative'])
        ur_results = pc.unrestrictedSearchResults(portal_type='ulearn.community', community_type=u'Open')
        communities = r_results + ur_results

        self.is_role_manager = False
        self.username = api.user.get_current().id
        global_roles = api.user.get_roles()
        if 'Manager' in global_roles:
            self.is_role_manager = True

        result = []
        favorites = self.get_favorites()
        for brain in communities:
            community = dict(id=brain.id,
                             title=brain.Title,
                             description=brain.Description,
                             url=brain.getURL(),
                             gwuuid=brain.gwuuid,
                             type=brain.community_type,
                             image=brain.image_filename if brain.image_filename else False,
                             favorited=brain.id in favorites,
                             can_manage=self.is_community_manager(brain))
            result.append(community)

        return ApiResponse(result)

    def get_favorites(self):
        pc = api.portal.get_tool('portal_catalog')

        results = pc.unrestrictedSearchResults(favoritedBy=self.username)
        return [favorites.id for favorites in results]

    def is_community_manager(self, community):
        # The user has role Manager
        if self.is_role_manager:
            return True

        gwuuid = community.gwuuid
        portal = api.portal.get()
        soup = get_soup('communities_acl', portal)

        records = [r for r in soup.query(Eq('gwuuid', gwuuid))]
        if records:
            return self.username in [a['id'] for a in records[0].attrs['acl']['users'] if a['role'] == u'owner']


class Community(REST, CommunityMixin):
    """
        /api/communities/{community}
    """

    grok.adapts(Communities, IPloneSiteRoot)
    grok.require('genweb.authenticated')

    def __init__(self, context, request):
        super(Community, self).__init__(context, request)

    @api_resource(required=['community_type'])
    def PUT(self):
        """ Modifies the community itself. """
        # Check if there's a valid community with the requested hash
        lookedup_obj = self.lookup_community()
        if lookedup_obj is not True:
            return lookedup_obj

        # Hard security validation as the view is soft checked
        check_permission = self.check_roles(self.community, ['Owner', 'Manager'])
        if check_permission is not True:
            return check_permission

        if 'community_type' in self.payload:
            # We are changing the type of the community
            # Check if it's a legit change
            if self.params['community_type'] in [a[0] for a in getAdapters((self.community,), ICommunityTyped)]:
                adapter = getAdapter(self.community, ICommunityTyped, name=self.params['community_type'])
            else:
                raise BadParameters('Bad request, wrong community type')

            if self.params['community_type'] == self.community.community_type:
                raise BadParameters('Bad request, already that community type')

            # Everything is ok, proceed
            adapter.update_community_type()

        success_response = 'Updated community "{}"'.format(self.community.absolute_url())
        logger.info(success_response)
        return ApiResponse.from_string(success_response)

    @api_resource()
    def DELETE(self):
        # Check if there's a valid community with the requested hash
        lookedup_obj = self.lookup_community()
        if lookedup_obj is not True:
            return lookedup_obj

        # Hard security validation as the view is soft checked
        check_permission = self.check_roles(self.community, ['Owner', 'Manager'])
        if check_permission is not True:
            return check_permission

        api.content.delete(obj=self.community)

        return ApiResponse({}, code=204)


class Subscriptions(REST, CommunityMixin):
    """
        /api/communities/{community}/subscriptions

        Manages the community subscriptions (ACL) for a given list of
        users/groups in the form:

        {'users': [{'id': 'user1', 'displayName': 'Display name', role: 'owner'}],
         'groups': [{'id': 'group1', 'displayName': 'Display name', role: 'writer'}]}

        At this time of writting (Feb2015), there are only three roles available
        and each other exclusive: owner, writer, reader.
    """

    grok.adapts(Community, IPloneSiteRoot)
    grok.require('genweb.authenticated')

    @api_resource()
    def GET(self):
        """
            Get the subscriptions for the community. The security is given an
            initial soft check for authenticated users at the view level and
            then by checking explicitly if the requester user has permission on
            the target community.
        """
        # Lookup for object
        lookedup_obj = self.lookup_community()
        if lookedup_obj is not True:
            return lookedup_obj

        # Hard security validation as the view is soft checked
        check_permission = self.check_roles(self.community, ['Owner', 'Manager'])
        if check_permission is not True:
            return check_permission

        result = ICommunityACL(self.community)().attrs.get('acl', '')

        return ApiResponse(result)

    @api_resource()
    def POST(self):
        """
            Subscribes a bunch of users to a community the security is given an
            initial soft check for authenticated users at the view level and
            then by checking explicitly if the requester user has permission on
            the target community.
        """
        # Lookup for object
        lookedup_obj = self.lookup_community()
        if lookedup_obj is not True:
            return lookedup_obj

        # Hard security validation as the view is soft checked
        check_permission = self.check_roles(self.community, ['Owner', 'Manager'])
        if check_permission is not True:
            return check_permission

        self.update_subscriptions()

        # Response successful
        success_response = 'Updated community "{}" subscriptions'.format(self.community.absolute_url())
        logger.info(success_response)
        return ApiResponse.from_string(success_response)

    def update_subscriptions(self):
        adapter = getAdapter(self.community, ICommunityTyped, name=self.community.community_type)

        # Change the uLearn part of the community
        adapter.update_acl(self.payload)
        adapter.set_plone_permissions(self.payload)

        # Communicate the change in the community subscription to the uLearnHub
        # XXX: Until we do not have a proper Hub online
        adapter.update_hub_subscriptions()

