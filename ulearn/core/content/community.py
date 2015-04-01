# -*- coding: utf-8 -*-
from AccessControl import Unauthorized
from AccessControl import getSecurityManager
from five import grok
from plone import api
from z3c.form import button
from zope import schema
from zope.annotation.interfaces import IAnnotations
from zope.app.container.interfaces import IObjectAddedEvent
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component import queryUtility
from zope.component import getAdapter
from zope.component.hooks import getSite
from zope.container.interfaces import INameChooser
from zope.event import notify
from zope.interface import implements
from zope.interface import Interface
from zope.interface import alsoProvides
from zope.globalrequest import getRequest
from zope.lifecycleevent import ObjectModifiedEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from zope.lifecycleevent.interfaces import IObjectRemovedEvent
from zope.schema.fieldproperty import FieldProperty
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleVocabulary
from zope.security import checkPermission

from plone.dexterity.content import Container
from plone.dexterity.utils import createContentInContainer
from plone.directives import form
from plone.indexer import indexer
from plone.memoize.view import memoize_contextless
from plone.namedfile.field import NamedBlobImage
from plone.portlets.constants import CONTEXT_CATEGORY
from plone.portlets.interfaces import ILocalPortletAssignmentManager
from plone.portlets.interfaces import IPortletManager
from plone.registry.interfaces import IRegistry
from plone.dexterity.interfaces import IDexterityContent

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.CMFPlone.interfaces.constrains import ISelectableConstrainTypes
from Products.statusmessages.interfaces import IStatusMessage
from ZPublisher.HTTPRequest import FileUpload

from zope.interface import implementer
from zope.component import provideUtility
from repoze.catalog.catalog import Catalog
from repoze.catalog.indexes.field import CatalogFieldIndex
from repoze.catalog.indexes.keyword import CatalogKeywordIndex
from souper.interfaces import ICatalogFactory
from souper.soup import NodeAttributeIndexer
from repoze.catalog.query import Eq
from souper.soup import get_soup
from souper.soup import Record

from genweb.core.adapters.favorites import IFavorite
from genweb.core.widgets.select2_maxuser_widget import Select2MAXUserInputFieldWidget

from genweb.core.widgets.select2_user_widget import SelectWidgetConverter
from hashlib import sha1
from mrs.max.utilities import IMAXClient

from genweb.core.gwuuid import IGWUUID
from genweb.core.utils import json_response
from ulearn.core import _
from ulearn.core.interfaces import IDXFileFactory
from ulearn.core.interfaces import IDocumentFolder
from ulearn.core.interfaces import IEventsFolder
from ulearn.core.interfaces import ILinksFolder
from ulearn.core.interfaces import IPhotosFolder
from ulearn.core.interfaces import IDiscussionFolder

import json
import logging
import mimetypes
import requests

logger = logging.getLogger(__name__)
VALID_COMMUNITY_ROLES = ['reader', 'writer', 'owner']

OPEN_PERMISSIONS = dict(read='subscribed',
                        write='subscribed',
                        subscribe='public',
                        unsubscribe='public')

CLOSED_PERMISSIONS = dict(read='subscribed',
                          write='restricted',
                          subscribe='restricted',
                          unsubscribe='public')

ORGANIZATIVE_PERMISSIONS = dict(read='subscribed',
                                write='restricted',
                                subscribe='restricted',
                                unsubscribe='restricted')


@grok.provider(IContextSourceBinder)
def availableCommunityTypes(context):
    proot = getSite()
    pm = getToolByName(proot, 'portal_membership')
    sm = getSecurityManager()
    user = pm.getAuthenticatedMember()
    terms = []

    terms.append(SimpleVocabulary.createTerm(u'Closed', 'closed', _(u'Closed')))
    terms.append(SimpleVocabulary.createTerm(u'Open', 'open', _(u'Open')))

    if sm.checkPermission('Modify portal content', context) or \
       ('Manager' in user.getRoles()) or \
       ('WebMaster' in user.getRoles()) or \
       ('Site Administrator' in user.getRoles()):
        terms.append(SimpleVocabulary.createTerm(u'Organizative', 'organizative', _(u'Organizative')))

    return SimpleVocabulary(terms)


@grok.provider(IContextSourceBinder)
def communityActivityViews(context):
    terms = []

    terms.append(SimpleVocabulary.createTerm(u'Darreres activitats', 'darreres_activitats', _(u'Darreres activitats')))
    terms.append(SimpleVocabulary.createTerm(u'Activitats mes valorades', 'activitats_mes_valorades', _(u'Activitats mes valorades')))
    terms.append(SimpleVocabulary.createTerm(u'Activitats destacades', 'activitats_destacades', _(u'Activitats destacades')))

    return SimpleVocabulary(terms)


class IInitializedCommunity(Interface):
    """
        A Community that has been succesfully initialized
    """


