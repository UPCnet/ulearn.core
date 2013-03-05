# -*- coding: utf-8 -*-
from zope.component import adapter
from zope.component import queryUtility
from zope.component.hooks import getSite

from plone.registry.interfaces import IRegistry
from plone.app.controlpanel.interfaces import IConfigurationChangedEvent

from Products.CMFCore.utils import getToolByName

from maxclient import MaxClient
from mrs.max.browser.controlpanel import IMAXUISettings


def Added(content, event):
    """ MAX hooks main handler
    """
    portal = getSite()
    pm = getToolByName(portal, "portal_membership")
    if pm.isAnonymousUser():  # the user has not logged in
        username = ''
        return
    else:
        member = pm.getAuthenticatedMember()

    registry = queryUtility(IRegistry)
    settings = registry.forInterface(IMAXUISettings, check=False)
    max_url = settings.max_server

    username = member.getUserName()
    memberdata = pm.getMemberById(username)
    oauth_token = memberdata.getProperty('oauth_token', None)

    import ipdb;ipdb.set_trace()
    community = content.newParent.absolute_url()

    maxcli = MaxClient(max_url, actor=username, auth_method='oauth2')
    maxcli.setOAuth2Auth(oauth_token, oauth2_scope='widgetcli')

    articles = dict(File=u'un', Image=u'una', Link=u'un')

    tipus = dict(File=u'document', Image=u'foto', Link=u'enllaç')

    parts = dict(type=tipus.get(content.portal_type, ''),
                 name=content.Title(),
                 link=content.absolute_url(),
                 un=articles.get(content.portal_type, 'un'))

    activity_text = u'He afegit %(un)s %(type)s "%(name)s" a %(link)s' % parts

    maxcli.addActivity(activity_text, contexts=[community, ])


@adapter(IConfigurationChangedEvent)
def updateMAXUserInfo(event):
    """Subscriber que s'executa cada cop que canvien les preferencies d'usuari"""
    site = getSite()
    pm = getToolByName(site, "portal_membership")
    if pm.isAnonymousUser():  # the user has not logged in
        username = ''
        return
    else:
        member = pm.getAuthenticatedMember()

    username = member.getUserName()
    memberdata = pm.getMemberById(username)
    properties = dict(displayName=memberdata.getProperty('fullname', None))

    registry = queryUtility(IRegistry)
    settings = registry.forInterface(IMAXUISettings, check=False)
    max_url = settings.max_server

    oauth_token = memberdata.getProperty('oauth_token', None)
    maxcli = MaxClient(max_url, actor=username, auth_method='oauth2')
    maxcli.setOAuth2Auth(oauth_token, oauth2_scope='widgetcli')

    maxcli.modifyUser(username, properties)
