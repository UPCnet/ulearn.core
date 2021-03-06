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
from genweb.core.adapters import IShowInApp
from genweb.core.utils import genweb_config
from ulearn.theme.browser.interfaces import IUlearnTheme
from souper.soup import get_soup
from repoze.catalog.query import Eq
import json
from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import IPortletAssignmentMapping
from zope.component import getUtility, getMultiAdapter


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


class newsToolBar(viewletBase):
    grok.name('ulearn.newstoolbar')
    grok.context(INewsItem)
    grok.template('newstoolbar')
    grok.viewletmanager(IAboveContentTitle)
    grok.layer(IUlearnTheme)
    grok.require('cmf.ModifyPortalContent')

    def canManageSite(self):
        return checkPermission("plone.app.controlpanel.Overview", self.portal())

    def permisos_important(self):
        # TODO: Comprovar que l'usuari tingui permisos per a marcar com a important
        return not IImportant(self.context).is_important and checkPermission("plone.app.controlpanel.Overview", self.portal())

    def permisos_notimportant(self):
        # TODO: Comprovar que l'usuari tingui permisos per a marcar com a notimportant
        return IImportant(self.context).is_important and checkPermission("plone.app.controlpanel.Overview", self.portal())

    def isNewImportant(self):
        context = aq_inner(self.context)
        return IImportant(context).is_important

    def permisos_flash(self):
        # TODO: Comprovar que l'usuari tingui permisos per a marcar com a important
        return not IFlash(self.context).is_flash and checkPermission("plone.app.controlpanel.Overview", self.portal())

    def permisos_notflash(self):
        # TODO: Comprovar que l'usuari tingui permisos per a marcar com a notimportant
        return IFlash(self.context).is_flash and checkPermission("plone.app.controlpanel.Overview", self.portal())

    def isNewFlash(self):
        context = aq_inner(self.context)
        return IFlash(context).is_flash

    def permisos_outoflist(self):
        # TODO: Comprovar que l'usuari tingui permisos per a marcar com a important
        return not IOutOfList(self.context).is_outoflist and checkPermission("plone.app.controlpanel.Overview", self.portal())

    def permisos_notoutoflist(self):
        # TODO: Comprovar que l'usuari tingui permisos per a marcar com a notimportant
        return IOutOfList(self.context).is_outoflist and checkPermission("plone.app.controlpanel.Overview", self.portal())

    def isNewOutOfList(self):
        context = aq_inner(self.context)
        return IOutOfList(context).is_outoflist

    def isNewApp(self):
        context = aq_inner(self.context)
        return IShowInApp(context).is_inapp

    def getListOfPortlets(self):
        site = getSite()
        active_portlets = []
        portlets_slots = ["plone.leftcolumn", "plone.rightcolumn",
                          "genweb.portlets.HomePortletManager1", "genweb.portlets.HomePortletManager2",
                          "genweb.portlets.HomePortletManager3", "genweb.portlets.HomePortletManager4",
                          "genweb.portlets.HomePortletManager5", "genweb.portlets.HomePortletManager6",
                          "genweb.portlets.HomePortletManager7", "genweb.portlets.HomePortletManager8",
                          "genweb.portlets.HomePortletManager9", "genweb.portlets.HomePortletManager10"]

        for manager_name in portlets_slots:
            if 'genweb' in manager_name:
                manager = getUtility(IPortletManager, name=manager_name, context=site['front-page'])
                mapping = getMultiAdapter((site['front-page'], manager), IPortletAssignmentMapping)
                [active_portlets.append(item[0]) for item in mapping.items()]
            else:
                manager = getUtility(IPortletManager, name=manager_name, context=site)
                mapping = getMultiAdapter((site, manager), IPortletAssignmentMapping)
                [active_portlets.append(item[0]) for item in mapping.items()]
        return active_portlets

    def isPortletListActivate(self):
        active_portlets = self.getListOfPortlets()
        show_news = api.portal.get_registry_record(
            name='ulearn.core.controlpanel.IUlearnControlPanelSettings.activate_news')
        return True if ('my-subscribed-news' in active_portlets) or show_news else False

    def isPortletFlashActivate(self):
        active_portlets = self.getListOfPortlets()
        return True if 'flashesinformativos' in active_portlets else False

    def isPortletImportantActivate(self):
        active_portlets = self.getListOfPortlets()
        return True if 'importantnews' in active_portlets else False

    def isViewInAppChecked(self):
        show_news_in_app = api.portal.get_registry_record(
            name='ulearn.core.controlpanel.IUlearnControlPanelSettings.show_news_in_app')
        return show_news_in_app

    def isManagementNewsActivate(self):
        active_portlets = self.getListOfPortlets()
        if 'my-subscribed-news' in active_portlets or 'flashesinformativos' in active_portlets or 'importantnews' in active_portlets or self.isViewInAppChecked():
            return True
        else:
            return False


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