class ICommunity(form.Schema):
    """ A manageable community
    """

    title = schema.TextLine(
        title=_(u"Nom"),
        description=_(u"Nom de la comunitat"),
        required=True
    )

    description = schema.Text(
        title=_(u"Descripció"),
        description=_(u"La descripció de la comunitat"),
        required=False
    )
    form.mode(community_type='hidden')
    community_type = schema.Choice(
        title=_(u"Tipus de comunitat"),
        description=_(u"community_type_description"),
        source=availableCommunityTypes,
        required=True,
        default=u'Closed'
    )

    activity_view = schema.Choice(
        title=_(u"activity_view"),
        description=_(u"help_activity_view"),
        source=communityActivityViews,
        required=True,
        default=u'Darreres activitats')

    form.omitted('readers', 'subscribed', 'owners')
    form.widget(readers=Select2MAXUserInputFieldWidget)
    readers = schema.List(
        title=_(u"Readers"),
        description=_(u"Subscribed people with read-only permissions"),
        value_type=schema.TextLine(),
        required=False,
        missing_value=[],
        default=[])

    # We maintain the subscribed field for backwards compatibility,
    # understanding that it refers to users with read/write permissions
    form.widget(subscribed=Select2MAXUserInputFieldWidget)
    subscribed = schema.List(
        title=_(u"Editors"),
        description=_(u"Subscribed people with editor permissions"),
        value_type=schema.TextLine(),
        required=False,
        missing_value=[],
        default=[])

    form.widget(owners=Select2MAXUserInputFieldWidget)
    owners = schema.List(
        title=_(u"Owners"),
        description=_(u"Subscribed people with owner permissions"),
        value_type=schema.TextLine(),
        required=False,
        missing_value=[],
        default=[])

    image = NamedBlobImage(
        title=_(u"Imatge"),
        description=_(u"Imatge que defineix la comunitat"),
        required=False,
    )

    twitter_hashtag = schema.TextLine(
        title=_(u"Twitter hashtag"),
        description=_(u'hashtag_help'),
        required=False
    )

    notify_activity_via_push = schema.Bool(
        title=_(u"Notify activity via push"),
        description=_(u'notify_activity_via_push_help'),
        required=False
    )

    notify_activity_via_push_comments_too = schema.Bool(
        title=_(u"Notify activity and comments via push"),
        description=_(u'help_notify_activity_via_push_comments_too'),
        required=False
    )


class ICommunityACL(Interface):
    """Helper to retrieve the community ACL safely by adapting any ICommunity"""


@grok.implementer(ICommunityACL)
@grok.adapter(ICommunity)
class GetCommunityACL(object):
    def __init__(self, context):
        self.context = context

    def __call__(self):
        portal = api.portal.get()
        soup = get_soup('communities_acl', portal)
        gwuuid = IGWUUID(self.context)
        records = [r for r in soup.query(Eq('gwuuid', gwuuid))]

        if records:
            return records[0]
        else:
            return None


class ICommunityTyped(Interface):
    """ The adapter for the ICommunity It would adapt the Community instances in
        order to have a centralized way of dealing with community types and the
        common processes with them.
    """


