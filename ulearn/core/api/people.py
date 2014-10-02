from Acquisition import aq_inner
from five import grok
from zope.component import getUtility

from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFPlone.interfaces import IPloneSiteRoot

from mrs.max.utilities import IMAXClient

from ulearn.core.api import logger
from ulearn.core.api import REST
from ulearn.core.api.root import APIRoot

import plone.api


class People(REST):
    """
        /api/people
    """

    placeholder_type = 'person'
    placeholder_id = 'username'

    grok.adapts(APIRoot, IPloneSiteRoot)
    grok.require('ulearn.APIAccess')


class Person(REST):
    """
        /api/people/{username}
    """

    grok.adapts(People, IPloneSiteRoot)
    grok.require('ulearn.APIAccess')

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
        self.create_user(
            self.params['username'],
            self.params['email'],
            password=self.params['password'],
            fullname=self.params['fullname']
        )
        self.response.setStatus(200)
        self.json_response({})

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

    def create_user(self, username, email, password=None, **properties):
        existing_user = plone.api.user.get(username=username)
        maxclient, settings = getUtility(IMAXClient)()
        maxclient.setActor(settings.max_restricted_username)
        maxclient.setToken(settings.max_restricted_token)

        if not existing_user:
            args = dict(
                email=email,
                username=username,
                properties=properties
            )
            if password:
                args['password'] = password
            plone.api.user.create(**args)
            maxclient.people[username].put(displayName=properties['fullname'])

        else:
            # Update portal membership user properties
            has_email = existing_user.getProperty('email', False)
            if not has_email:
                properties.update({'email': email})

            existing_user.setMemberProperties(properties)

            # Update MAX properties
            maxclient.people[username].post()  # Just to make sure user exists (in case it was only on ldap)
            maxclient.people[username].put(displayName=properties['fullname'])



    def deleteMembers(self, member_ids):
        # this method exists to bypass the 'Manage Users' permission check
        # in the CMF member tool's version
        context = aq_inner(self.context)
        mtool = plone.api.portal.get_tool(name='portal_membership')

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
        mdtool = plone.api.portal.get_tool(name='portal_memberdata')
        if mdtool is not None:
            for member_id in member_ids:
                mdtool.deleteMemberData(member_id)

        # Delete members' local roles.
        mtool.deleteLocalRoles(getUtility(ISiteRoot), member_ids,
                               reindex=1, recursive=1)

