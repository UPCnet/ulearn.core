# -*- coding: utf-8 -*-
from five import grok
from zope import schema
from zope.component import queryUtility
from zope.security import checkPermission
from zope.component import getMultiAdapter
from zope.app.container.interfaces import IObjectAddedEvent
from z3c.form import button

from plone.directives import form
from plone.namedfile.field import NamedBlobImage
from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import IPortletAssignmentMapping
from plone.z3cform.textlines.textlines import TextLinesConverter
from plone.z3cform.textlines.textlines import TextLinesFieldWidget
from plone.registry.interfaces import IRegistry
from plone.dexterity.utils import createContentInContainer

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.statusmessages.interfaces import IStatusMessage

from maxclient import MaxClient
from mrs.max.browser.controlpanel import IMAXUISettings

from ulearn.core import _


class ICommunity(form.Schema):
    """ A manageable community
    """

    title = schema.TextLine(
        title=_(u"Nom"),
        description=_(u"Nom de la comunitat"),
        required=True
    )

    form.widget(subscribed=TextLinesFieldWidget)
    subscribed = schema.List(
        title=_(u"Subscrits"),
        description=_(u"Llista amb les persones subscrites"),
        value_type=schema.TextLine(),
        required=False,
        missing_value=[])

    image = NamedBlobImage(
        title=_(u"Imatge"),
        description=_(u"Imatge que defineix la comunitat"),
        required=False,
    )


class View(grok.View):
    grok.context(ICommunity)

    def canEditCommunity(self):
        return checkPermission('cmf.RequestReview', self.context)


class communityAdder(form.SchemaForm):
    grok.name('addCommunity')
    grok.context(IPloneSiteRoot)
    grok.require('genweb.authenticated')

    schema = ICommunity
    ignoreContext = True

    @button.buttonAndHandler(_(u'Crea la comunitat'))
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        # Handle order here. For now, just print it to the console. A more
        # realistic action would be to send the order to another system, send
        # an email, or similar

        nom = data['title']
        subscribed = data['subscribed']
        image = data['image']

        new_comunitat = createContentInContainer(self.context, 'ulearn.community', title=nom, subscribed=subscribed, image=image, checkConstraints=False)

        # Redirect back to the front page with a status message

        IStatusMessage(self.request).addStatusMessage(
            "La comunitat {} ha estat creada.".format(nom),
            "info"
        )

        self.request.response.redirect(new_comunitat.absolute_url())


class communityEdit(form.SchemaForm):
    grok.name('editCommunity')
    grok.context(ICommunity)
    grok.require('cmf.ModifyPortalContent')

    schema = ICommunity
    ignoreContext = True

    def updateWidgets(self):
        super(communityEdit, self).updateWidgets()

        self.widgets["title"].value = self.context.title

        tlc = TextLinesConverter(self.fields['subscribed'].field, self.widgets["subscribed"])
        self.widgets["subscribed"].value = tlc.toWidgetValue(self.context.subscribed)

    @button.buttonAndHandler(_(u'Edita la comunitat'))
    def handleApply(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        nom = data['title']
        subscribed = data['subscribed']
        image = data['image']

        registry = queryUtility(IRegistry)
        maxui_settings = registry.forInterface(IMAXUISettings)

        maxclient = MaxClient(maxui_settings.max_server, maxui_settings.oauth_server)
        maxclient.setActor(maxui_settings.max_restricted_username)
        maxclient.setToken(maxui_settings.max_restricted_token)

        # Subscribe new usernames to the community
        for guest in subscribed:
            maxclient.subscribe(url=self.context.absolute_url(), username=guest)

        #unsubscribe = [a for a in self.context.subscribed if a not in subscribed]
        # Unsubscribe username from community

        # Set new values in community
        self.context.title = nom
        self.context.subscribed = subscribed
        self.context.image = image

        IStatusMessage(self.request).addStatusMessage(
            "La comunitat {} ha estat modificada.".format(nom),
            "info"
        )

        self.request.response.redirect(self.context.absolute_url())


@grok.subscribe(ICommunity, IObjectAddedEvent)
def initialize_community(community, event):
    registry = queryUtility(IRegistry)
    maxui_settings = registry.forInterface(IMAXUISettings)

    maxclient = MaxClient(maxui_settings.max_server, maxui_settings.oauth_server)
    maxclient.setActor(maxui_settings.max_restricted_username)
    maxclient.setToken(maxui_settings.max_restricted_token)

    # Add context for the community on MAX server
    maxclient.addContext(community.absolute_url(),
                         "Comunitat {}".format(community.title),
                         dict(read='subscribed', write='subscribed', join='restricted', invite='restricted')
                         )

    # Subscribe owner
    maxclient.subscribe(url=community.absolute_url(), username=community.Creator())

    # Subscribe the invited users
    for guest in community.subscribed:
        maxclient.subscribe(url=community.absolute_url(), username=guest)

    # Change workflow to intranet
    portal_workflow = getToolByName(community, 'portal_workflow')
    portal_workflow.doActionFor(community, 'publishtointranet')

    # Disable Inheritance
    community.__ac_local_roles_block__ = True

    # Set permissions
    for guest in community.subscribed:
        community.manage_setLocalRoles(guest, ['Reader', 'Editor', 'Contributor'])

    # Create default content
    documents = createContentInContainer(community, 'Folder', title=u"Documents", checkConstraints=False)
    enllacos = createContentInContainer(community, 'Folder', title=u"Enllaços", checkConstraints=False)
    fotos = createContentInContainer(community, 'Folder', title=u"Fotos", checkConstraints=False)

    # Change workflow to intranet
    portal_workflow.doActionFor(documents, 'publishtointranet')
    portal_workflow.doActionFor(enllacos, 'publishtointranet')
    portal_workflow.doActionFor(fotos, 'publishtointranet')

    # Add default portlets
    target_manager = queryUtility(IPortletManager, name='plone.leftcolumn', context=community)
    target_manager_assignments = getMultiAdapter((community, target_manager), IPortletAssignmentMapping)
    from ulearn.theme.portlets.profile import Assignment as profileAssignment
    from ulearn.theme.portlets.thinnkers import Assignment as thinnkersAssignment
    from ulearn.theme.portlets.communities import Assignment as communitiesAssignment
    from plone.app.portlets.portlets.navigation import Assignment as navigationAssignment
    target_manager_assignments['profile'] = profileAssignment()
    target_manager_assignments['navigation'] = navigationAssignment(root='/{}'.format(community.id))
    target_manager_assignments['communities'] = communitiesAssignment()
    target_manager_assignments['thinnkers'] = thinnkersAssignment()

    target_manager = queryUtility(IPortletManager, name='plone.rightcolumn', context=community)
    target_manager_assignments = getMultiAdapter((community, target_manager), IPortletAssignmentMapping)
    from ulearn.theme.portlets.calendar import Assignment as calendarAssignment
    from ulearn.theme.portlets.mostvalued import Assignment as mostvaluedAssignment
    from ulearn.theme.portlets.comments import Assignment as commentsAssignment
    target_manager_assignments['calendar'] = calendarAssignment()
    target_manager_assignments['mostvalued'] = mostvaluedAssignment()
    target_manager_assignments['comments'] = commentsAssignment()