class CommunityAdapterMixin(object):
    """ Common methods for community adapters """
    def __init__(self, context):
        self.context = context
        self.get_max_client()

        # Determine the value for notifications
        if self.context.notify_activity_via_push and self.context.notify_activity_via_push_comments_too:
            self.max_notifications = 'comments'
        elif self.context.notify_activity_via_push and not self.context.notify_activity_via_push_comments_too:
            self.max_notifications = 'posts'
        elif not self.context.notify_activity_via_push and not self.context.notify_activity_via_push_comments_too:
            self.max_notifications = False

    def get_max_client(self):
        self.maxclient, self.settings = getUtility(IMAXClient)()
        self.maxclient.setActor(self.settings.max_restricted_username)
        self.maxclient.setToken(self.settings.max_restricted_token)

    def create_max_context(self):
        """ Add context for the community on MAX server given a set of
            properties like context permissions and notifications.
        """
        self.maxclient.contexts.post(
            url=self.context.absolute_url(),
            displayName=self.context.title,
            permissions=self.max_permissions,
            notifications=self.max_notifications,
        )

    def set_initial_max_metadata(self):
        # Update twitter hashtag
        self.maxclient.contexts[self.context.absolute_url()].put(
            twitterHashtag=self.context.twitter_hashtag
        )

        # Update community tag
        self.maxclient.contexts[self.context.absolute_url()].tags.put(data=['[COMMUNITY]'])

    def set_initial_subscription(self, acl):
        self.maxclient.people[self.context.Creator()].subscriptions.post(object_url=self.context.absolute_url())
        self.update_acl(acl)

    def update_community_type(self):
        # Guard in case the update could already be made by other means
        context_current_info = self.maxclient.contexts[self.context.absolute_url()].get()
        should_update = False
        for key in self.max_permissions:
            if self.max_permissions[key] != context_current_info['permissions'][key]:
                should_update = True
        if should_update:
            properties_to_update = dict(permissions=self.max_permissions)
            self.maxclient.contexts[self.context.absolute_url()].put(**properties_to_update)

        # Update the community_type field
        self.context.community_type = self.__component_name__

        # and related permissions
        self.set_plone_permissions(self.get_acl())

    def get_acl(self):
        return ICommunityACL(self.context)().attrs.get('acl', '')

    def update_acl(self, acl):
        gwuuid = IGWUUID(self.context)
        portal = api.portal.get()
        soup = get_soup('communities_acl', portal)

        records = [r for r in soup.query(Eq('gwuuid', gwuuid))]

        # Save ACL into the communities_acl soup
        if records:
            acl_record = records[0]
        else:
            # The community isn't indexed in the acl catalog yet, so do it now.
            record = Record()
            record.attrs['path'] = '/'.join(self.context.getPhysicalPath())
            record.attrs['gwuuid'] = gwuuid
            record.attrs['hash'] = sha1(self.context.absolute_url()).hexdigest()
            record_id = soup.add(record)
            acl_record = soup.get(record_id)

        acl_record.attrs['groups'] = [g['id'] for g in acl.get('groups', []) if g.get('id', False)]
        acl_record.attrs['acl'] = acl

        soup.reindex(records=[acl_record])

    def delete_acl(self):
        """ In case that we delete the community, delete its ACL record. """
        gwuuid = IGWUUID(self.context)
        portal = api.portal.get()
        soup = get_soup('communities_acl', portal)

        records = [r for r in soup.query(Eq('gwuuid', gwuuid))]

        if records:
            del soup[records[0]]

    def remove_acl_atomic(self, username):
        acl = self.get_acl()

        for user in acl['users']:
            if user['id'] == username:
                acl['users'].remove(user)

        self.update_acl(acl)

    def update_acl_atomic(self, username, role):
        """ This method is used when it is required to perform an atomic (single
            user) acl update to a community.
        """
        acl = self.get_acl()
        new_user_acl = dict(id=username, displayName=u'', role=role)
        acl['users'].append(new_user_acl)
        self.update_acl(acl)

    def update_hub_subscriptions(self):
        portal = api.portal.get()
        subscribe_request = {}
        subscribe_request['component'] = dict(type='communities', id=portal.absolute_url())
        subscribe_request['permission_mapping'] = self.hub_permission_mapping
        subscribe_request['ignore_grants_and_vetos'] = True
        subscribe_request['context'] = self.context.absolute_url()
        subscribe_request['acl'] = self.get_acl()

        requests.post('{}/api/domains/{}/services/syncacl'.format(self.settings.hub_server, self.settings.domain), json=subscribe_request)

    def add_max_subscription_atomic(self, username):
        """ Used in auto-subscribe an user to an Open community. """
        self.maxclient.people[username].subscriptions.post(object_url=self.context.absolute_url())

    def remove_max_subscription_atomic(self, username):
        """ Used in unsubscribe an user to an Open or Closed community. """
        self.maxclient.people[username].subscriptions[self.context.absolute_url()].delete()

    def update_max_context(self):
        # Get current MAX context information
        context_current_info = self.maxclient.contexts[self.context.absolute_url()].get()

        # collect updated properties
        properties_to_update = {}
        if context_current_info:
            if context_current_info.get('twitterHashtag', None) != self.context.twitter_hashtag:
                properties_to_update['twitterHashtag'] = self.context.twitter_hashtag

            if context_current_info.get('displayName', '') != self.context.title:
                properties_to_update['displayName'] = self.context.title

            if context_current_info.get('notifications', '') != self.max_notifications:
                properties_to_update['notifications'] = self.max_notifications

        # update context properties that have changed
        if properties_to_update:
            self.maxclient.contexts[self.context.absolute_url()].put(**properties_to_update)

    def delete_max_context(self):
        self.maxclient.contexts[self.context.absolute_url()].delete()

    def set_plone_permissions(self, acl, changed=False):
        """ Set the Plone local roles given the acl. Shameless ripped off from
            sharing.py in p.a.workflow
        """
        user_and_groups = acl.get('users', []) + acl.get('groups', [])

        # Sanitize the list, just in case
        user_and_groups = [p for p in user_and_groups if p.get('id', False) and p.get('role', False) and p.get('role', '') in VALID_COMMUNITY_ROLES]

        member_ids_to_clear = []

        for principal in user_and_groups:
            user_id = principal['id']
            existing_roles = frozenset(self.context.get_local_roles_for_userid(userid=user_id))

            if principal['role'] == u'reader':
                selected_roles = frozenset(['Reader', ])

            if principal['role'] == u'writer':
                selected_roles = frozenset(['Reader', 'Contributor', 'Editor'])

            if principal['role'] == u'owner':
                selected_roles = frozenset(['Reader', 'Contributor', 'Editor', 'Owner'])

            managed_roles = frozenset(['Reader', 'Contributor', 'Editor', 'Owner'])
            relevant_existing_roles = managed_roles & existing_roles

            # If, for the managed roles, the new set is the same as the
            # current set we do not need to do anything.
            if relevant_existing_roles == selected_roles:
                continue

            # We will remove those roles that we are managing and which set
            # on the context, but which were not selected
            to_remove = relevant_existing_roles - selected_roles

            # Leaving us with the selected roles, less any roles that we
            # want to remove
            wanted_roles = (selected_roles | existing_roles) - to_remove

            # take away roles that we are managing, that were not selected
            # and which were part of the existing roles

            if wanted_roles:
                self.context.manage_setLocalRoles(user_id, list(wanted_roles))
                changed = True
            elif existing_roles:
                member_ids_to_clear.append(user_id)

        if member_ids_to_clear:
            self.context.manage_delLocalRoles(userids=member_ids_to_clear)
            changed = True

        if changed:
            self.context.reindexObjectSecurity()


