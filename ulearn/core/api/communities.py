
from five import grok
from zope.component import getUtility
from zope.component.hooks import getSite
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent

from Products.CMFPlone.interfaces import IPloneSiteRoot

from mrs.max.utilities import IMAXClient

from ulearn.core.api import REST
from ulearn.core.api import logger
from ulearn.core.api.root import APIRoot
from ulearn.core.api.security import execute_under_special_role

import plone.api


class Communities(REST):
    """
        /api/communities
    """

    placeholder_type = 'community'
    placeholder_id = 'community'

    grok.adapts(APIRoot, IPloneSiteRoot)


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
    """

    grok.adapts(Community, IPloneSiteRoot)
    grok.require('ulearn.APIAccess')

    def POST(self):
        """
            Subscribe a bunch of users to a community
        """
        validation = self.validate()
        if validation is not True:
            return validation

        portal = getSite()
        self.data = self.request.form

        execute_under_special_role(portal, 'Manager', self.update_subscriptions)

    def update_subscriptions(self):
        pc = plone.api.portal.get_tool(name='portal_catalog')
        result = pc.searchResults(community_hash=self.params['community'])

        maxclient, settings = getUtility(IMAXClient)()
        maxclient.setActor(settings.max_restricted_username)
        maxclient.setToken(settings.max_restricted_token)

        if not result:
            self.response.setStatus(404)
            error_response = 'Community hash not found: {}'.format(self.params['community'])
            logger.error(error_response)
            return self.json_response({'error': error_response})
        else:
            readers = self.data.get('readers', [])
            editors = self.data.get('editors', [])
            owners = self.data.get('owners', [])

            readers = readers if isinstance(readers, list) else [readers]
            editors = editors if isinstance(editors, list) else [editors]
            owners = owners if isinstance(owners, list) else [owners]

            # Create users before subscriptions
            for user in readers:
                maxclient.people[user].post()
            for user in editors:
                maxclient.people[user].post()
            for user in owners:
                maxclient.people[user].post()

            community = result[0].getObject()
            community.readers = readers
            community.subscribed = editors
            community.owners = owners

            notify(ObjectModifiedEvent(community))

            success_response = 'Successfully subscribed...\nreaders:{}\neditors:{}\nowners:{}\n.'.format(readers, editors, owners)
            logger.info(success_response)
            self.response.setStatus(200)

            return self.json_response({})
