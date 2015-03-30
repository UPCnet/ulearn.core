import json
import urllib2
import requests
from five import grok
from plone import api
from AccessControl import getSecurityManager
from Products.Five.browser import BrowserView
# from zope.interface import Interface
from zope.component import getMultiAdapter, queryUtility
from zope.i18nmessageid import MessageFactory
from zope.component.hooks import getSite
from zope.component import getUtility
from plone.memoize import ram
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName

from ulearn.core.controlpanel import IUlearnControlPanelSettings


class ulearnUtils(BrowserView):
    """ Convenience methods placeholder ulearn.utils view. """

    def portal(self):
        return api.portal.get()

    def get_url_forget_password(self,context):
        """ return redirect url when forget user password """
        portal = getToolByName(context, 'portal_url').getPortalObject()
        base_path = '/'.join(portal.getPhysicalPath())
        registry = queryUtility(IRegistry)
        settings = registry.forInterface(IUlearnControlPanelSettings)
        if 'http' in settings.url_forget_password:
        	return settings.url_forget_password
        else:
        	return base_path + settings.url_forget_password