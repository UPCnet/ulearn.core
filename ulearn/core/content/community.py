# -*- coding: utf-8 -*-
from five import grok
from zope import schema
from zope.component import queryUtility
from zope.app.container.interfaces import IObjectAddedEvent

from plone.directives import form, dexterity
from plone.app.textfield import RichText
from plone.z3cform.textlines.textlines import TextLinesFieldWidget
from plone.registry.interfaces import IRegistry
from plone.dexterity.utils import createContentInContainer

from Products.CMFCore.utils import getToolByName

from maxclient import MaxClient
from mrs.max.browser.controlpanel import IMAXUISettings

from ulearn.core import _


class ICommunity(form.Schema):
    """ A manageable community
    """

    title = schema.TextLine(
            title=_(u"Nom"),
            description=_(u"Nom de la comunitat"),
        )

    form.widget(subscribed=TextLinesFieldWidget)
    subscribed = schema.List(
            title=_(u"Subscrits"),
            description=_(u"Llista amb les persones subscrites"),
            value_type=schema.TextLine(),
            required=False,
            missing_value=[],
        )


class View(grok.View):
    grok.context(ICommunity)

    # def render(self):
    #     return "asdasd"


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
