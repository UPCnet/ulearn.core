from Acquisition import aq_inner
from five import grok
from zope.component import getUtility

from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFPlone.interfaces import IPloneSiteRoot
from repoze.catalog.query import Eq
from souper.soup import get_soup

from mrs.max.utilities import IMAXClient
from StringIO import StringIO
from genweb.core.utils import json_response
from ulearn.core.api import REST
from ulearn.core.api.root import APIRoot

from Products.CMFCore.utils import getToolByName
from mrs.max.portrait import changeMemberPortrait
from ulearn.core.browser.security import execute_under_special_role
from plone import api
from genweb.core.utils import add_user_to_catalog
from genweb.core.utils import get_all_user_properties

import logging
import requests

logger = logging.getLogger(__name__)


class People(REST):
    """
        /api/people
    """

    placeholder_type = 'person'
    placeholder_id = 'username'

    grok.adapts(APIRoot, IPloneSiteRoot)
    grok.require('genweb.authenticated')


class Sync(REST):
    """
        /api/people/sync
    """
    grok.adapts(People, IPloneSiteRoot)
    grok.require('genweb.authenticated')

    def __init__(self, context, request):
        super(Sync, self).__init__(context, request)

    __required_params__ = ['users']

    def POST(self):
        """
            Syncs user local registry with remote ldap attributes
        """
        validation = self.validate()
        if validation is not True:
            return validation

        maxclient, settings = getUtility(IMAXClient)()
        maxclient.setActor(settings.max_restricted_username)
        maxclient.setToken(settings.max_restricted_token)
        users = self.params['users']

        for username in users:
            user_memberdata = api.user.get(username=username)
            try:
                plone_user = user_memberdata.getUser()
                properties = get_all_user_properties(plone_user)
                add_user_to_catalog(plone_user, properties)
            except:
                logger.error('User {} cannot be found in LDAP repository'.format(username))

        self.response.setStatus(200)
        return self.json_response({})


class Person(REST):
    """
        /api/people/{username}
    """

    grok.adapts(People, IPloneSiteRoot)
    grok.require('genweb.authenticated')

    def __init__(self, context, request):
        super(Person, self).__init__(context, request)

    __required_params__ = ['username', 'fullname', 'email', 'password']

    def POST(self):
        """
            Creates a user
        """
        validation = self.validate()
        if validation is not True:
            return validation

        username = self.params.pop('username')
        email = self.params.pop('email')
        password = self.params.pop('password', None)

        result = self.create_user(
            username,
            email,
            password,
            **self.params
        )
        self.response.setStatus(result.pop('status'))
        return self.json_response(result)

    def DELETE(self):
        """
            Deletes a user from the plone & max
        """
        validation = self.validate()
        if validation is not True:
            return validation

        self.deleteMembers([self.params['username']])
        self.response.setStatus(204)
        return self.json_response({})

    def create_user(self, username, email, password, **properties):
        existing_user = api.user.get(username=username)
        maxclient, settings = getUtility(IMAXClient)()
        maxclient.setActor(settings.max_restricted_username)
        maxclient.setToken(settings.max_restricted_token)

        avatar = self.params.pop('avatar', None)

        if not existing_user:
            args = dict(
                email=email,
                username=username,
                properties=properties
            )
            if password:
                args['password'] = password
            api.user.create(**args)
            maxclient.people[username].put(displayName=properties['fullname'])
            # Save the image into the Plone user profile if provided
            if avatar:
                portal = api.portal.get()
                membership_tool = getToolByName(portal, 'portal_membership')
                imgName = (avatar.split('/')[-1]).decode('utf-8')
                imgData = requests.get(avatar).content
                image = StringIO(imgData)
                image.filename = imgName
                execute_under_special_role(portal,
                                           "Manager",
                                           changeMemberPortrait,
                                           membership_tool,
                                           image,
                                           username)

            created = 201

        else:
            # Update portal membership user properties
            has_email = existing_user.getProperty('email', False)
            if not has_email:
                properties.update({'email': email})

            existing_user.setMemberProperties(properties)

            # Update MAX properties
            maxclient.people[username].post()  # Just to make sure user exists (in case it was only on ldap)
            created = maxclient.last_response_code
            maxclient.people[username].put(displayName=properties['fullname'])

            if avatar:
                portal = api.portal.get()
                membership_tool = getToolByName(portal, 'portal_membership')
                token = maxclient.getToken(username, password)
                member = membership_tool.getMemberById(username)
                member.setMemberProperties({'oauth_token': token})
                imgName = (avatar.split('/')[-1]).decode('utf-8')
                imgData = requests.get(avatar).content
                image = StringIO(imgData)
                image.filename = imgName
                execute_under_special_role(portal,
                                           "Manager",
                                           changeMemberPortrait,
                                           membership_tool,
                                           image,
                                           username)

        if created == 201:
            return {'message': 'User {} created'.format(username), 'status': created}
        else:
            return {'message': 'User {} updated'.format(username), 'status': created}

    def deleteMembers(self, member_ids):
        # this method exists to bypass the 'Manage Users' permission check
        # in the CMF member tool's version
        context = aq_inner(self.context)
        mtool = api.portal.get_tool(name='portal_membership')

        # Delete members in acl_users.
        acl_users = context.acl_users
        if isinstance(member_ids, basestring):
            member_ids = (member_ids,)
        member_ids = list(member_ids)
        for member_id in member_ids[:]:
            member = mtool.getMemberById(member_id)
            if member is None:
                member_ids.remove(member_id)
        try:
            acl_users.userFolderDelUsers(member_ids)
        except (AttributeError, NotImplementedError):
            raise NotImplementedError(
                'The underlying User Folder '
                'doesn\'t support deleting members.')

        # Delete member data in portal_memberdata.
        mdtool = api.portal.get_tool(name='portal_memberdata')
        if mdtool is not None:
            for member_id in member_ids:
                mdtool.deleteMemberData(member_id)

        # Delete members' local roles.
        mtool.deleteLocalRoles(getUtility(ISiteRoot), member_ids,
                               reindex=1, recursive=1)


class Subscriptions(REST):
    """
        /api/people/{username}/subscriptions

        Manages the user subscriptions.
    """

    grok.adapts(Person, IPloneSiteRoot)
    grok.require('genweb.authenticated')

    @json_response
    def GET(self):
        """ Returns all the user communities."""
        # Parameters validation
        validation = self.validate()
        if validation is not True:
            return validation

        # Hard security validation as the view is soft checked
        check_permission = self.check_roles(roles=['Member', ])
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

        return result

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
