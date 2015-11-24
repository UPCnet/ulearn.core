# -*- coding: utf-8 -*-
from five import grok
from zope.component import getUtility
from zope.component import queryUtility
from zope.component.hooks import getSite
from zope.interface import Interface

from Products.CMFCore.utils import getToolByName
from plone import api
from plone.dexterity.interfaces import IDexterityContent
from plone.indexer import indexer

from ulearn.theme.browser.interfaces import IUlearnTheme

from Products.Archetypes.interfaces import IBaseObject
from genweb.core.utilities import IElasticSearch

import json
import re


class IElasticSharing(Interface):
    """ Marker for ElasticSharingglobal utility """


class ElasticSharing(object):
    """
        The records that will be stored to represent sharing on ES will
        represent shared permissions over an object, storing the
        following attributes:

        principal: The id of the user or group
        path: Path to the object relative to portal root
        roles: Roles assigned to the principal on this object
        uuid: Unique ID of the community where this object belongs

    """
    grok.implements(IElasticSharing)

    def __init__(self):
        try:
            self.elastic = getUtility(IElasticSearch)
        except:
            pass
        self._root_path = None

    @property
    def site_root_path(self):
        if self._root_path is None:
            site = getSite()
            self._root_path = '/'.join(site.getPhysicalPath())
        return self._root_path

    def relative_path(self, object):
        absolute_path = '/'.    join(object.getPhysicalPath())
        return re.sub(r'^{}'.format(self.site_root_path), r'', '/'.join(absolute_path))

    def object_local_roles(self, object):
        """
            Remap local roles to exclude Owner roles
        """
        current_local_roles = {}
        for principal, roles in object.__ac_local_roles__.items():
            effective_roles = [role for role in roles if role not in ['Owner']]
            if effective_roles:
                current_local_roles['principal'] = effective_roles
        return current_local_roles

    def make_record(self, object):
        """
            Constructs a record based on <object> properties, suitable
            to be inserted on ES
        """
        path = self.relative_path(object)

        # XXX TODO
        #
        # Build object
        return {}

    def get(self, object, principal=None):
        """
            Returns an existing elastic index for a site object, empty object or list if no register found.
            If principal not specified, will return all records for an object:
        """
        path = self.relative_path(object)

        if principal is None:
            # XXX TODO
            #
            # Change to query elastic for a register matching principal and path
            # and return a list of items or None if query empty
            result = []
        else:
            # XXX TODO
            #
            # Change to Query elastic for all registers matching path
            # and returm ONE item
            result = {}

        return result

    def modified(self, object):
        """
            Handler for local roles changed event. Will add or remove a record form elastic
        """
        current_local_roles = self.object_local_roles(object)

        # Search for records to be deleted
        existing_records = self.get(object)
        existing_principals = [a['principal'] for a in existing_records]

        current_principals = current_local_roles.keys()
        principals_to_delete = set(existing_principals) - set(current_principals)

        for principal in principals_to_delete:
            self.remove(object, principal)

        # XXX Remove the next self.remove when activating ES powered sharing
        self.remove(object, None)

        # Add new records or modify existing ones
        for principal, roles in current_local_roles.items():

            es_record = self.get(object, principal)
            if not es_record:
                self.add(object, principal)
            elif es_record.roles != roles:
                self.modify(object, principal, roles=roles)
            else:
                pass
                # No changes to roles, ignore others

    def add(self, object, principal):
        """
            Adds a shared object index
        """
        record = self.make_record(object)
        SharedMarker(object).share()

        # XXX TODO
        #
        # Add record to ES for principal
        pass

    def modify(self, object, principal, attributes):
        """
            Modifies an existing ES record
        """
        path = self.relative_path(object)
        # XXX TODO
        #
        # Modify record from ES matching path and principal
        pass

    def remove(self, object, principal):
        """
            Removes a shared object index
        """
        path = self.relative_path(object)
        SharedMarker(object).unshare()

        # XXX TODO
        #
        # Remove record from ES matching path and principal
        pass

    def shared_on(self, object):
        """
            Returns a list of all items shared on a specific community
        """
        base_path = '/'.join(object.getPhysicalPath())
        portal_catalog = getToolByName(getSite(), 'portal_catalog')
        shared_items = portal_catalog.searchResults(is_shared=True)

        return [item for item in shared_items if item.getPath().startswith(base_path)]

    def shared_with(self, username):
        """
            Returns a list of all items shared with a specific user, and all groups
            where this user belongs to
        """
        user_groups = []
        principals = user_groups + [username]
        portal_catalog = getToolByName(getSite(), 'portal_catalog')

        communities_by_path = {a.getPath(): a for a in portal_catalog.searchResults(portal_type='ulearn.community')}

        def format_item(item):
            community_path = re.sub(r'(^{}\/[^\/]+)\/?.*$'.format(self.site_root_path), r'\1', item.getPath())
            community = communities_by_path[community_path]
            return dict(
                title=item.Title,
                url=item.getURL(),
                community_displayname=community.Title,
                community_url=community.getURL(),
                by=item.Creator,
                by_profile='{}/profile/{}'.format(getSite().absolute_url(), item.Creator)
            )

        def is_shared(item):
            object = item.getObject()
            if username in object.__ac_local_roles__.keys():
                effective_roles = [a for a in object.__ac_local_roles__[username] if a not in ['Owner']]
                if effective_roles:
                    return True
            return False

        shared_items = portal_catalog.searchResults(is_shared=True)
        results = [format_item(a) for a in shared_items if is_shared(a)]

        # XXX TODO
        #
        # Query ES for all registers matching principals

        return results

