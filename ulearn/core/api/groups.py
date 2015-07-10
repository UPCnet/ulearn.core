from plone import api
from five import grok
from zope.component import getAdapter
from zope.component import getAdapters
from Products.CMFPlone.interfaces import IPloneSiteRoot
from repoze.catalog.query import Eq
from souper.soup import get_soup

from genweb.core.utils import json_response
from ulearn.core.content.community import ICommunityTyped
from ulearn.core.content.community import ICommunityACL
from ulearn.core.api import REST
from ulearn.core.api import logger
from ulearn.core.api.root import APIRoot


class Groups(REST):
    """
        /api/groups
    """

    placeholder_type = 'group'
    placeholder_id = 'group'

    grok.adapts(APIRoot, IPloneSiteRoot)
    grok.require('genweb.authenticated')


class Group(REST):
    """
        /api/groups/{group}
    """

    grok.adapts(Groups, IPloneSiteRoot)
    grok.require('genweb.authenticated')


class Communities(REST):
    """
        /api/groups/{group}/communities

        Returns

        {
            'url': context['url'],
            'groups': [],
            'users': ['testuser1.creator']
        }

    """

    grok.adapts(Group, IPloneSiteRoot)
    grok.require('ulearn.APIAccess')

    @json_response
    def GET(self):
        """

        """
        # Parameters validation
        validation = self.validate()
        if validation is not True:
            return validation

        portal = api.portal.get()
        soup = get_soup('communities_acl', portal)
        records = [r for r in soup.query(Eq('groups', self.params['group']))]

        result = []
        for record in records:
            users = [user['id'] for user in record.attrs['acl']['users']]
            result.append(dict(
                url=record.attrs['hash'],
                groups=record.attrs['groups'],
                users=users,
            ))

        return dict(data=result)