@grok.implementer(ICommunityTyped)
@grok.adapter(ICommunity, name="Organizative")
class OrganizativeCommunity(CommunityAdapterMixin):
    """ Named adapter for the organizative communities """
    def __init__(self, context):
        super(OrganizativeCommunity, self).__init__(context)
        self.max_permissions = ORGANIZATIVE_PERMISSIONS
        self.hub_permission_mapping = dict(reader=['read'],
                                           write=['read', 'write'],
                                           owner=['read', 'write', 'unsubscribe', 'flag'])


@grok.implementer(ICommunityTyped)
@grok.adapter(ICommunity, name="Open")
class OpenCommunity(CommunityAdapterMixin):
    """ Named adapter for the open communities """
    def __init__(self, context):
        super(OpenCommunity, self).__init__(context)
        self.max_permissions = OPEN_PERMISSIONS
        self.hub_permission_mapping = dict(reader=['read', 'unsubscribe'],
                                           write=['read', 'write', 'unsubscribe'],
                                           owner=['read', 'write', 'unsubscribe', 'flag'])

    def set_plone_permissions(self, acl, changed=False):

        if not self.context.get_local_roles_for_userid(userid='AuthenticatedUsers'):
            self.context.manage_setLocalRoles('AuthenticatedUsers', ['Reader'])
            changed = True

        super(OpenCommunity, self).set_plone_permissions(acl, changed)


@grok.implementer(ICommunityTyped)
@grok.adapter(ICommunity, name="Closed")
class ClosedCommunity(CommunityAdapterMixin):
    """ Named adapter for the closed communities """
    def __init__(self, context):
        super(ClosedCommunity, self).__init__(context)
        self.max_permissions = CLOSED_PERMISSIONS
        self.hub_permission_mapping = dict(reader=['read', 'unsubscribe'],
                                           write=['read', 'write', 'unsubscribe'],
                                           owner=['read', 'write', 'unsubscribe', 'flag'])

    def set_initial_subscription(self, acl):
        super(ClosedCommunity, self).set_initial_subscription(acl)
        self.maxclient.contexts[self.context.absolute_url()].permissions[self.context.Creator()]['write'].put()

    def set_plone_permissions(self, acl, changed=False):

        if self.context.get_local_roles_for_userid(userid='AuthenticatedUsers'):
            self.context.manage_delLocalRoles(['AuthenticatedUsers'])
            changed = True

        super(ClosedCommunity, self).set_plone_permissions(acl, changed)


class Community(Container):
    implements(ICommunity)


@indexer(ICommunity)
def imageFilename(context):
    """Create a catalogue indexer, registered as an adapter, which can
    populate the ``context.filename`` value and index it.
    """
    return context.image.filename
grok.global_adapter(imageFilename, name='image_filename')


@indexer(ICommunity)
def subscribed_items(context):
    """Create a catalogue indexer, registered as an adapter, which can
    populate the ``context.subscribed`` value count it and index.
    """
    return len(list(set(context.readers + context.subscribed + context.owners)))
grok.global_adapter(subscribed_items, name='subscribed_items')


@indexer(ICommunity)
def subscribed_users(context):
    """Create a catalogue indexer, registered as an adapter, which can
    populate the ``context.subscribed`` value count it and index.
    """
    return list(set(context.readers + context.subscribed + context.owners))
grok.global_adapter(subscribed_users, name='subscribed_users')


@indexer(ICommunity)
def community_type(context):
    """Create a catalogue indexer, registered as an adapter, which can
    populate the ``community_type`` value count it and index.
    """
    return context.community_type
grok.global_adapter(community_type, name='community_type')


@indexer(ICommunity)
def community_hash(context):
    """Create a catalogue indexer, registered as an adapter, which can
    populate the ``community_hash`` value count it and index.
    """
    return sha1(context.absolute_url()).hexdigest()
grok.global_adapter(community_hash, name='community_hash')


