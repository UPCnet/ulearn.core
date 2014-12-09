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

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.CMFPlone.interfaces.constrains import ISelectableConstrainTypes
from Products.statusmessages.interfaces import IStatusMessage
from ZPublisher.HTTPRequest import FileUpload
from genweb.core.adapters.favorites import IFavorite
from genweb.core.widgets.select2_maxuser_widget import Select2MAXUserInputFieldWidget

from genweb.core.widgets.select2_user_widget import SelectWidgetConverter
from hashlib import sha1
from maxclient.rest import MaxClient
from mrs.max.browser.controlpanel import IMAXUISettings
from mrs.max.utilities import IMAXClient
from ulearn.core import _
from ulearn.core.interfaces import IDXFileFactory
from ulearn.core.interfaces import IDocumentFolder
from ulearn.core.interfaces import IEventsFolder
from ulearn.core.interfaces import ILinksFolder
from ulearn.core.interfaces import IPhotosFolder
from ulearn.core.interfaces import IDiscussionFolder

import json
import mimetypes
import logging

logger = logging.getLogger(__name__)


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

    community_type = schema.Choice(
        title=_(u"Tipus de comunitat"),
        description=_(u"community_type_description"),
        source=availableCommunityTypes,
        required=True,
        default=u'Closed'
    )

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


