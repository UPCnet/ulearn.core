# -*- coding: utf-8 -*-
from hashlib import sha1

from five import grok
from zope import schema
from z3c.form import button
from zope.event import notify
from zope.component import queryUtility
from zope.interface import alsoProvides
from zope.security import checkPermission
from zope.component import getMultiAdapter
from zope.component.hooks import getSite
from zope.lifecycleevent import ObjectModifiedEvent
from zope.app.container.interfaces import IObjectAddedEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from zope.lifecycleevent.interfaces import IObjectRemovedEvent
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleVocabulary
from AccessControl import getSecurityManager
from AccessControl import Unauthorized

from plone.indexer import indexer
from plone.directives import form
from plone.memoize.view import memoize_contextless
from plone.namedfile.field import NamedBlobImage
from plone.portlets.constants import CONTEXT_CATEGORY
from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import IPortletAssignmentMapping
from plone.portlets.interfaces import ILocalPortletAssignmentManager
from plone.z3cform.textlines.textlines import TextLinesConverter
from plone.registry.interfaces import IRegistry
from plone.dexterity.utils import createContentInContainer

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.statusmessages.interfaces import IStatusMessage
from Products.CMFPlone.interfaces.constrains import ISelectableConstrainTypes

from genweb.core.adapters.favorites import IFavorite
from genweb.core.widgets.select2_user_widget import SelectWidgetConverter
from genweb.core.widgets.select2_user_widget import Select2UserInputFieldWidget

from maxclient import MaxClient
from mrs.max.browser.controlpanel import IMAXUISettings

from ulearn.core import _
from ulearn.core.interfaces import IDocumentFolder, ILinksFolder, IPhotosFolder, IEventsFolder

from wildcard.foldercontents.interfaces import IDXFileFactory
import json


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

    form.widget(readers=Select2UserInputFieldWidget)
    readers = schema.List(
        title=_(u"Readers"),
        description=_(u"Subscribed people with read-only permissions"),
        value_type=schema.TextLine(),
        required=False,
        missing_value=[],
        default=[])

    # We maintain the subscribed field for backwards compatibility,
    # understanding that it refers to users with read/write permissions
    form.widget(subscribed=Select2UserInputFieldWidget)
    subscribed = schema.List(
        title=_(u"Editors"),
        description=_(u"Subscribed people with editor permissions"),
        value_type=schema.TextLine(),
        required=False,
        missing_value=[],
        default=[])

    form.widget(owners=Select2UserInputFieldWidget)
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
           not current_user in self.context.owners and \
           not current_user in self.context.subscribed:
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
        if not 'multipart/form-data' in self.request['CONTENT_TYPE'] and \
           len(self.request.form.keys()) != 1:
            self.request.response.setHeader("Content-type", "application/json")
            self.request.response.setStatus(400)
            return json.dumps({"Error": "Not supported upload method"})

        file_key = self.request.form.keys()[0]
        input_file = self.request.form[file_key]
        filename = input_file.filename

        ctr = getToolByName(self.context, 'content_type_registry')
        type_ = ctr.findTypeName(filename.lower(), '', '') or 'File'
        if type_ == 'File':
            container = self.get_documents_folder()
        else:
            container = self.get_images_folder()

        content_type = input_file.headers['content-type']
        factory = IDXFileFactory(container)

        try:
            factory(filename, content_type, input_file)
        except Unauthorized:
            self.request.response.setHeader("Content-type", "application/json")
            self.request.response.setStatus(401)
            return json.dumps({"Error": "Unauthorized"})
        finally:
            self.request.response.setStatus(201)


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
                community.subscribed.append(current_user)

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
        if user in community.subscribed:
            community.subscribed.remove(user)
        if user in community.owners:
            community.owners.remove(user)


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
                community.readers.remove(current_user)
                community.subscribed.append(current_user)
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

        portal = getSite()
        pc = getToolByName(portal, 'portal_catalog')
        result = pc.unrestrictedSearchResults(portal_type='ulearn.community', Title=nom)

        if result:
            msgid = _(u"comunitat_existeix", default=u'La comunitat ${comunitat} ja existeix, si us plau, escolliu un altre nom.', mapping={u"comunitat": nom})

            translated = self.context.translate(msgid)

            messages = IStatusMessage(self.request)
            messages.addStatusMessage(translated, type="info")

            self.request.response.redirect('{}/++add++ulearn.community'.format(portal.absolute_url()))
        else:
            new_comunitat = createContentInContainer(
                self.context,
                'ulearn.community',
                title=nom,
                description=description,
                readers=readers,
                subscribed=subscribed,
                owners=owners,
                image=image,
                community_type=community_type,
                twitter_hashtag=twitter_hashtag,
                checkConstraints=False)

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

    # Add creator to owners field
    community.owners.append(community.Creator())

    # Determine the kind of security the community should have provided the type
    # of community
    if community.community_type == u'Open':
        community_permissions = dict(read='subscribed', write='subscribed', subscribe='public')
    elif community.community_type == u'Closed':
        community_permissions = dict(read='subscribed', write='restricted', subscribe='restricted', unsubscribe='public')
    elif community.community_type == u'Organizative':
        community_permissions = dict(read='subscribed', write='restricted', subscribe='restricted')

    # Add context for the community on MAX server
    maxclient.addContext(community.absolute_url(),
                         community.title,
                         community_permissions
                         )

    # Update twitter hashtag
    maxclient.modifyContext(community.absolute_url(),
                            dict(twitterHashtag=community.twitter_hashtag))

    # Update community tag
    maxclient.add_tags_to_context(community.absolute_url(), ['[COMMUNITY]'])

    # Subscribe the invited users and grant them permission
    for reader in community.readers:
        maxclient.subscribe(url=community.absolute_url(), username=reader)
        maxclient.grant_permission(url=community.absolute_url(), username=reader, permission='read')
    for writter in community.subscribed:
        maxclient.subscribe(url=community.absolute_url(), username=writter)
        maxclient.grant_permission(url=community.absolute_url(), username=writter, permission='write')
    for owner in community.owners:
        maxclient.subscribe(url=community.absolute_url(), username=owner)
        maxclient.grant_permission(url=community.absolute_url(), username=owner, permission='write')

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
    photos.setTitle(community.translate(_(u"Fotos")))

    # Create the default events container and set title
    events = createContentInContainer(community, 'Folder', title='events', checkConstraints=False)
    events.setTitle(community.translate(_(u"Esdeveniments")))

    # Set default view layout
    documents.setLayout('folder_summary_view')
    links.setLayout('folder_summary_view')
    photos.setLayout('folder_summary_view')
    events.setLayout('folder_summary_view')

    # Mark them with a marker interface
    alsoProvides(documents, IDocumentFolder)
    alsoProvides(links, ILinksFolder)
    alsoProvides(photos, IPhotosFolder)
    alsoProvides(events, IEventsFolder)

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

    # Reindex all created objects
    community.reindexObject()
    documents.reindexObject()
    links.reindexObject()
    photos.reindexObject()
    events.reindexObject()