class View(grok.View):
    grok.context(ICommunity)

    def canEditCommunity(self):
        return checkPermission('cmf.RequestReview', self.context)

    @memoize_contextless
    def portal_url(self):
        return self.portal().absolute_url()

    @memoize_contextless
    def portal(self):
        return getSite()

    def is_user_subscribed(self):
        pm = getToolByName(self.context, "portal_membership")
        current_user = pm.getAuthenticatedMember().getUserName()
        return current_user in self.context.readers or \
            current_user in self.context.subscribed or \
            current_user in self.context.owners

    def show_community_open_but_not_subscribed(self):
        if self.context.community_type == 'Open' and \
           not self.is_user_subscribed():
            return True
        else:
            return False

    def show_community_open_subscribed_readonly(self):
        """ This use case happens when given a closed community and then is
            converted to an open one, the users with reader role stays with that
            role, but are allowed to 'upgrade' it to writer.
        """
        pm = getToolByName(self.context, "portal_membership")
        current_user = pm.getAuthenticatedMember().getUserName()
        if self.context.community_type == 'Open' and \
           current_user in self.context.readers and \
           current_user not in self.context.owners and \
           current_user not in self.context.subscribed:
            return True
        else:
            return False


class EditACL(grok.View):
    grok.context(ICommunity)

    def get_gwuuid(self):
        return IGWUUID(self.context)

    def get_acl(self):
        return json.dumps(ICommunityACL(self.context)().attrs.get('acl', ''))


class UploadFile(grok.View):
    grok.context(ICommunity)
    grok.name('upload')

    def canEditCommunity(self):
        return checkPermission('cmf.RequestReview', self.context)

    @memoize_contextless
    def portal_url(self):
        return self.portal().absolute_url()

    @memoize_contextless
    def portal(self):
        return getSite()

    def is_user_subscribed(self):
        pm = getToolByName(self.context, "portal_membership")
        current_user = pm.getAuthenticatedMember().getUserName()
        return current_user in self.context.readers or \
            current_user in self.context.subscribed or \
            current_user in self.context.owners

    def get_images_folder(self):
        for obj in self.context.objectIds():
            if IPhotosFolder.providedBy(self.context[obj]):
                return self.context[obj]

    def get_documents_folder(self):
        for obj in self.context.objectIds():
            if IDocumentFolder.providedBy(self.context[obj]):
                return self.context[obj]

    def render(self):
        if 'multipart/form-data' not in self.request['CONTENT_TYPE'] and \
           len(self.request.form.keys()) != 1:
            self.request.response.setHeader("Content-type", "application/json")
            self.request.response.setStatus(400)
            return json.dumps({"Error": "Not supported upload method"})

        for key in self.request.form.keys():
            if isinstance(self.request.form[key], FileUpload):
                file_key = key

        input_file = self.request.form[file_key]
        filename = input_file.filename
        activity_text = self.request.get('activity', '')

        ctr = getToolByName(self.context, 'content_type_registry')
        type_ = ctr.findTypeName(filename.lower(), '', '') or 'File'
        if type_ == 'File':
            container = self.get_documents_folder()
        else:
            container = self.get_images_folder()

        content_type = mimetypes.guess_type(filename)[0] or ""
        factory = IDXFileFactory(container)

        try:
            thefile = factory(filename, content_type, input_file, activity_text, self.request)
            self.request.response.setStatus(201)
            return json.dumps({"uploadURL": thefile.absolute_url(), "thumbURL": "{}/@@images/image/mini".format(thefile.absolute_url())})
        except Unauthorized:
            self.request.response.setHeader("Content-type", "application/json")
            self.request.response.setStatus(401)
            return json.dumps({"Error": "Unauthorized"})


class ToggleFavorite(grok.View):
    grok.context(IDexterityContent)
    grok.name('toggle-favorite')

    @json_response
    def render(self):
        if self.request.method == 'POST':
            current_user = api.user.get_current()
            if current_user.id in IFavorite(self.context).get():
                IFavorite(self.context).remove(current_user)
                return dict(message='UnFavorited', status_code=200)
            else:
                IFavorite(self.context).add(current_user)
                return dict(message='Favorited', status_code=200)

        if self.request.method != 'POST':
            return dict(error='Bad request. POST request expected.',
                        status_code=400)


class Subscribe(grok.View):
    """" Subscribe a requester user to an open community """
    grok.context(ICommunity)
    grok.name('subscribe')

    @json_response
    def render(self):
        community = self.context
        current_user = api.user.get_current()

        if self.request.method == 'POST' and \
           community.community_type == u'Open' and \
           'Reader' in api.user.get_roles(obj=self.context):
            adapter = getAdapter(self.context, ICommunityTyped, name=self.context.community_type)

            # Subscribe to context
            try:
                adapter.add_max_subscription_atomic(current_user.id)
            except:
                return dict(error='Something bad happened while sending the related MAX request.',
                            status_code='502')

            # For this use case, the user is able to auto-subscribe to the
            # community with write permissions
            adapter.update_acl_atomic(current_user.id, u'write')

            acl = adapter.get_acl()
            # Finally, we update the plone permissions
            adapter.set_plone_permissions(acl)

            return dict(message='Subscription to the requested open community done.')

        if self.request.method != 'POST':
            return dict(error='Bad request. POST request expected.',
                        status_code=400)


