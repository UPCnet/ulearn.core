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

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone import api
from zope.interface import alsoProvides
from mrs.max.utilities import IMAXClient
from ulearn.core.api.people import Person
from genweb.core.utils import remove_user_from_catalog
from repoze.catalog.query import Eq
from souper.soup import get_soup
from genweb.core.gwuuid import IGWUUID
from ulearn.core.browser.security import execute_under_special_role

import logging
logger = logging.getLogger(__name__)



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
        from ulearn.theme.portlets.angularrouteview import Assignment as angularrouteviewAssignment

        target_manager_assignments['profile'] = profileAssignment()
        target_manager_assignments['communities'] = communitiesAssignment()
        target_manager_assignments['thinnkers'] = thinnkersAssignment()

        target_manager = queryUtility(IPortletManager, name='genweb.portlets.HomePortletManager3', context=frontpage)
        target_manager_assignments = getMultiAdapter((frontpage, target_manager), IPortletAssignmentMapping)
        target_manager_assignments['angularroute'] = angularrouteviewAssignment()
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


class changeURLCommunities(grok.View):
    """ Aquesta vista canvia la url de les comunitats """
    grok.name('changeurlcommunities')
    grok.context(IPloneSiteRoot)

    render = ViewPageTemplateFile('views_templates/changeurlcommunities.pt')

    def update(self):
        try:
            from plone.protect.interfaces import IDisableCSRFProtection
            alsoProvides(self.request, IDisableCSRFProtection)
        except:
            pass
        if self.request.environ['REQUEST_METHOD'] == 'POST':
            pc = api.portal.get_tool('portal_catalog')
            communities = pc.searchResults(portal_type='ulearn.community')
            # portal_url = api.portal.get().absolute_url()

            if self.request.form['url'] != '':
                url_nova = self.request.form['url']
                url_antiga = self.request.form['url_antiga']
                self.context.plone_log('Buscant comunitats per modificar la url')

                for brain in communities:
                    obj = brain.getObject()
                    community = obj.adapted()
                    community_url = url_antiga + '/' + obj.id
                    community_url_nova = url_nova + '/' + obj.id
                    properties_to_update = dict(url=community_url_nova)

                    community.maxclient.contexts[community_url].put(**properties_to_update)
                    self.context.plone_log('Comunitat amb url {} actualitzada per {}'.format(community_url, community_url_nova))

class deleteUsers(grok.View):
    """ Delete users from the plone & max & communities """
    grok.name('deleteusers')
    grok.context(IPloneSiteRoot)

    render = ViewPageTemplateFile('views_templates/deleteusers.pt')

    def update(self):
        try:
            from plone.protect.interfaces import IDisableCSRFProtection
            alsoProvides(self.request, IDisableCSRFProtection)
        except:
            pass
        if self.request.environ['REQUEST_METHOD'] == 'POST':

            if self.request.form['users'] != '':
                users = self.request.form['users'].split(',')

                for user in users:
                    user = user.strip()
                    try:
                        person = Person(self.context, [user])
                        person.deleteMembers([user])
                        remove_user_from_catalog(user.lower())
                        pc = api.portal.get_tool(name='portal_catalog')
                        username = user
                        comunnities = pc.unrestrictedSearchResults(portal_type="ulearn.community")
                        for num, community in enumerate(comunnities):
                            obj = community._unrestrictedGetObject()
                            self.context.plone_log('Processant {} de {}. Comunitat {}'.format(num, len(comunnities), obj))
                            gwuuid = IGWUUID(obj).get()
                            portal = api.portal.get()
                            soup = get_soup('communities_acl', portal)

                            records = [r for r in soup.query(Eq('gwuuid', gwuuid))]

                            # Save ACL into the communities_acl soup
                            if records:
                                exist = [a for a in records[0].attrs['acl']['users'] if a['id'] == unicode(username)]
                                if exist:
                                    records[0].attrs['acl']['users'].remove(exist[0])
                                    soup.reindex(records=[records[0]])
                                    adapter = obj.adapted()
                                    adapter.set_plone_permissions(adapter.get_acl())

                        maxclient, settings = getUtility(IMAXClient)()
                        maxclient.setActor(settings.max_restricted_username)
                        maxclient.setToken(settings.max_restricted_token)
                        maxclient.people[username].delete()
                        logger.info('Delete user: {}'.format(user))
                    except:
                        logger.error('User not deleted: {}'.format(user))
                        pass

                logger.info('Finished deleted users: {}'.format(users))
