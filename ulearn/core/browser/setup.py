from five import grok
from zope.component import queryUtility
from zope.component import getUtility
from zope.component import getMultiAdapter
from zope.component.hooks import getSite

from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import IPortletAssignmentMapping
from plone.dexterity.utils import createContentInContainer

from Products.CMFPlone.interfaces import IPloneSiteRoot

from genweb.portlets.browser.manager import ISpanStorage


class setupHomePage(grok.View):
    grok.context(IPloneSiteRoot)
    grok.require('zope2.ViewManagementScreens')

    def render(self):
        portal = getSite()
        frontpage = portal['front-page']
        # Add portlets programatically
        target_manager = queryUtility(IPortletManager, name='genweb.portlets.HomePortletManager1', context=frontpage)
        target_manager_assignments = getMultiAdapter((frontpage, target_manager), IPortletAssignmentMapping)
        from ulearn.theme.portlets.profile import Assignment as profileAssignment
        from ulearn.theme.portlets.communities import Assignment as communitiesAssignment
        from ulearn.theme.portlets.thinnkers import Assignment as thinnkersAssignment
        from mrs.max.portlets.maxui import Assignment as maxAssignment
        from ulearn.theme.portlets.homebuttonbar import Assignment as homebuttonbarAssignment
        from ulearn.theme.portlets.calendar import Assignment as calendarAssignment
        from ulearn.theme.portlets.stats import Assignment as statsAssignment
        from ulearn.theme.portlets.econnect import Assignment as econnectAssignment

        target_manager_assignments['profile'] = profileAssignment()
        target_manager_assignments['communities'] = communitiesAssignment()
        target_manager_assignments['thinnkers'] = thinnkersAssignment()

        target_manager = queryUtility(IPortletManager, name='genweb.portlets.HomePortletManager3', context=frontpage)
        target_manager_assignments = getMultiAdapter((frontpage, target_manager), IPortletAssignmentMapping)
        target_manager_assignments['buttons'] = homebuttonbarAssignment()
        target_manager_assignments['max'] = maxAssignment()

        portletManager = getUtility(IPortletManager, 'genweb.portlets.HomePortletManager3')
        spanstorage = getMultiAdapter((frontpage, portletManager), ISpanStorage)
        spanstorage.span = '8'

        target_manager = queryUtility(IPortletManager, name='genweb.portlets.HomePortletManager4', context=frontpage)
        target_manager_assignments = getMultiAdapter((frontpage, target_manager), IPortletAssignmentMapping)
        target_manager_assignments['calendar'] = calendarAssignment()
        target_manager_assignments['stats'] = statsAssignment()
        target_manager_assignments['econnect'] = econnectAssignment()


class ldapkillah(grok.View):
    grok.context(IPloneSiteRoot)
    grok.require('zope2.ViewManagementScreens')

    def render(self):
        portal = getSite()

        if getattr(portal.acl_users, 'ldapUPC', None):
            portal.acl_users.manage_delObjects('ldapUPC')

        if getattr(portal.acl_users, 'ldapexterns', None):
            portal.acl_users.manage_delObjects('ldapexterns')


class memberFolderSetup(grok.View):
    grok.context(IPloneSiteRoot)
    grok.require('zope2.ViewManagementScreens')

    def render(self):
        portal = getSite()
        if not getattr(portal, 'users', None):
            users_folder = createContentInContainer(portal, 'Folder', title='users', checkConstraints=False)
            users_folder.setDefaultPage('member_search_form')
            portal.manage_delObjects('Members')
