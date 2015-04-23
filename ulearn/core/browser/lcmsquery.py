# -*- coding: utf-8 -*-
from five import grok
from zope.interface import Interface

from Products.CMFCore.utils import getToolByName
from ulearn.theme.browser.interfaces import IUlearnTheme

from zope.component.hooks import getSite
import json


class LCMSSearch(grok.View):
    # LCMS QUERY!
    # Used in Aquology Moodle Site for connecting to Plone and return all docs

    grok.name('lcms-query')
    grok.context(Interface)
    grok.layer(IUlearnTheme)

    def render(self):
        query = self.request.form.get('q', None)

        alldocs = self.request.form.get('all', None)

        portal = getSite()
        pc = getToolByName(portal, "portal_catalog")
        if alldocs=='True':
            docs = pc.searchResults(portal_type="Document",
                                    sort_on='id',)

        else:    
            docs = pc.searchResults(portal_type="Document",
                                    sort_on='id',
                                    SearchableText=query)

        data = []

        for obj in docs:
            valueEntry = {}
            valueEntry['Title'] = obj.Title
            valueEntry['path'] = obj.absolute_url()
            valueEntry['Description'] = obj.Description
            valueEntry['Description'] = obj.Description
            valueEntry['ModificationDate'] = obj.ModificationDate
            valueEntry['CreationDate'] = obj.CreationDate

            data.append(valueEntry)

        self.request.response.setHeader("Content-type", "application/json")
        return json.dumps(data)