@grok.subscribe(ICommunity, IObjectModifiedEvent)
def edit_community(community, event):
    registry = queryUtility(IRegistry)
    maxui_settings = registry.forInterface(IMAXUISettings)

    maxclient = MaxClient(maxui_settings.max_server, maxui_settings.oauth_server)
    maxclient.setActor(maxui_settings.max_restricted_username)
    maxclient.setToken(maxui_settings.max_restricted_token)

    # Get current MAX context information
    context_current_info = maxclient.get_context(url=community.absolute_url())

    if context_current_info:
        if context_current_info.get('twitterHashtag', None) != community.twitter_hashtag:
            # Update twitter hashtag
            maxclient.modifyContext(community.absolute_url(),
                                    dict(twitterHashtag=community.twitter_hashtag))

    # Determine the kind of security the community should have provided the type
    # of community
    if community.community_type == u'Open':
        community_permissions = dict(read='subscribed', write='subscribed', subscribe='public')
    elif community.community_type == u'Closed':
        community_permissions = dict(read='subscribed', write='restricted', subscribe='restricted', unsubscribe='public')
    elif community.community_type == u'Organizative':
        community_permissions = dict(read='subscribed', write='restricted', subscribe='restricted')

    if context_current_info:
        if context_current_info.get('permissions', '') != community_permissions:
            # Update community permissions on MAX
            maxclient.modifyContext(community.absolute_url(),
                                    dict(permissions=community_permissions))

    # Update/Subscribe the invited users and grant them permission on MAX
    for reader in community.readers:
        maxclient.subscribe(url=community.absolute_url(), username=reader)
        maxclient.grant_permission(url=community.absolute_url(), username=reader, permission='read')
    for writter in community.subscribed:
        maxclient.subscribe(url=community.absolute_url(), username=writter)
        maxclient.grant_permission(url=community.absolute_url(), username=writter, permission='write')
    for owner in community.owners:
        maxclient.subscribe(url=community.absolute_url(), username=owner)
        maxclient.grant_permission(url=community.absolute_url(), username=owner, permission='write')

    # If the community is of the type "Open", then allow any auth user to see it
    if community.community_type == u'Open':
        community.manage_setLocalRoles('AuthenticatedUsers', ['Reader'])
    elif community.community_type == u'Closed':
        community.manage_delLocalRoles(['AuthenticatedUsers'])

    # Update subscribed user permissions on uLearn
    for reader in community.readers:
        community.manage_setLocalRoles(reader, ['Reader'])

    for writter in community.subscribed:
        community.manage_setLocalRoles(writter, ['Reader', 'Contributor', 'Editor'])

    for owner in community.owners:
        community.manage_setLocalRoles(owner, ['Reader', 'Contributor', 'Editor', 'Owner'])

    # Unsubscribe no longer members from community
    all_subscribers = list(set(community.readers + community.subscribed + community.owners))
    subscribed = [user.get('username', '') for user in maxclient.subscribed_to_context(community.absolute_url())]
    unsubscribe = [a for a in subscribed if a not in all_subscribers]

    for user in unsubscribe:
        maxclient.unsubscribe(url=community.absolute_url(), username=user)

    # Update unsubscribed user permissions
    community.manage_delLocalRoles(unsubscribe)

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

    maxclient.deleteContext(event.object.absolute_url())
