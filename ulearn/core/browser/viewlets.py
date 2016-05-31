from five import grok
from hashlib import sha1
from plone import api
from Acquisition import aq_inner
from zope.interface import Interface
from zope.component.hooks import getSite
from zope.security import checkPermission
from plone.app.layout.viewlets.interfaces import IPortalHeader

from genweb.core.gwuuid import IGWUUID
from ulearn.core.content.community import ICommunity
from ulearn.core import _
from Acquisition import aq_chain

from plone.app.contenttypes.interfaces import INewsItem
from plone.app.layout.viewlets.interfaces import IAboveContentTitle
from plone.memoize.view import memoize_contextless
from Products.CMFCore.utils import getToolByName
from genweb.core.adapters import IImportant
from genweb.core.adapters import IFlash
from genweb.core.adapters import IOutOfList
from genweb.core.utils import genweb_config
from ulearn.theme.browser.interfaces import IUlearnTheme
from souper.soup import get_soup
from repoze.catalog.query import Eq
import json


class CommunityNGDirective(grok.Viewlet):
    grok.context(Interface)
    grok.name('ulearn.communityngdirective')
    grok.viewletmanager(IPortalHeader)

    def update(self):
        self.community_hash = ''
        self.community_gwuuid = ''
        self.community_url = ''
        self.community_type = ''
        for obj in aq_chain(self.context):
            if ICommunity.providedBy(obj):
                self.community_hash = sha1(obj.absolute_url()).hexdigest()
                self.community_gwuuid = IGWUUID(obj).get()
                self.community_url = obj.absolute_url()
                self.community_type = obj.community_type


class ULearnNGDirectives(grok.Viewlet):
    grok.context(Interface)
    grok.name('ulearn.ulearnngdirectives')
    grok.viewletmanager(IPortalHeader)
    grok.layer(IUlearnTheme)

    def get_communities(self):
        """ Gets the communities to show in the stats selectize dropdown
        """
        pc = api.portal.get_tool('portal_catalog')
        all_communities = [{'hash': 'all', 'title': _(u'Todas las comunidades')}]
        all_communities += [{'hash': community.community_hash, 'title': community.Title} for community in pc.searchResults(portal_type='ulearn.community')]
        return json.dumps(all_communities)

    def show_extended(self):
        """ This attribute from the directive is used to show special buttons or
            links in the stats tabs. This is common in client packages.
        """
        return api.portal.get_registry_record(name='ulearn.core.controlpanel.IUlearnControlPanelSettings.stats_button')


class viewletBase(grok.Viewlet):
    grok.baseclass()

    @memoize_contextless
    def portal_url(self):
        return self.portal().absolute_url()

    @memoize_contextless
    def portal(self):
        return getSite()

    def genweb_config(self):
        return genweb_config()

    def pref_lang(self):
        """ Extracts the current language for the current user
        """
        lt = getToolByName(self.portal(), 'portal_languages')
        return lt.getPreferredLanguage()


class importantNews(viewletBase):
    grok.name('genweb.important')
    grok.context(INewsItem)
    grok.template('important')
    grok.viewletmanager(IAboveContentTitle)
    grok.require('cmf.ModifyPortalContent')
    grok.layer(IUlearnTheme)

    def permisos_important(self):
        # TODO: Comprovar que l'usuari tingui permisos per a marcar com a important
        return not IImportant(self.context).is_important and checkPermission("plone.app.controlpanel.Overview", self.portal())

    def permisos_notimportant(self):
        # TODO: Comprovar que l'usuari tingui permisos per a marcar com a notimportant
        return IImportant(self.context).is_important and checkPermission("plone.app.controlpanel.Overview", self.portal())

    def isNewImportant(self):
        context = aq_inner(self.context)
        is_important = IImportant(context).is_important
        return is_important


class FlashNews(viewletBase):
    grok.name('genweb.flash')
    grok.context(INewsItem)
    grok.template('flash')
    grok.viewletmanager(IAboveContentTitle)
    grok.require('cmf.ModifyPortalContent')
    grok.layer(IUlearnTheme)

    def permisos_flash(self):
        # TODO: Comprovar que l'usuari tingui permisos per a marcar com a important
        return not IFlash(self.context).is_flash and checkPermission("plone.app.controlpanel.Overview", self.portal())

    def permisos_notflash(self):
        # TODO: Comprovar que l'usuari tingui permisos per a marcar com a notimportant
        return IFlash(self.context).is_flash and checkPermission("plone.app.controlpanel.Overview", self.portal())

    def isNewFlash(self):
        context = aq_inner(self.context)
        is_flash = IFlash(context).is_flash
        return is_flash


class OutOfListNews(viewletBase):
    grok.name('genweb.outoflist')
    grok.context(INewsItem)
    grok.template('outoflist')
    grok.viewletmanager(IAboveContentTitle)
    grok.require('cmf.ModifyPortalContent')
    grok.layer(IUlearnTheme)

    def permisos_outoflist(self):
        # TODO: Comprovar que l'usuari tingui permisos per a marcar com a important
        return not IOutOfList(self.context).is_outoflist and checkPermission("plone.app.controlpanel.Overview", self.portal())

    def permisos_notoutoflist(self):
        # TODO: Comprovar que l'usuari tingui permisos per a marcar com a notimportant
        return IOutOfList(self.context).is_outoflist and checkPermission("plone.app.controlpanel.Overview", self.portal())

    def isNewOutOfList(self):
        context = aq_inner(self.context)
        is_outoflist = IOutOfList(context).is_outoflist
        return is_outoflist


class ListTagsNews(viewletBase):
    grok.name('genweb.listtags')
    grok.context(INewsItem)
    grok.template('listtags')
    grok.viewletmanager(IAboveContentTitle)
    grok.require('genweb.authenticated')
    grok.layer(IUlearnTheme)

    def isTagFollowed(self, category):
        portal = getSite()
        current_user = api.user.get_current()
        userid = current_user.id

        soup_tags = get_soup('user_subscribed_tags', portal)
        tags_soup = [r for r in soup_tags.query(Eq('id', userid))]
        if tags_soup:
            tags = tags_soup[0].attrs['tags']
            return True if category in tags else False
        else:
            return False