class UnSubscribe(grok.View):
    """ Unsubscribe from an Open or Closed community. """

    grok.context(ICommunity)
    grok.name('unsubscribe')

    @json_response
    def render(self):
        community = self.context
        current_user = api.user.get_current()

        if self.request.method == 'POST':
            if community.community_type == u'Open' or community.community_type == u'Closed':
                adapter = getAdapter(self.context, ICommunityTyped, name=self.context.community_type)

                # Unsubscribe to context
                try:
                    adapter.remove_max_subscription_atomic(current_user.id)
                except:
                    return dict(error='Something bad happened while sending the related MAX request.',
                                status_code='502')

                # Remove from acl
                adapter.remove_acl_atomic(current_user.id)

                acl = adapter.get_acl()
                # Finally, we update the plone permissions
                adapter.set_plone_permissions(acl)

                # Unfavorite
                IFavorite(self.context).remove(current_user)

                return dict(message='Unsubscription to the requested community done.')

            elif community.community_type == u'Organizative':
                # Bad, bad guy... You shouldn't been trying this...
                return dict(error='Unsubscription from organizative community forbidden.',
                            status_code='403')

        if self.request.method != 'POST':
            return dict(error='Bad request. POST request expected.',
                        status_code=400)


class UpgradeSubscribe(grok.View):
    """ DEPRECATED: ASK JAVIER. Upgrade subscription from reader to editor in an open community. """

    grok.context(ICommunity)
    grok.name('upgrade-subscribe')

    def render(self):
        community = self.context
        pm = getToolByName(self.context, "portal_membership")
        current_user = pm.getAuthenticatedMember().getUserName()

        if community.community_type == u'Open':
            if current_user in community.readers:
                community.remove_subscription(unicode(current_user), 'readers')
                community.add_subscription(unicode(current_user), 'subscribed')
                community.reindexObject()
                notify(ObjectModifiedEvent(community))
                return True
            else:
                return False

        elif community.community_type == u'Organizative':
            # Bad, bad guy... You shouldn't been trying this...
            return False


class communityAdder(form.SchemaForm):
    grok.name('addCommunity')
    grok.context(IPloneSiteRoot)
    grok.require('ulearn.addCommunity')

    schema = ICommunity
    ignoreContext = True

    def update(self):
        super(communityAdder, self).update()
        self.actions['save'].addClass('context')

    def updateWidgets(self):
        super(communityAdder, self).updateWidgets()
        # Override the interface forced 'hidden' to 'input' for add form only
        self.widgets['community_type'].mode = 'input'

    @button.buttonAndHandler(_(u'Crea la comunitat'), name="save")
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        nom = data['title']
        description = data['description']
        image = data['image']
        community_type = data['community_type']
        activity_view = data['activity_view']
        twitter_hashtag = data['twitter_hashtag']
        notify_activity_via_push = data['notify_activity_via_push']
        notify_activity_via_push_comments_too = data['notify_activity_via_push_comments_too']

        portal = api.portal.get()
        pc = api.portal.get_tool('portal_catalog')

        nom = safe_unicode(nom)
        chooser = INameChooser(self.context)
        id_normalized = chooser.chooseName(nom, self.context.aq_parent)

        result = pc.unrestrictedSearchResults(portal_type='ulearn.community', id=id_normalized)

        if result:
            msgid = _(u"comunitat_existeix", default=u'La comunitat ${comunitat} ja existeix, si us plau, escolliu un altre nom.', mapping={u"comunitat": nom})

            translated = self.context.translate(msgid)

            messages = IStatusMessage(self.request)
            messages.addStatusMessage(translated, type="info")

            self.request.response.redirect('{}/++add++ulearn.community'.format(portal.absolute_url()))
        else:
            new_comunitat_id = self.context.invokeFactory(
                'ulearn.community',
                id_normalized,
                title=nom,
                description=description,
                image=image,
                community_type=community_type,
                activity_view=activity_view,
                twitter_hashtag=twitter_hashtag,
                notify_activity_via_push=notify_activity_via_push,
                notify_activity_via_push_comments_too=notify_activity_via_push_comments_too,
                checkConstraints=False)

            new_comunitat = self.context[new_comunitat_id]
            # Redirect back to the front page with a status message
            msgid = _(u"comunitat_creada", default=u'La comunitat ${comunitat} ha estat creada.', mapping={u"comunitat": nom})

            translated = self.context.translate(msgid)

            messages = IStatusMessage(self.request)
            messages.addStatusMessage(translated, type="info")

            self.request.response.redirect(new_comunitat.absolute_url())


