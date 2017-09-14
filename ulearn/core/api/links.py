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
from ulearn.core.api import ObjectNotFound


class Links(REST):
    """
        /api/links
    """
    placeholder_type = 'link'
    placeholder_id = 'language'

    grok.adapts(APIRoot, IPloneSiteRoot)
    grok.require('genweb.authenticated')


class Link(REST):
    """
        /api/links/{language}

        http://localhost:8090/Plone/api/links/es

    """
    grok.adapts(Links, IPloneSiteRoot)
    grok.require('genweb.authenticated')

    @api_resource(required=['language'])
    def GET(self):
        """ Return the links from Menu Gestion folder and Menu ControlPanel """
        language = self.params['language']
        portal = api.portal.get()
        try:
            path = portal['gestion']['menu'][language]  # fixed en code... always in this path
            folders = api.content.find(context=path, depth=1)

            # Links from gestion folder
            resultsGestion = {}
            for folder in folders:
                resultsGestion[folder.Title] = []
                menufolder = folder.getObject().items()
                for item in menufolder:
                    menuLink = dict(url=item[1].remoteUrl,
                                    title=item[1].title,
                                    )
                    resultsGestion[folder.Title].append(menuLink)

            registry = getUtility(IRegistry)
            settings = registry.forInterface(IUlearnControlPanelSettings, check=False)

            # Links from controlpanel
            resultsControlPanel = []
            if settings.quicklinks_table is not None:
                for item in settings.quicklinks_table:
                    quickLink = dict(title=item['text'],
                                     url=item['link'],
                                     icon=item['icon']
                                     )
                resultsControlPanel.append(quickLink)
            values = {'Menu_Gestion': resultsGestion, 'Menu_Controlpanel': resultsControlPanel}

            return ApiResponse(values)
        except:
            raise ObjectNotFound('Language not configured in this Site.')
