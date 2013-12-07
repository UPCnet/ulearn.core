# -*- encoding: utf-8 -*-
from zope.component import getMultiAdapter
from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from itertools import chain
from Products.CMFPlone.utils import normalizeString
from five import grok
from zope.interface import Interface
import json


class SearchUser(grok.View):
    grok.name('searchUser')
    grok.context(Interface)

    def update(self):
        pass

    def render(self):
        if 'search' in self.request:
            searchString = self.request.get('search')
        else:
            searchString = ''
        ignore = []
        mtool = getToolByName(self.context, 'portal_membership')
        searchView = getMultiAdapter((aq_inner(self.context), self.request), name='pas_search')
        userResults = searchView.merge(chain(*[searchView.searchUsers(**{field: searchString}) for field in ['name', 'fullname', 'email', 'twitter_username', 'ubicacio', 'location']]), 'userid')
        userResults = [mtool.getMemberById(u['id']) for u in userResults if u['id'] not in ignore]
        userResults.sort(key=lambda x: x is not None and x.getProperty('fullname') is not None and normalizeString(x.getProperty('fullname')) or '')

        usersDict = []
        for user in userResults:
            usersDict.append({
                'username': user.getProperty('fullname'),
                'ubicacio': user.getProperty('ubicacio'),
                'location': user.getProperty('location'),
                'email': user.getProperty('email'),
                'foto': self.context.absolute_url() + '/portal_memberdata/portraits/' + user.id
                })
        self.request.response.setHeader('Content-Type', 'application/json')
        return json.dumps(usersDict)