class communityEdit(form.SchemaForm):
    grok.name('editCommunity')
    grok.context(ICommunity)
    grok.require('cmf.ModifyPortalContent')

    schema = ICommunity
    ignoreContext = True

    ctype_map = {u'Closed': 'closed', u'Open': 'open', u'Organizative': 'organizative'}
    cview_map = {u'Darreres activitats': 'darreres_activitats', u'Activitats mes valorades': 'activitats_mes_valorades', u'Activitats destacades': 'activitats_destacades'}

    def update(self):
        super(communityEdit, self).update()
        self.actions['save'].addClass('context')

    def updateWidgets(self):
        super(communityEdit, self).updateWidgets()

        self.widgets["title"].value = self.context.title
        self.widgets["description"].value = self.context.description
        self.widgets["community_type"].value = [self.ctype_map[self.context.community_type]]
        self.widgets["activity_view"].value = [self.cview_map[self.context.activity_view]]
        self.widgets["twitter_hashtag"].value = self.context.twitter_hashtag

        if self.context.notify_activity_via_push:
            self.widgets["notify_activity_via_push"].value = ['selected']
            # Bool widgets should call update() once modified
            self.widgets["notify_activity_via_push"].update()

        if self.context.notify_activity_via_push_comments_too:
            self.widgets["notify_activity_via_push_comments_too"].value = ['selected']
            # Bool widgets should call update() once modified
            self.widgets["notify_activity_via_push_comments_too"].update()

        converter = SelectWidgetConverter(self.fields['readers'].field, self.widgets["readers"])
        self.widgets["readers"].value = converter.toWidgetValue(self.context.readers)

        converter = SelectWidgetConverter(self.fields['subscribed'].field, self.widgets["subscribed"])
        self.widgets["subscribed"].value = converter.toWidgetValue(self.context.subscribed)

        converter = SelectWidgetConverter(self.fields['owners'].field, self.widgets["owners"])
        self.widgets["owners"].value = converter.toWidgetValue(self.context.owners)

    @button.buttonAndHandler(_(u'Edita la comunitat'), name="save")
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        nom = data['title']
        description = data['description']
        readers = data['readers']
        subscribed = data['subscribed']
        owners = data['owners']
        image = data['image']
        community_type = data['community_type']
        activity_view = data['activity_view']
        twitter_hashtag = data['twitter_hashtag']
        notify_activity_via_push = data['notify_activity_via_push']
        notify_activity_via_push_comments_too = data['notify_activity_via_push_comments_too']

        portal = getSite()
        pc = getToolByName(portal, 'portal_catalog')
        result = pc.unrestrictedSearchResults(portal_type='ulearn.community', Title=nom)

        if result and self.context.title != nom:
            msgid = _(u"comunitat_existeix", default=u'La comunitat ${comunitat} ja existeix, si us plau, escolliu un altre nom.', mapping={u"comunitat": nom})

            translated = self.context.translate(msgid)

            messages = IStatusMessage(self.request)
            messages.addStatusMessage(translated, type="info")

            self.request.response.redirect('{}/edit'.format(self.context.absolute_url()))

        else:
            # Set new values in community
            self.context.title = nom
            self.context.description = description
            self.context.readers = readers
            self.context.subscribed = subscribed
            self.context.owners = owners
            self.context.community_type = community_type
            self.context.activity_view = activity_view
            self.context.twitter_hashtag = twitter_hashtag
            self.context.notify_activity_via_push = notify_activity_via_push
            self.context.notify_activity_via_push_comments_too = notify_activity_via_push_comments_too

            if image:
                self.context.image = image

            self.context.reindexObject()

            notify(ObjectModifiedEvent(self.context))

            msgid = _(u"comunitat_modificada", default=u'La comunitat ${comunitat} ha estat modificada.', mapping={u"comunitat": nom})

            translated = self.context.translate(msgid)

            messages = IStatusMessage(self.request)
            messages.addStatusMessage(translated, type="info")

            self.request.response.redirect(self.context.absolute_url())


