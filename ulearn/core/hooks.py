# -*- coding: utf-8 -*-
from five import grok
from Acquisition import aq_chain
from zope.component import queryUtility
from zope.component.hooks import getSite
from zope.app.container.interfaces import IObjectAddedEvent

from plone.registry.interfaces import IRegistry


from Products.CMFCore.utils import getToolByName

from maxclient import MaxClient
from ulearn.core.content.community import ICommunity
from mrs.max.browser.controlpanel import IMAXUISettings


@grok.subscribe(ICommunity, IObjectAddedEvent)
def communityAdded(content, event):
    """ Community added handler
    """
    portal = getSite()
    pm = getToolByName(portal, "portal_membership")
    pl = getToolByName(portal, "portal_languages")
    default_lang = pl.getDefaultLanguage()

    if pm.isAnonymousUser():  # the user has not logged in
        username = ''
        return
    else:
        member = pm.getAuthenticatedMember()

    registry = queryUtility(IRegistry)
    settings = registry.forInterface(IMAXUISettings, check=False)
    effective_grant_type = settings.oauth_grant_type

    username = member.getUserName()
    memberdata = pm.getMemberById(username)
    oauth_token = memberdata.getProperty('oauth_token', None)

    maxclient = MaxClient(url=settings.max_server, oauth_server=settings.oauth_server, grant_type=effective_grant_type)
    maxclient.setActor(username)
    maxclient.setToken(oauth_token)

    activity_text = {
        'ca': u'He creat una nova comunitat: {}',
        'es': u'He creado una comunidad nueva: {}',
        'en': u'I\'ve just created a new community: {}',
    }

    maxclient.addActivity(activity_text[default_lang].format(content.Title().decode('utf-8')), contexts=[content.absolute_url(), ])


def Added(content, event):
    """ MAX hooks main handler
    """
    portal = getSite()
    pm = getToolByName(portal, "portal_membership")
    pl = getToolByName(portal, "portal_languages")
    default_lang = pl.getDefaultLanguage()

    if pm.isAnonymousUser():  # the user has not logged in
        username = ''
        return
    else:
        member = pm.getAuthenticatedMember()

    registry = queryUtility(IRegistry)
    settings = registry.forInterface(IMAXUISettings, check=False)
    effective_grant_type = settings.oauth_grant_type

    username = member.getUserName()
    memberdata = pm.getMemberById(username)
    oauth_token = memberdata.getProperty('oauth_token', None)

    community = findContainerCommunity(content)

    if not community:
        # For some reason the file we are creating is not inside a community
        return

    maxclient = MaxClient(url=settings.max_server, oauth_server=settings.oauth_server, grant_type=effective_grant_type)
    maxclient.setActor(username)
    maxclient.setToken(oauth_token)

    articles = {
        'ca': dict(File=u'un', Image=u'una', Link=u'un'),
        'es': dict(File=u'un', Image=u'una', Link=u'un'),
        'en': dict(File=u'a', Image=u'an', Link=u'a'),
    }

    tipus = {
        'ca': dict(Document=u'document', File=u'document', Image=u'foto', Link=u'enllaç', Event=u'esdeveniment'),
        'es': dict(Document=u'documento', File=u'documento', Image=u'foto', Link=u'enlace', Event=u'evento'),
        'en': dict(Document=u'document', File=u'document', Image=u'photo', Link=u'link', Event=u'event'),
    }

    parts = dict(type=tipus[default_lang].get(content.portal_type, ''),
                 name=content.Title().decode('utf-8') or getattr(getattr(content, 'file', u''), 'filename', u'').decode('utf-8') or getattr(getattr(content, 'image', u''), 'filename', u'').decode('utf-8'),
                 link='{}/view'.format(content.absolute_url()),
                 un=articles[default_lang].get(content.portal_type, 'un'))

    activity_text = {
        'ca': u'He afegit {un} {type} "{name}" a {link}',
        'es': u'He añadido {un} {type} "{name}" a {link}',
        'en': u'I\'ve added {un} {type} "{name}" a {link}',
    }

    maxclient.addActivity(activity_text[default_lang].format(**parts), contexts=[community.absolute_url(), ])


def findContainerCommunity(content):
    for parent in aq_chain(content):
        if ICommunity.providedBy(parent):
            return parent

    return None