grok.global_utility(ElasticSharing)


class SharedWithMe(grok.View):
    grok.context(Interface)
    grok.name('shared_with_me')
    grok.require('genweb.authenticated')
    grok.layer(IUlearnTheme)

    def render(self):
        """
            AJAX view to access shared items of the current logged in user
        """
        self.request.response.setHeader('Content-type', 'application/json')
        results = []
        sharing = queryUtility(IElasticSharing)
        username = api.user.get_current().id
        results = sharing.shared_with(username)
        return json.dumps(results)


class Shared(grok.View):
    grok.context(Interface)
    grok.require('genweb.authenticated')
    grok.layer(IUlearnTheme)

    def getContent(self):
        """
            List all items shared on this community
        """
        results = []
        sharing = queryUtility(IElasticSharing)
        results = sharing.shared_on(self.context)
        return results


class IShared(Interface):
    def is_shared():
        """ Is this object shared outside a community? (true or false) """
        pass


class SharedMarker(grok.Adapter):
    grok.provides(IShared)
    grok.context(Interface)

    def __init__(self, context):
        """
            Initialize mark as non-shared
        """
        self.context = context
        if getattr(self.context, '_shared', None) is None:
            self.set_shared_mark()

    def is_shared(self):
        """
            Returns True if the object is shared
        """
        return getattr(self.context, '_shared', False)

    def share(self):
        """
            Sets the shared status of the object
        """
        if not self.is_shared():
            setattr(self.context, '_shared', True)
            self.context.indexObject()
            print
            print 'Shared'
            print

    def unshare(self):
        """
            Sets the shared status of the object
        """
        if self.is_shared():
            setattr(self.context, '_shared', False)
            self.context.indexObject()
            print
            print 'Unshared'
            print


def SharingChanged(content, event):
    """ Hook to store shared mark on object & elastic
    """
    elastic_sharing = queryUtility(IElasticSharing)
    elastic_sharing.modified(content)


@indexer(IDexterityContent)
def sharedIndexer(context):
    """Create a catalogue indexer, registered as an adapter for DX content. """
    return IShared(context).is_shared()
grok.global_adapter(sharedIndexer, name='is_shared')


@indexer(IBaseObject)
def sharedIndexerAT(context):
    """Create a catalogue indexer, registered as an adapter for AT content. """
    return IShared(context).is_shared()
grok.global_adapter(sharedIndexerAT, name='is_shared')
