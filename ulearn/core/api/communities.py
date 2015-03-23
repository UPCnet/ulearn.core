from plone import api
from five import grok
from zope.component import getUtility
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent
from zope.component import getAdapter
from zope.component import getAdapters
from Products.CMFPlone.interfaces import IPloneSiteRoot
from repoze.catalog.query import Eq
from souper.soup import get_soup
from souper.soup import Record

from mrs.max.utilities import IMAXClient

from genweb.core.gwuuid import IGWUUID
from ulearn.core.content.community import ICommunityTyped
from ulearn.core.content.community import ICommunityACL
from ulearn.core.api import REST
from ulearn.core.api import logger
from ulearn.core.api.root import APIRoot
from ulearn.core.api.security import execute_under_special_role

import json


class Communities(REST):
    """
        /api/communities
    """

    placeholder_type = 'community'
    placeholder_id = 'community'

    grok.adapts(APIRoot, IPloneSiteRoot)
    grok.require('genweb.authenticated')


class Community(REST):
    """
        /api/communities/{community}
    """

    grok.adapts(Communities, IPloneSiteRoot)
    grok.require('genweb.authenticated')

    def __init__(self, context, request):
        super(Community, self).__init__(context, request)

    def PUT(self):
        """ Modifies the community itself. """
        # Parameters validation
        validation = self.validate()
        if validation is not True:
            return validation

        # Check if there's a valid community with the requested hash
        lookedup_obj = self.lookup_community()
        if lookedup_obj is not True:
            return lookedup_obj

        # Hard security validation as the view is soft checked
        check_permission = self.check_roles(self.community, ['Owner', 'Manager'])
        if check_permission is not True:
            return check_permission

        self.data = json.loads(self.request['BODY'])

        if 'community_type' in self.data:
            # We are changing the type of the community
            # Check if it's a legit change
            if self.data['community_type'] in [a[0] for a in getAdapters((self.community,), ICommunityTyped)]:
                adapter = getAdapter(self.community, ICommunityTyped, name=self.data['community_type'])
            else:
                self.response.setStatus(400)
                return self.json_response(dict(error='Bad request, wrong community type', status_code=400))

            if self.data['community_type'] == self.community.community_type:
                self.response.setStatus(400)
                return self.json_response(dict(error='Bad request, already that community type', status_code=400))

            # Everything is ok, proceed
            adapter.update_community_type()

        self.response.setStatus(200)
        success_response = 'Updated community "{}"'.format(self.community.absolute_url())
        logger.info(success_response)
        return self.json_response(dict(message=success_response, status_code=200))


class Subscriptions(REST):
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

    def GET(self):
        """
            Get the subscriptions for the community. The security is given an
            initial soft check for authenticated users at the view level and
            then by checking explicitly if the requester user has permission on
            the target community.
        """
        # Parameters validation
        validation = self.validate()
        if validation is not True:
            return validation

        # Lookup for object
        lookedup_obj = self.lookup_community()
        if lookedup_obj is not True:
            return lookedup_obj

        # Hard security validation as the view is soft checked
        check_permission = self.check_roles(self.community, ['Owner', 'Manager'])
        if check_permission is not True:
            return check_permission

        result = ICommunityACL(self.community)().attrs.get('acl', '')

        self.response.setStatus(200)
        return self.json_response(result)

    def POST(self):
        """
            Subscribes a bunch of users to a community the security is given an
            initial soft check for authenticated users at the view level and
            then by checking explicitly if the requester user has permission on
            the target community.
        """
        # Parameters validation
        validation = self.validate()
        if validation is not True:
            return validation

        # Lookup for object
        lookedup_obj = self.lookup_community()
        if lookedup_obj is not True:
            return lookedup_obj

        # Hard security validation as the view is soft checked
        check_permission = self.check_roles(self.community, ['Owner', 'Manager'])
        if check_permission is not True:
            return check_permission

        self.data = json.loads(self.request['BODY'])

        result = self.update_subscriptions()

        self.response.setStatus(result['status_code'])
        return self.json_response(result)

    def update_subscriptions(self):
        adapter = getAdapter(self.community, ICommunityTyped, name=self.community.community_type)

        # Change the uLearn part of the community
        adapter.update_acl(self.data)
        adapter.set_plone_permissions(self.data)

        # Communicate the change in the community subscription to the uLearnHub
        # XXX: Until we do not have a proper Hub online
        adapter.update_hub_subscriptions()

        # Response successful
        success_response = 'Updated community "{}" subscriptions'.format(self.community.absolute_url())
        logger.info(success_response)
        return {'message': success_response, 'status_code': 200}