class Community(Container):
    implements(ICommunity)

    def add_subscription(self, username, role):
        if role == 'readers':
            self.readers = list(set(self.readers + [username, ]))
        if role == 'subscribed':
            self.subscribed = list(set(self.subscribed + [username, ]))
        if role == 'owners':
            self.owners = list(set(self.owners + [username, ]))

    def remove_subscription(self, username, role):
        if role == 'readers':
            self.readers = list(set(self.readers) - set([username, ]))
        if role == 'subscribed':
            self.subscribed = list(set(self.subscribed) - set([username, ]))
        if role == 'owners':
            self.owners = list(set(self.owners) - set([username, ]))

    def get_max_client(self):
        maxclient, settings = getUtility(IMAXClient)()
        maxclient.setActor(settings.max_restricted_username)
        maxclient.setToken(settings.max_restricted_token)

        return maxclient

    def _get_max_subscribed_to_context(self):
        """ Get subscribed users from MAX """
        portal = getSite()
        wrapped_community = self.__of__(portal)
        # print('Getting subscribed users for {}'.format(wrapped_community.absolute_url()))
        return [user.get('username', '') for user in self.get_max_client().contexts[wrapped_community.absolute_url()].subscriptions.get(qs={'limit': 0})]

    def _intersect_subscribed_users_by_role(self):
        """ We assume that the default user role assignment will be editor
            otherwise noted. So try to map each of the other roles (reader,
            owner) and if not matched, then assign them to the default (editor)
        """
        request = getRequest()

        key = 'cache-subscribed-{}'.format(self.id)

        cache = IAnnotations(request)
        subscribed = cache.get(key, None)
        if not subscribed:
            subscribed = self._get_max_subscribed_to_context()
            cache[key] = subscribed

        readers = []
        editors = []
        owners = []

        for user in subscribed:
            if user in self._readers:
                readers.append(user)
            if user in self._owners:
                owners.append(user)
            if user in self._editors:
                editors.append(user)

        return dict(readers=readers, editors=editors, owners=owners)

    def clear_subscribed_cache(self):
        request = getRequest()
        key = 'cache-subscribed-{}'.format(self.id)

        cache = IAnnotations(request)
        subscribed = cache.get(key, None)
        if subscribed:
            del cache[key]

    def create_max_context(self):
        # Determine the kind of security the community should have provided the type
        # of community
        if self._ctype == u'Open':
            community_permissions = dict(read='subscribed', write='subscribed', subscribe='public', unsubscribe='public')
        elif self._ctype == u'Closed':
            community_permissions = dict(read='subscribed', write='restricted', subscribe='restricted', unsubscribe='public')
        elif self._ctype == u'Organizative':
            community_permissions = dict(read='subscribed', write='restricted', subscribe='restricted', unsubscribe='restricted')

        if not getattr(self, 'notify_activity_via_push', False):
            notify_push = False
        else:
            notify_push = self.notify_activity_via_push

        if not getattr(self, 'notify_activity_via_push_comments_too', False):
            notify_push_comments = False
        else:
            notify_push_comments = self.notify_activity_via_push_comments_too

        # Determine the value for notifications
        if notify_push and notify_push_comments:
            notifications = 'comments'
        elif notify_push and not notify_push_comments:
            notifications = 'posts'
        elif not notify_push and not notify_push_comments:
            notifications = False

        portal = getSite()
        wrapped_community = self.__of__(portal)

        # Add context for the community on MAX server
        self.get_max_client().contexts.post(
            url=wrapped_community.absolute_url(),
            displayName=self.title,
            permissions=community_permissions,
            notifications=notifications,
        )

    def subscribe_max_user_per_role(self, user, permission):
        portal = getSite()
        wrapped_community = self.__of__(portal)
        maxclient = self.get_max_client()

        if not getattr(portal, self.id, False):
            self.create_max_context()

        maxclient.people[user].subscriptions.post(object_url=wrapped_community.absolute_url())
        maxclient.contexts[wrapped_community.absolute_url()].permissions[user][permission].put()
        if permission == 'read':
            # Make sure the user only gets the read permission by unset the write one
            # This is the case of the permission roaming user...
            maxclient.contexts[wrapped_community.absolute_url()].permissions[user][permission].delete()

    def unsubscribe_user(self, user):
        portal = getSite()
        wrapped_community = self.__of__(portal)
        maxclient = self.get_max_client()
        maxclient.people[user].subscriptions[wrapped_community.absolute_url()].delete()

    def set_plone_permissions(self, user, role):
        if role == 'reader':
            self.manage_setLocalRoles(user, ['Reader', ])

        if role == 'editor':
            self.manage_setLocalRoles(user, ['Reader', 'Contributor', 'Editor'])

        if role == 'owner':
            self.manage_setLocalRoles(user, ['Reader', 'Contributor', 'Editor', 'Owner'])

    def unset_plone_permissions(self, user):
        self.manage_delLocalRoles([user, ])

    _ctype = FieldProperty(ICommunity['community_type'])

    _readers = FieldProperty(ICommunity['readers'])

    def get_readers(self):
        return self._intersect_subscribed_users_by_role()['readers']

    def set_readers(self, value):
        # print u'\nreader setter: {}'.format(value)
        subscribe = set(value) - set(self._readers)
        for user in subscribe:
            # print u'\nreaders subscribing: {}'.format(user)
            self.subscribe_max_user_per_role(user, 'read')
            self.clear_subscribed_cache()
            self.set_plone_permissions(user, 'reader')
        unsubscribe = set(self._readers) - set(value)
        for user in unsubscribe:
            if user not in self._editors and \
               user not in self._owners:
                # print u'\nreaders unsubscribing: {}'.format(user)
                self.unsubscribe_user(user)
                self.clear_subscribed_cache()
                self.unset_plone_permissions(user)
        self._readers = value

    readers = property(get_readers, set_readers)

    _editors = FieldProperty(ICommunity['subscribed'])

    def get_editors(self):
        return self._intersect_subscribed_users_by_role()['editors']

    def set_editors(self, value):
        # print u'\neditors setter: {}'.format(value)
        subscribe = set(value) - set(self._editors)
        for user in subscribe:
            # print u'\neditors subscribing: {}'.format(user)
            self.subscribe_max_user_per_role(user, 'write')
            self.clear_subscribed_cache()
            self.set_plone_permissions(user, 'editor')
        unsubscribe = set(self._editors) - set(value)
        for user in unsubscribe:
            if user not in self._readers and \
               user not in self._owners:
                # print u'\neditors unsubscribing: {}'.format(user)
                self.unsubscribe_user(user)
                self.clear_subscribed_cache()
                self.unset_plone_permissions(user)
        self._editors = value

    subscribed = property(get_editors, set_editors)

    _owners = FieldProperty(ICommunity['owners'])

    def get_owners(self):
        return self._intersect_subscribed_users_by_role()['owners']

    def set_owners(self, value):
        # print u'\nowners setter: {}'.format(value)
        subscribe = set(value) - set(self._owners)
        for user in subscribe:
            # print u'\nowners subscribing: {}'.format(user)
            self.subscribe_max_user_per_role(user, 'write')
            self.clear_subscribed_cache()
            self.set_plone_permissions(user, 'owner')
        unsubscribe = set(self._owners) - set(value)
        for user in unsubscribe:
            if user not in self._readers and \
               user not in self._editors:
                # print u'\nowners unsubscribing: {}'.format(user)
                self.unsubscribe_user(user)
                self.clear_subscribed_cache()
                self.unset_plone_permissions(user)
        self._owners = value

    owners = property(get_owners, set_owners)


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
        pm = getToolByName(self.context, "portal_membership")
        current_user = pm.getAuthenticatedMember().getUserName()
        if self.context.community_type == 'Open' and \
           current_user in self.context.readers and \
           current_user not in self.context.owners and \
           current_user not in self.context.subscribed:
            return True
        else:
            return False


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
    grok.context(ICommunity)
    grok.name('toggle-favorite')

    def render(self):
        pm = getToolByName(self.context, "portal_membership")
        current_user = pm.getAuthenticatedMember().getUserName()
        if current_user in IFavorite(self.context).get():
            IFavorite(self.context).remove(current_user)
        else:
            IFavorite(self.context).add(current_user)
        return "Toggled"


