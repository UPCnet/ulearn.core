# -*- coding: utf-8 -*-
from five import grok
from zope.component import getUtility
from zope.component import queryUtility
from zope.component.hooks import getSite
from zope.interface import Interface

from plone import api

from ulearn.theme.browser.interfaces import IUlearnTheme

from genweb.core.utilities import IElasticSearch

import json


class IElasticSharing(Interface):
    """ Marker for ElasticSharingglobal utility """


class ElasticSharing(object):
    grok.implements(IElasticSharing)

    def __init__(self):
        try:
            self.elastic = getUtility(IElasticSearch)
        except:
            pass

    def shared_with(self, username):
        """
            Returns a list of all items shared with a specific user
        """
        results = [
            dict(
                title='Document de prova',
                url='http://www.upc.edu',
                community_displayname='La meva comunitat',
                community_url='http://community_url',
                by='Carles Bruguera',
                by_profile='http://profile/'
            ),
            dict(
                title='Document de prova 2',
                url='http://www.upc.edu',
                community_displayname='La meva comunitat 2',
                community_url='http://community_url',
                description='Descripció del contingut bla bla bla.',
                by='Carles Bruguera',
                by_profile='http://profile/'
            )
        ]

        return results

grok.global_utility(ElasticSharing)


class SharedWithMe(grok.View):
    grok.context(Interface)
    grok.name('shared_with_me')
    grok.require('genweb.authenticated')
    grok.layer(IUlearnTheme)

    def render(self):
        """
            AJAX view to access shared items of the current logged in user
        """
        self.request.response.setHeader('Content-type', 'application/json')
        results = []
        sharing = queryUtility(IElasticSharing)
        username = api.user.get_current().id
        portal = getSite()
        results = sharing.shared_with(username)
        return json.dumps(results)