@grok.subscribe(ICommunity, IObjectAddedEvent)
def initialize_community(community, event):
    """ On creation we only initialize the community based on its type and all
        the Plone-based processes. On the MAX side, for convenience we create
        the context directly into the MAX server with only the creator as
        subscriber (and owner).
    """
    initial_acl = dict(users=[dict(id=unicode(community.Creator().encode('utf-8')), role='owner')])
    adapter = getAdapter(community, ICommunityTyped, name=community.community_type)

    adapter.create_max_context()
    adapter.set_initial_max_metadata()
    adapter.set_initial_subscription(initial_acl)
    adapter.set_plone_permissions(initial_acl)

    # Disable Inheritance
    community.__ac_local_roles_block__ = True

    # Auto-favorite the creator user to this community
    IFavorite(community).add(community.Creator())

    # Create default content containers
    documents = createContentInContainer(community, 'Folder', title='documents', checkConstraints=False)
    links = createContentInContainer(community, 'Folder', title='links', checkConstraints=False)
    photos = createContentInContainer(community, 'Folder', title='media', checkConstraints=False)
    events = createContentInContainer(community, 'Folder', title='events', checkConstraints=False)

    # Set the correct title, translated
    documents.setTitle(community.translate(_(u"Documents")))
    links.setTitle(community.translate(_(u"Enllaços")))
    photos.setTitle(community.translate(_(u"Media")))
    events.setTitle(community.translate(_(u"Esdeveniments")))

    # Create the default discussion container and set title
    discussion = createContentInContainer(community, 'Folder', title='discussion', checkConstraints=False)
    discussion.setTitle(community.translate(_(u"Discussion")))

    # Set default view layout
    documents.setLayout('filtered_contents_search_view')
    # links.setLayout('folder_summary_view')
    # photos.setLayout('folder_summary_view')
    events.setLayout('folder_summary_view')
    discussion.setLayout('discussion_folder_view')

    # Mark them with a marker interface
    alsoProvides(documents, IDocumentFolder)
    # alsoProvides(links, ILinksFolder)
    # alsoProvides(photos, IPhotosFolder)
    alsoProvides(events, IEventsFolder)
    alsoProvides(discussion, IDiscussionFolder)

    # Set on them the allowable content types
    behavior = ISelectableConstrainTypes(documents)
    behavior.setConstrainTypesMode(1)
    behavior.setLocallyAllowedTypes(('Document', 'File', 'Folder','Link','Image'))
    behavior.setImmediatelyAddableTypes(('Document', 'File', 'Folder','Link','Image'))
    # behavior = ISelectableConstrainTypes(links)
    # behavior.setConstrainTypesMode(1)
    # behavior.setLocallyAllowedTypes(('Link', 'Folder'))
    # behavior.setImmediatelyAddableTypes(('Link', 'Folder'))
    # behavior = ISelectableConstrainTypes(photos)
    # behavior.setConstrainTypesMode(1)
    # behavior.setLocallyAllowedTypes(('Image', 'Folder'))
    # behavior.setImmediatelyAddableTypes(('Image', 'Folder'))
    behavior = ISelectableConstrainTypes(events)
    behavior.setConstrainTypesMode(1)
    behavior.setLocallyAllowedTypes(('Event', 'Folder'))
    behavior.setImmediatelyAddableTypes(('Event', 'Folder'))
    behavior = ISelectableConstrainTypes(discussion)
    behavior.setConstrainTypesMode(1)
    behavior.setLocallyAllowedTypes(('ulearn.discussion', 'Folder'))
    behavior.setImmediatelyAddableTypes(('ulearn.discussion', 'Folder'))

    # Blacklist the right column portlets on documents
    right_manager = queryUtility(IPortletManager, name=u"plone.rightcolumn")
    blacklist = getMultiAdapter((documents, right_manager), ILocalPortletAssignmentManager)
    blacklist.setBlacklistStatus(CONTEXT_CATEGORY, True)

    # # Blacklist the right column portlets on photos
    # right_manager = queryUtility(IPortletManager, name=u"plone.rightcolumn")
    # blacklist = getMultiAdapter((photos, right_manager), ILocalPortletAssignmentManager)
    # blacklist.setBlacklistStatus(CONTEXT_CATEGORY, True)

    # # Blacklist the right column portlets on links
    # right_manager = queryUtility(IPortletManager, name=u"plone.rightcolumn")
    # blacklist = getMultiAdapter((links, right_manager), ILocalPortletAssignmentManager)
    # blacklist.setBlacklistStatus(CONTEXT_CATEGORY, True)

    # Blacklist the right column portlets on events
    right_manager = queryUtility(IPortletManager, name=u"plone.rightcolumn")
    blacklist = getMultiAdapter((events, right_manager), ILocalPortletAssignmentManager)
    blacklist.setBlacklistStatus(CONTEXT_CATEGORY, True)

    # Blacklist the right column portlets on discussion
    right_manager = queryUtility(IPortletManager, name=u"plone.rightcolumn")
    blacklist = getMultiAdapter((discussion, right_manager), ILocalPortletAssignmentManager)
    blacklist.setBlacklistStatus(CONTEXT_CATEGORY, True)

    # Reindex all created objects
    community.reindexObject()
    documents.reindexObject()
    # links.reindexObject()
    # photos.reindexObject()
    events.reindexObject()
    discussion.reindexObject()

    # Mark community as initialitzated, to avoid previous
    # folder creations to trigger modify event
    alsoProvides(community, IInitializedCommunity)


@grok.subscribe(ICommunity, IObjectModifiedEvent)
def edit_community(community, event):
    # Skip community modification if community is in creation state
    if not IInitializedCommunity.providedBy(community):
        return

    adapter = getAdapter(community, ICommunityTyped, name=community.community_type)
    adapter.update_max_context()


@grok.subscribe(ICommunity, IObjectRemovedEvent)
def delete_community(community, event):
    try:
        adapter = getAdapter(community, ICommunityTyped, name=community.community_type)
        adapter.delete_max_context()
        adapter.delete_acl()
    except:
        logger.error('There was an error deleting the community {}'.community.absolute_url())


@implementer(ICatalogFactory)
class ACLSoupCatalog(object):
    def __call__(self, context):
        catalog = Catalog()
        pathindexer = NodeAttributeIndexer('path')
        catalog['path'] = CatalogFieldIndex(pathindexer)
        hashindex = NodeAttributeIndexer('hash')
        catalog['hash'] = CatalogFieldIndex(hashindex)
        gwuuid = NodeAttributeIndexer('gwuuid')
        catalog['gwuuid'] = CatalogFieldIndex(gwuuid)
        groups = NodeAttributeIndexer('groups')
        catalog['groups'] = CatalogKeywordIndex(groups)
        return catalog
grok.global_utility(ACLSoupCatalog, name='communities_acl')