class ToggleSubscribe(grok.View):
    """ Toggle subscription in an Open or Closed community. """

    grok.context(ICommunity)
    grok.name('toggle-subscribe')

    def render(self):
        community = self.context
        pm = getToolByName(self.context, "portal_membership")
        current_user = pm.getAuthenticatedMember().getUserName()

        if community.community_type == u'Open' or community.community_type == u'Closed':
            if self.user_is_subscribed(current_user, community):
                self.remove_user_from_subscriptions(current_user, community)
                if current_user in IFavorite(community).get():
                    IFavorite(community).remove(current_user)
            else:
                community.add_subscription(unicode(current_user), 'subscribed')

            community.reindexObject()
            notify(ObjectModifiedEvent(community))
            return True

        elif community.community_type == u'Organizative':
            # Bad, bad guy... You shouldn't been trying this...
            return False

    def user_is_subscribed(self, user, community):
        return user in community.readers + community.subscribed + community.owners

    def remove_user_from_subscriptions(self, user, community):
        if user in community.readers:
            community.readers.remove(user)
            community.remove_subscription(unicode(user), 'readers')
        if user in community.subscribed:
            community.remove_subscription(unicode(user), 'subscribed')
        if user in community.owners:
            community.remove_subscription(unicode(user), 'owners')


