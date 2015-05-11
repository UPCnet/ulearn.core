# -*- coding: utf-8 -*-
from five import grok
from Acquisition import aq_chain
from zope.component import getUtility

from zope.component.hooks import getSite
from zope.app.container.interfaces import IObjectAddedEvent

from Products.CMFCore.utils import getToolByName

from ulearn.core.interfaces import IAppImage
from ulearn.core.interfaces import IAppFile
from ulearn.core.content.community import ICommunity

from mrs.max.utilities import IMAXClient

import logging

logger = logging.getLogger(__name__)

articles = {
    'ca': dict(File=u'un', Image=u'una', Link=u'un', Event=u'un'),
    'es': dict(File=u'un', Image=u'una', Link=u'un', Event=u'un'),
    'en': dict(File=u'a', Image=u'an', Link=u'a', Event=u'an'),
}

tipus = {
    'ca': dict(Document=u'document', File=u'document', Image=u'foto', Link=u'enllaç', Event=u'esdeveniment'),
    'es': dict(Document=u'documento', File=u'documento', Image=u'foto', Link=u'enlace', Event=u'evento'),
    'en': dict(Document=u'document', File=u'document', Image=u'photo', Link=u'link', Event=u'event'),
}


@grok.subscribe(ICommunity, IObjectAddedEvent)
def communityAdded(content, event):
    """ Community added handler
    """
    portal = getSite()
    pm = getToolByName(portal, 'portal_membership')
    pl = getToolByName(portal, 'portal_languages')
    default_lang = pl.getDefaultLanguage()

    if pm.isAnonymousUser():  # the user has not logged in
        username = ''
        return
    else:
        member = pm.getAuthenticatedMember()

    username = member.getUserName()
    memberdata = pm.getMemberById(username)
    oauth_token = memberdata.getProperty('oauth_token', None)

    maxclient, settings = getUtility(IMAXClient)()
    maxclient.setActor(username)
    maxclient.setToken(oauth_token)

    activity_text = {
        'ca': u'He creat una nova comunitat: {}',
        'es': u'He creado una comunidad nueva: {}',
        'en': u'I\'ve just created a new community: {}',
    }

    try:
        maxclient.people[username].activities.post(object_content=activity_text[default_lang].format(content.Title().decode('utf-8')), contexts=[dict(url=content.absolute_url(), objectType="context")])
    except:
        logger.warning('The username {} has been unable to post the default community creation message'.format(username))


def Added(content, event):
    """ MAX hooks main handler
    """
    portal = getSite()
    pm = getToolByName(portal, 'portal_membership')
    pl = getToolByName(portal, 'portal_languages')
    default_lang = pl.getDefaultLanguage()

    community = findContainerCommunity(content)

    if not community or \
       IAppFile.providedBy(content) or \
       IAppImage.providedBy(content):
        # For some reason the file we are creating is not inside a community
        # or the content is created externaly through apps via the upload ws
        return

    username, oauth_token = getUserOauthToken(pm)
    maxclient = connectMaxclient(username, oauth_token)

    parts = dict(type=tipus[default_lang].get(content.portal_type, ''),
                 name=content.Title().decode('utf-8') or getattr(getattr(content, 'file', u''), 'filename', u'').decode('utf-8') or getattr(getattr(content, 'image', u''), 'filename', u'').decode('utf-8'),
                 link='{}/view'.format(content.absolute_url()),
                 un=articles[default_lang].get(content.portal_type, 'un'))

    activity_text = {
        'ca': u'He afegit {un} {type} "{name}" a {link}',
        'es': u'He añadido {un} {type} "{name}" a {link}',
        'en': u'I\'ve added {un} {type} "{name}" a {link}',
    }

    if (content.portal_type == 'Image' or
       content.portal_type == 'File') and \
       content.description:
        activity_text = u'{} {}'.format(content.title, u'{}/view'.format(content.absolute_url()))

        try:
            maxclient.people[username].activities.post(object_content=activity_text, contexts=[dict(url=community.absolute_url(), objectType='context')])
        except:
            logger.warning('The username {} has been unable to post the default object creation message'.format(username))
    else:
        try:
            maxclient.people[username].activities.post(object_content=activity_text[default_lang].format(**parts), contexts=[dict(url=community.absolute_url(), objectType='context')])
        except:
            logger.warning('The username {} has been unable to post the default object creation message'.format(username))


def Modified(content, event):
    """ Max hooks modified handler """

    portal = getSite()
    pm = getToolByName(portal, 'portal_membership')
    pl = getToolByName(portal, 'portal_languages')
    default_lang = pl.getDefaultLanguage()

    community = findContainerCommunity(content)

    if not community or \
       IAppFile.providedBy(content) or \
       IAppImage.providedBy(content):
        # For some reason the file we are creating is not inside a community
        # or the content is created externaly through apps via the upload ws
        return

    username, oauth_token = getUserOauthToken(pm)
    maxclient = connectMaxclient(username, oauth_token)

    parts = dict(type=tipus[default_lang].get(content.portal_type, ''),
                 name=content.Title().decode('utf-8') or getattr(getattr(content, 'file', u''), 'filename', u'').decode('utf-8') or getattr(getattr(content, 'image', u''), 'filename', u'').decode('utf-8'),
                 link='{}/view'.format(content.absolute_url()),
                 un=articles[default_lang].get(content.portal_type, 'un'))

    activity_text = {
        'ca': u'He modificat {un} {type} "{name}" a {link}',
        'es': u'He modificado {un} {type} "{name}" a {link}',
        'en': u'I\'ve modified {un} {type} "{name}" a {link}',
    }

    if (content.portal_type == 'Image' or
       content.portal_type == 'File') and \
       content.description:
        activity_text = u'{} {}'.format(content.title, u'{}/view'.format(content.absolute_url()))

        try:
            maxclient.people[username].activities.post(object_content=activity_text, contexts=[dict(url=community.absolute_url(), objectType='context')])
        except:
            logger.warning('The username {} has been unable to post the default object creation message'.format(username))
    else:
        try:
            maxclient.people[username].activities.post(object_content=activity_text[default_lang].format(**parts), contexts=[dict(url=community.absolute_url(), objectType='context')])
        except:
            logger.warning('The username {} has been unable to post the default object creation message'.format(username))


def findContainerCommunity(content):
    for parent in aq_chain(content):
        if ICommunity.providedBy(parent):
            return parent

    return None


def getUserOauthToken(pm):
    if pm.isAnonymousUser():  # the user has not logged in
        username = ''
        return
    else:
        member = pm.getAuthenticatedMember()

    username = member.getUserName()
    memberdata = pm.getMemberById(username)
    oauth_token = memberdata.getProperty('oauth_token', None)

    return username, oauth_token


def connectMaxclient(username, oauth_token):
    maxclient, settings = getUtility(IMAXClient)()
    maxclient.setActor(username)
    maxclient.setToken(oauth_token)

    return maxclient
