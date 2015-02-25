from plone import api
from five import grok
from zope.component import getUtility
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent
from zope.component import getAdapter

from Products.CMFPlone.interfaces import IPloneSiteRoot
from repoze.catalog.query import Eq
from souper.soup import get_soup
from souper.soup import Record

from mrs.max.utilities import IMAXClient

from genweb.core.gwuuid import IGWUUID
from ulearn.core.content.community import ICommunityTyped
from ulearn.core.api import REST
from ulearn.core.api import logger
from ulearn.core.api.root import APIRoot
from ulearn.core.api.security import execute_under_special_role


class Communities(REST):
    """
        /api/communities
    """

    placeholder_type = 'community'
    placeholder_id = 'community'

    grok.adapts(APIRoot, IPloneSiteRoot)
    grok.require('ulearn.APIAccess')


class Community(REST):
    """
        /api/communities/{community}
    """

    grok.adapts(Communities, IPloneSiteRoot)
    grok.require('ulearn.APIAccess')

    def __init__(self, context, request):
        super(Community, self).__init__(context, request)


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

    def POST(self):
        """
            Subscribes a bunch of users to a community the security is given an
            initial soft check for authenticated users at the view level and
            then by checking explicitly if the requester user has permission on
            the target community.
        """
        # Hard security validation as the view is soft checked
        check_permission = self.check_roles(['Owner', 'Manager'])
        if check_permission is not True:
            return check_permission

        # Parameters validation
        validation = self.validate()
        if validation is not True:
            return validation

        self.data = self.request.form

        with api.env.adopt_roles(['Manager']):
            result = self.update_subscriptions()

        self.response.setStatus(result.pop('status'))
        return self.json_response(result)

    def update_subscriptions(self):
        pc = api.portal.get_tool(name='portal_catalog')
        result = pc.searchResults(community_hash=self.params['community'])

        if not result:
            # Fallback search by gwuuid
            result = pc.searchResults(gwuuid=self.params['community'])

            if not result:
                # Not found either by hash nor by gwuuid
                self.response.setStatus(404)
                error_response = 'Community hash not found: {}'.format(self.params['community'])
                logger.error(error_response)
                return self.json_response({'error': error_response})

        community = result[0].getObject()

        adapter = getAdapter(community, ICommunityTyped, name=community.community_type)

        # Change the uLearn part of the community
        adapter.update_acl(self.data)
        adapter.set_plone_permissions(self.data)

        # XXX Communicate the change in the community subscription to the uLearnHub
        # adapter.send_update_context()

        # Response successful
        success_response = 'Updated community "{}" subscriptions'.format(result[0].getPath())
        logger.info(success_response)
        return {'message': success_response, 'status': 200}
