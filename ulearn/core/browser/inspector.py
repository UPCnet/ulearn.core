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
from Products.PloneLDAP.factory import manage_addPloneLDAPMultiPlugin
from Products.LDAPUserFolder.LDAPUserFolder import LDAPUserFolder
from Products.PluggableAuthService.interfaces.plugins import IUserAdderPlugin
from Products.PlonePAS.interfaces.group import IGroupManagement

from genweb.portlets.browser.manager import ISpanStorage

import inspect
import importlib

MODULES_TO_INSPECT = ['ulearn.core.browser.setup', 'ulearn.core.browser.migrations']


class clouseau(grok.View):
    grok.context(IPloneSiteRoot)

    def get_templates(self):
        portal = getSite()

        urls = []

        for module in MODULES_TO_INSPECT:
            themodule = importlib.import_module(module)
            members = inspect.getmembers(themodule, inspect.isclass)

            for name, klass in members:
                if grok.View in klass.__bases__:
                    urls.append('{}/{}'.format(portal.absolute_url(), name.lower()))

        return urls
