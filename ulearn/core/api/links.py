# -*- coding: utf-8 -*-
from five import grok
from Products.CMFPlone.interfaces import IPloneSiteRoot
from plone import api
from ulearn.core.api import ApiResponse
from ulearn.core.api import REST
from ulearn.core.api import api_resource
from ulearn.core.api.root import APIRoot
from zope.component import getUtility
from plone.registry.interfaces import IRegistry
from ulearn.core.controlpanel import IUlearnControlPanelSettings


class Links(REST):
    """
        /api/links

        GET params username, language


    """

    grok.adapts(APIRoot, IPloneSiteRoot)
    grok.require('genweb.authenticated')

    @api_resource(required=['username', 'language'])
    def GET(self):
        """ Return the links from fixed gestion folder and ControlPanel """
        username = self.params['username']
        language = self.params['language']
        portal = api.portal.get()
        path = portal['gestion']['menu'][language]  # fixed en code... always in this path
        folders = api.content.find(context=path, depth=1)
        results = {}
        # Links from gestion folder
        for folder in folders:
            results[folder.Title] = []
            menufolder = folder.getObject().items()
            for item in menufolder:
                menuLink = dict(remote=item[1].remoteUrl,
                                title=item[1].title,
                                )
                results[folder.Title].append(menuLink)

        registry = getUtility(IRegistry)
        settings = registry.forInterface(IUlearnControlPanelSettings, check=False)

        results2 = []
        # Links from controlpanel
        if settings.quicklinks_table is not None:
            for item in settings.quicklinks_table:
                quickLink = dict(title=item['text'],
                                 remote=item['link'],
                                 icon=item['icon']
                                 )
            results2.append(quickLink)
        values = {'menu_gestion': results, 'menu_carpetas': results2}

        return ApiResponse(values)
