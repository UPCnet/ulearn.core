# -*- coding: utf-8 -*-
from five import grok
from Products.CMFPlone.interfaces import IPloneSiteRoot
from plone import api
from ulearn.core.api import ApiResponse
from ulearn.core.api import REST
from ulearn.core.api import api_resource
from ulearn.core.api.root import APIRoot
import requests


class Appconfig(REST):
    """
        /api/appconfig

    """
    grok.adapts(APIRoot, IPloneSiteRoot)
    grok.require('genweb.authenticated')

    @api_resource(required=[])
    def GET(self):
        main_color = api.portal.get_registry_record(name='ulearn.core.controlpanel.IUlearnControlPanelSettings.main_color')
        secondary_color = api.portal.get_registry_record(name='ulearn.core.controlpanel.IUlearnControlPanelSettings.secondary_color')
        max_server = api.portal.get_registry_record(name='mrs.max.browser.controlpanel.IMAXUISettings.max_server')
        max_server_alias = api.portal.get_registry_record(name='mrs.max.browser.controlpanel.IMAXUISettings.max_server_alias')
        hub_server = api.portal.get_registry_record(name='mrs.max.browser.controlpanel.IMAXUISettings.hub_server')
        domain = api.portal.get_registry_record(name='mrs.max.browser.controlpanel.IMAXUISettings.domain')
        oauth_server = max_server + '/info'

        session = requests.Session()
        resp = session.get(oauth_server)
        max_oauth_server = resp.json()['max.oauth_server']

        show_news_in_app = api.portal.get_registry_record(name='ulearn.core.controlpanel.IUlearnControlPanelSettings.show_news_in_app')

        info = dict(main_color=main_color,
                    secondary_color=secondary_color,
                    max_server=max_server,
                    max_server_alias=max_server_alias,
                    hub_server=hub_server,
                    domain=domain,
                    oauth_server=oauth_server,
                    max_oauth_server=max_oauth_server,
                    show_news_in_app=show_news_in_app
                    )
        return ApiResponse(info)
