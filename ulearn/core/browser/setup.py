from five import grok
from Acquisition import aq_parent
from Acquisition import aq_inner
from zope.component import queryUtility
from zope.component import getUtility
from zope.component import getMultiAdapter
from zope.component.hooks import getSite

from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import IPortletAssignmentMapping

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.PluggableAuthService.interfaces.plugins import IUserAdderPlugin
from Products.PlonePAS.interfaces.group import IGroupManagement

from genweb.portlets.browser.manager import ISpanStorage

import pkg_resources

try:
    pkg_resources.get_distribution('Products.PloneLDAP')
except pkg_resources.DistributionNotFound:
    HAS_LDAP = False
else:
    HAS_LDAP = True
    from Products.PloneLDAP.factory import manage_addPloneLDAPMultiPlugin
    from Products.LDAPUserFolder.LDAPUserFolder import LDAPUserFolder


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


class setupLDAPExterns(grok.View):
    grok.context(IPloneSiteRoot)
    grok.require('zope2.ViewManagementScreens')

    def render(self):
        portal = getSite()

        # Delete the LDAPUPC if exists
        if getattr(portal.acl_users, 'ldapUPC', None):
            portal.acl_users.manage_delObjects('ldapUPC')

        # try:
        manage_addPloneLDAPMultiPlugin(portal.acl_users, "ldapexterns",
            title="ldapexterns", use_ssl=1, login_attr="cn", uid_attr="cn", local_groups=0,
            users_base="ou=users,ou=upcnet,dc=upcnet,dc=es", users_scope=2,
            roles="Authenticated,Member", groups_base="ou=groups,ou=upcnet,dc=upcnet,dc=es",
            groups_scope=2, read_only=True, binduid="cn=ldap,ou=upcnet,dc=upcnet,dc=es", bindpwd="conldapnexio",
            rdn_attr="cn", LDAP_server="fajolpetit.upcnet.es", encryption="SSHA")
        portal.acl_users.ldapexterns.acl_users.manage_edit("ldapexterns", "cn", "cn", "ou=users,ou=upcnet,dc=upcnet,dc=es", 2, "Authenticated,Member",
            "ou=groups,ou=upcnet,dc=upcnet,dc=es", 2, "cn=ldap,ou=upcnet,dc=upcnet,dc=es", "conldapnexio", 1, "cn",
            "top,person,inetOrgPerson", 0, 0, "SSHA", 0, '')

        plugin = portal.acl_users['ldapexterns']

        # Activate plugins (all)
        plugin.manage_activateInterfaces(['IAuthenticationPlugin',
                                          'ICredentialsResetPlugin',
                                          'IGroupEnumerationPlugin',
                                          'IGroupIntrospection',
                                          'IGroupManagement',
                                          'IGroupsPlugin',
                                          'IPropertiesPlugin',
                                          'IRoleEnumerationPlugin',
                                          'IRolesPlugin',
                                          'IUserAdderPlugin',
                                          'IUserEnumerationPlugin',
                                          'IUserManagement'])

        # In case to have more than one server for fault tolerance
        #LDAPUserFolder.manage_addServer(portal.acl_users.ldapUPC.acl_users, "ldap.upc.edu", '636', use_ssl=1)

        # Redefine some schema properties
        LDAPUserFolder.manage_deleteLDAPSchemaItems(portal.acl_users.ldapexterns.acl_users, ldap_names=['sn'], REQUEST=None)
        LDAPUserFolder.manage_deleteLDAPSchemaItems(portal.acl_users.ldapexterns.acl_users, ldap_names=['cn'], REQUEST=None)
        LDAPUserFolder.manage_addLDAPSchemaItem(portal.acl_users.ldapexterns.acl_users, ldap_name='sn', friendly_name='Last Name', public_name='fullname')
        LDAPUserFolder.manage_addLDAPSchemaItem(portal.acl_users.ldapexterns.acl_users, ldap_name='cn', friendly_name='Canonical Name')

        # Update the preference of the plugins
        portal.acl_users.plugins.movePluginsUp(IUserAdderPlugin, ['ldapexterns'])
        portal.acl_users.plugins.movePluginsUp(IGroupManagement, ['ldapexterns'])

        # Move the ldapUPC to the top of the active plugins.
        # Otherwise member.getProperty('email') won't work properly.
        # from Products.PluggableAuthService.interfaces.plugins import IPropertiesPlugin
        # portal.acl_users.plugins.movePluginsUp(IPropertiesPlugin, ['ldapUPC'])
        #portal.acl_users.plugins.manage_movePluginsUp('IPropertiesPlugin', ['ldapUPC'], context.REQUEST.RESPONSE)
        # except:
        #     pass

        return 'Done.'


class ldapkillah(grok.View):
    grok.context(IPloneSiteRoot)
    grok.require('zope2.ViewManagementScreens')

    def render(self):
        portal = getSite()

        if getattr(portal.acl_users, 'ldapUPC', None):
            portal.acl_users.manage_delObjects('ldapUPC')

        if getattr(portal.acl_users, 'ldapexterns', None):
            portal.acl_users.manage_delObjects('ldapexterns')
