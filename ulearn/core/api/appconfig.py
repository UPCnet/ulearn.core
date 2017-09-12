# -*- coding: utf-8 -*-
from five import grok
from Products.CMFPlone.interfaces import IPloneSiteRoot
from ulearn.core.api import ApiResponse
from ulearn.core.api import REST
from ulearn.core.api.root import APIRoot
from plone import api


class Appconfig(REST):
    """
        /api/appconfig

        http://localhost:8090/Plone/api/appconfig

    """

    grok.adapts(APIRoot, IPloneSiteRoot)
    grok.require('genweb.authenticated')

    def GET(self):
        portal = api.portal.get()
        results = portal

        return ApiResponse(results)