class UpgradeSubscribe(grok.View):
    """ Upgrade subscription from reader to editor in an open community. """

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

    @button.buttonAndHandler(_(u'Crea la comunitat'), name="save")
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        # Handle order here. For now, just print it to the console. A more
        # realistic action would be to send the order to another system, send
        # an email, or similar

        nom = data['title']
        description = data['description']
        readers = data['readers']
        subscribed = data['subscribed']
        owners = data['owners']
        image = data['image']
        community_type = data['community_type']
        twitter_hashtag = data['twitter_hashtag']
        notify_activity_via_push = data['notify_activity_via_push']
        notify_activity_via_push_comments_too = data['notify_activity_via_push_comments_too']

        portal = getSite()
        pc = getToolByName(portal, 'portal_catalog')

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
            # Just to be safe in some corner cases, we set the current user as
            # owner of the community in this point
            owners = list(set(owners + [unicode(api.user.get_current().id.encode('utf-8'))]))

            new_comunitat_id = self.context.invokeFactory(
                'ulearn.community',
                id_normalized,
                title=nom,
                description=description,
                readers=readers,
                subscribed=subscribed,
                owners=owners,
                image=image,
                community_type=community_type,
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

    def update(self):
        super(communityEdit, self).update()
        self.actions['save'].addClass('context')

    def updateWidgets(self):
        super(communityEdit, self).updateWidgets()

        self.widgets["title"].value = self.context.title
        self.widgets["description"].value = self.context.description
        self.widgets["community_type"].value = [self.ctype_map[self.context.community_type]]
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
    registry = queryUtility(IRegistry)
    maxui_settings = registry.forInterface(IMAXUISettings)

    maxclient = MaxClient(maxui_settings.max_server, maxui_settings.oauth_server)
    maxclient.setActor(maxui_settings.max_restricted_username)
    maxclient.setToken(maxui_settings.max_restricted_token)

    # Fallback for some rare cases when we arrive at this point and the MAX
    # context is not created. This happens when the community has been created
    # using the default Dexterity machinery.
    try:
        maxclient.contexts[community.absolute_url()].get()
    except:
        create_max_context(community)

    # Add creator to owners field - Not making use of .append() to force the setter
    community.owners = list(set(community.owners + [unicode(community.Creator().encode('utf-8'))]))

    # # Determine the value for notifications
    # if community.notify_activity_via_push and community.notify_activity_via_push_comments_too:
    #     notifications = 'comments'
    # elif community.notify_activity_via_push and not community.notify_activity_via_push_comments_too:
    #     notifications = 'posts'
    # elif not community.notify_activity_via_push and not community.notify_activity_via_push_comments_too:
    #     notifications = False

    # # Determine the kind of security the community should have provided the type
    # # of community
    # if community.community_type == u'Open':
    #     community_permissions = dict(read='subscribed', write='subscribed', subscribe='public')
    # elif community.community_type == u'Closed':
    #     community_permissions = dict(read='subscribed', write='restricted', subscribe='restricted', unsubscribe='public')
    # elif community.community_type == u'Organizative':
    #     community_permissions = dict(read='subscribed', write='restricted', subscribe='restricted')

    # # Add context for the community on MAX server
    # maxclient.contexts.post(
    #     url=community.absolute_url(),
    #     displayName=community.title,
    #     permissions=community_permissions,
    #     notifications=community.notify_activity_via_push,
    # )

    # Update twitter hashtag
    maxclient.contexts[community.absolute_url()].put(
        twitterHashtag=community.twitter_hashtag
    )

    # Update community tag
    maxclient.contexts[community.absolute_url()].tags.put(data=['[COMMUNITY]'])

    # Subscribe the invited users and grant them permission
    # for reader in community.readers:
    #     maxclient.people[reader].subscriptions.post(object_url=community.absolute_url())
    #     maxclient.contexts[community.absolute_url()].permissions[reader]['read'].put()
    # for writter in community.subscribed:
    #     maxclient.people[writter].subscriptions.post(object_url=community.absolute_url())
    #     maxclient.contexts[community.absolute_url()].permissions[writter]['write'].put()
    # for owner in community.owners:
    #     maxclient.people[owner].subscriptions.post(object_url=community.absolute_url())
    #     maxclient.contexts[community.absolute_url()].permissions[owner]['write'].put()

    # Auto-favorite the creator user to this community
    IFavorite(community).add(community.Creator())

    # Change workflow to intranet
    # portal_workflow = getToolByName(community, 'portal_workflow')
    # portal_workflow.doActionFor(community, 'publishtointranet')

    # Disable Inheritance
    community.__ac_local_roles_block__ = True

    # Set uLearn permissions
    for reader in community.readers:
        community.manage_setLocalRoles(reader, ['Reader'])

    for writter in community.subscribed:
        community.manage_setLocalRoles(writter, ['Reader', 'Contributor', 'Editor'])

    for owner in community.owners:
        community.manage_setLocalRoles(owner, ['Reader', 'Contributor', 'Editor', 'Owner'])

    # If the community is of the type "Open", then allow any auth user to see it
    if community.community_type == u'Open':
        community.manage_setLocalRoles('AuthenticatedUsers', ['Reader'])

    # Create default content containers
    documents = createContentInContainer(community, 'Folder', title='documents', checkConstraints=False)
    links = createContentInContainer(community, 'Folder', title='links', checkConstraints=False)
    photos = createContentInContainer(community, 'Folder', title='media', checkConstraints=False)

    # Set the correct title, translated
    documents.setTitle(community.translate(_(u"Documents")))
    links.setTitle(community.translate(_(u"Enllaços")))
    photos.setTitle(community.translate(_(u"Media")))

    # Create the default events container and set title
    events = createContentInContainer(community, 'Folder', title='events', checkConstraints=False)
    events.setTitle(community.translate(_(u"Esdeveniments")))

    # Create the default discussion container and set title
    discussion = createContentInContainer(community, 'Folder', title='discussion', checkConstraints=False)
    discussion.setTitle(community.translate(_(u"Discussion")))

    # Set default view layout
    documents.setLayout('folder_summary_view')
    links.setLayout('folder_summary_view')
    photos.setLayout('folder_summary_view')
    events.setLayout('folder_summary_view')
    discussion.setLayout('discussion_folder_view')

    # Mark them with a marker interface
    alsoProvides(documents, IDocumentFolder)
    alsoProvides(links, ILinksFolder)
    alsoProvides(photos, IPhotosFolder)
    alsoProvides(events, IEventsFolder)
    alsoProvides(discussion, IDiscussionFolder)

    # Set on them the allowable content types
    behavior = ISelectableConstrainTypes(documents)
    behavior.setConstrainTypesMode(1)
    behavior.setLocallyAllowedTypes(('Document', 'File', 'Folder'))
    behavior.setImmediatelyAddableTypes(('Document', 'File', 'Folder'))
    behavior = ISelectableConstrainTypes(links)
    behavior.setConstrainTypesMode(1)
    behavior.setLocallyAllowedTypes(('Link', 'Folder'))
    behavior.setImmediatelyAddableTypes(('Link', 'Folder'))
    behavior = ISelectableConstrainTypes(photos)
    behavior.setConstrainTypesMode(1)
    behavior.setLocallyAllowedTypes(('Image', 'Folder'))
    behavior.setImmediatelyAddableTypes(('Image', 'Folder'))
    behavior = ISelectableConstrainTypes(events)
    behavior.setConstrainTypesMode(1)
    behavior.setLocallyAllowedTypes(('Event', 'Folder'))
    behavior.setImmediatelyAddableTypes(('Event', 'Folder'))
    behavior = ISelectableConstrainTypes(discussion)
    behavior.setConstrainTypesMode(1)
    behavior.setLocallyAllowedTypes(('ulearn.discussion', 'Folder'))
    behavior.setImmediatelyAddableTypes(('ulearn.discussion', 'Folder'))

    # Change workflow to intranet ** no longer needed
    # portal_workflow.doActionFor(documents, 'publishtointranet')
    # portal_workflow.doActionFor(links, 'publishtointranet')
    # portal_workflow.doActionFor(photos, 'publishtointranet')

    # Add portlets programatically
    # target_manager = queryUtility(IPortletManager, name='plone.leftcolumn', context=community)
    # target_manager_assignments = getMultiAdapter((community, target_manager), IPortletAssignmentMapping)
    # from ulearn.theme.portlets.profile import Assignment as profileAssignment
    # from ulearn.theme.portlets.thinnkers import Assignment as thinnkersAssignment
    # from ulearn.theme.portlets.communities import Assignment as communitiesAssignment
    # from ulearn.theme.portlets.stats import Assignment as statsAssignment
    # from plone.app.portlets.portlets.navigation import Assignment as navigationAssignment
    # target_manager_assignments['profile'] = profileAssignment()
    # target_manager_assignments['navigation'] = navigationAssignment(root=u'/{}'.format(community.id))
    # target_manager_assignments['communities'] = communitiesAssignment()
    # target_manager_assignments['thinnkers'] = thinnkersAssignment()
    # target_manager_assignments['stats'] = statsAssignment()

    # Blacklist the right column portlets on documents
    right_manager = queryUtility(IPortletManager, name=u"plone.rightcolumn")
    blacklist = getMultiAdapter((documents, right_manager), ILocalPortletAssignmentManager)
    blacklist.setBlacklistStatus(CONTEXT_CATEGORY, True)

    # Blacklist the right column portlets on photos
    right_manager = queryUtility(IPortletManager, name=u"plone.rightcolumn")
    blacklist = getMultiAdapter((photos, right_manager), ILocalPortletAssignmentManager)
    blacklist.setBlacklistStatus(CONTEXT_CATEGORY, True)

    # Blacklist the right column portlets on links
    right_manager = queryUtility(IPortletManager, name=u"plone.rightcolumn")
    blacklist = getMultiAdapter((links, right_manager), ILocalPortletAssignmentManager)
    blacklist.setBlacklistStatus(CONTEXT_CATEGORY, True)

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
    links.reindexObject()
    photos.reindexObject()
    events.reindexObject()
    discussion.reindexObject()

    # Mark community as initialitzated, to avoid  previous
    # folder creations to trigger modify event
    alsoProvides(community, IInitializedCommunity)


@grok.subscribe(ICommunity, IObjectModifiedEvent)
def edit_community(community, event):
    # Skip community modification if community is in creation state
    if not IInitializedCommunity.providedBy(community):
        return

    registry = queryUtility(IRegistry)
    maxui_settings = registry.forInterface(IMAXUISettings)

    maxclient = MaxClient(maxui_settings.max_server, maxui_settings.oauth_server)
    maxclient.setActor(maxui_settings.max_restricted_username)
    maxclient.setToken(maxui_settings.max_restricted_token)

    # Get current MAX context information
    context_current_info = maxclient.contexts[community.absolute_url()].get()

    # Determine the kind of security the community should have provided the type
    # of community
    if community.community_type == u'Open':
        community_permissions = dict(read='subscribed', write='subscribed', subscribe='public', unsubscribe='public')
    elif community.community_type == u'Closed':
        community_permissions = dict(read='subscribed', write='restricted', subscribe='restricted', unsubscribe='public')
    elif community.community_type == u'Organizative':
        community_permissions = dict(read='subscribed', write='restricted', subscribe='restricted', unsubscribe='restricted')

    # collect updated properties
    properties_to_update = {}
    if context_current_info:
        if context_current_info.get('twitterHashtag', None) != community.twitter_hashtag:
            properties_to_update['twitterHashtag'] = community.twitter_hashtag

        if context_current_info.get('permissions', '') != community_permissions:
            properties_to_update['permissions'] = community_permissions

        if context_current_info.get('displayName', '') != community.title:
            properties_to_update['displayName'] = community.title

        # Determine the value for notifications
        if community.notify_activity_via_push and community.notify_activity_via_push_comments_too:
            notifications = 'comments'
        elif community.notify_activity_via_push and not community.notify_activity_via_push_comments_too:
            notifications = 'posts'
        elif not community.notify_activity_via_push and not community.notify_activity_via_push_comments_too:
            notifications = False

        if context_current_info.get('notifications', '') != notifications:
            properties_to_update['notifications'] = notifications

    # update context properties that have changed
    if properties_to_update:
        maxclient.contexts[community.absolute_url()].put(**properties_to_update)

    # Update/Subscribe the invited users and grant them permission on MAX
    # Guard in case that the user does not exist or the community does not exist
    # for reader in community.readers:
    #     try:
    #         maxclient.people[reader].subscriptions.post(object_url=community.absolute_url())
    #         maxclient.contexts[community.absolute_url()].permissions[reader]['read'].put()
    #     except:
    #         logger.error('Impossible to subscribe user {} as reader in the {} community.'.format(reader, community.absolute_url()))

    # for writter in community.subscribed:
    #     try:
    #         maxclient.people[writter].subscriptions.post(object_url=community.absolute_url())
    #         maxclient.contexts[community.absolute_url()].permissions[writter]['write'].put()
    #     except:
    #         logger.error('Impossible to subscribe user {} as editor in the {} community.'.format(writter, community.absolute_url()))

    # for owner in community.owners:
    #     try:
    #         maxclient.people[owner].subscriptions.post(object_url=community.absolute_url())
    #         maxclient.contexts[community.absolute_url()].permissions[owner]['write'].put()
    #     except:
    #         logger.error('Impossible to subscribe user {} as owner in the {} community.'.format(owner, community.absolute_url()))

    # If the community is of the type "Open", then allow any auth user to see it
    if community.community_type == u'Open':
        community.manage_setLocalRoles('AuthenticatedUsers', ['Reader'])
    elif community.community_type == u'Closed':
        community.manage_delLocalRoles(['AuthenticatedUsers'])

    # Update subscribed user permissions on uLearn
    # for reader in community.readers:
    #     community.manage_setLocalRoles(reader, ['Reader'])

    # for writter in community.subscribed:
    #     community.manage_setLocalRoles(writter, ['Reader', 'Contributor', 'Editor'])

    # for owner in community.owners:
    #     community.manage_setLocalRoles(owner, ['Reader', 'Contributor', 'Editor', 'Owner'])

    # Unsubscribe no longer members from community
    # all_subscribers = list(set(community.readers + community.subscribed + community.owners))
    # Normalize to lower case all uLearn users
    # all_subscribers = [b.lower() for b in all_subscribers]
    # subscribed = [user.get('username', '') for user in maxclient.contexts[community.absolute_url()].subscriptions.get(qs={'limit': 0})]
    # unsubscribe = [a for a in subscribed if a not in all_subscribers]

    # for user in unsubscribe:
    #     maxclient.people[user].subscriptions[community.absolute_url()].delete()

    # Update unsubscribed user permissions
    # community.manage_delLocalRoles(unsubscribe)

    # Reindex all operations in object
    community.reindexObject()
    community.reindexObjectSecurity()


@grok.subscribe(ICommunity, IObjectRemovedEvent)
def delete_community(community, event):
    registry = queryUtility(IRegistry)
    maxui_settings = registry.forInterface(IMAXUISettings)

    maxclient = MaxClient(maxui_settings.max_server, maxui_settings.oauth_server)
    maxclient.setActor(maxui_settings.max_restricted_username)
    maxclient.setToken(maxui_settings.max_restricted_token)

    maxclient.contexts[event.object.absolute_url()].delete()


def create_max_context(community):
    maxclient, settings = getUtility(IMAXClient)()
    maxclient.setActor(settings.max_restricted_username)
    maxclient.setToken(settings.max_restricted_token)

    # Determine the value for notifications
    if community.notify_activity_via_push and community.notify_activity_via_push_comments_too:
        notifications = 'comments'
    elif community.notify_activity_via_push and not community.notify_activity_via_push_comments_too:
        notifications = 'posts'
    elif not community.notify_activity_via_push and not community.notify_activity_via_push_comments_too:
        notifications = False

    # Determine the kind of security the community should have provided the type
    # of community
    if community.community_type == u'Open':
        community_permissions = dict(read='subscribed', write='subscribed', subscribe='public', unsubscribe='public')
    elif community.community_type == u'Closed':
        community_permissions = dict(read='subscribed', write='restricted', subscribe='restricted', unsubscribe='public')
    elif community.community_type == u'Organizative':
        community_permissions = dict(read='subscribed', write='restricted', subscribe='restricted', unsubscribe='restricted')

    # Add context for the community on MAX server
    maxclient.contexts.post(
        url=community.absolute_url(),
        displayName=community.title,
        permissions=community_permissions,
        notifications=notifications,
    )

    # Update/Subscribe the invited users and grant them permission on MAX
    # Guard in case that the user does not exist or the community does not exist
    for reader in community.readers:
        try:
            maxclient.people[reader].subscriptions.post(object_url=community.absolute_url())
            maxclient.contexts[community.absolute_url()].permissions[reader]['read'].put()
        except:
            logger.error('Impossible to subscribe user {} as reader in the {} community.'.format(reader, community.absolute_url()))

    for writter in community.subscribed:
        try:
            maxclient.people[writter].subscriptions.post(object_url=community.absolute_url())
            maxclient.contexts[community.absolute_url()].permissions[writter]['write'].put()
        except:
            logger.error('Impossible to subscribe user {} as editor in the {} community.'.format(writter, community.absolute_url()))

    for owner in community.owners:
        try:
            maxclient.people[owner].subscriptions.post(object_url=community.absolute_url())
            maxclient.contexts[community.absolute_url()].permissions[owner]['write'].put()
        except:
            logger.error('Impossible to subscribe user {} as owner in the {} community.'.format(owner, community.absolute_url()))
