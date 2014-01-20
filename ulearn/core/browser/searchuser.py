# -*- encoding: utf-8 -*-
from zope.component import getMultiAdapter
from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from itertools import chain
from Products.CMFPlone.utils import normalizeString
from zope.component.hooks import getSite
from ulearn.core.content.community import ICommunity
import random


def searchUsersFunction(context, request, searchString):
    ignore = []
    mtool = getToolByName(context, 'portal_membership')

    # Get all my communities
    pc = getToolByName(context, 'portal_catalog')
    if ICommunity.providedBy(context):
        visible = context.readers + context.subscribed + context.owners
    else:
        # We are in root object
        my_communities = pc.searchResults(subscribed_users=mtool.getAuthenticatedMember().getId())
        visible = list(set([user for community in my_communities for user in community.subscribed_users]))

    if searchString:
        searchView = getMultiAdapter((aq_inner(context), request), name='pas_search')
        # Si cal, per performance "max_results":20
        userResults = searchView.merge(chain(*[searchView.searchUsers(**{field: searchString}) for field in ['name', 'fullname', 'email', 'twitter_username', 'ubicacio', 'location']]), 'userid')
        userResults = [mtool.getMemberById(u['id']) for u in userResults if u['id'] not in ignore]
        userResults.sort(key=lambda x: x is not None and x.getProperty('fullname') is not None and normalizeString(x.getProperty('fullname')) or '')
    else:
        userResults = [mtool.getMemberById(user) for user in visible]
        userResults.sort(key=lambda x: x is not None and x.getProperty('fullname') is not None and normalizeString(x.getProperty('fullname')) or '')

    # Filter by community
    site = getSite()
    usersDict = []
    for user in userResults:
        # if is in any of my communities
        if user is not None and user.id in visible:
            usersDict.append({
                'id': user.id,
                'username': user.getProperty('fullname', ''),
                'ubicacio': user.getProperty('ubicacio', ''),
                'location': user.getProperty('location', ''),
                'email': user.getProperty('email', ''),
                'telefon': user.getProperty('telefon', ''),
                'foto': str(mtool.getPersonalPortrait(user.id)),
                'url': site.absolute_url() + '/profile/' + user.id
            })

    len_usuaris = len(usersDict)
    if len_usuaris > 20:
        escollits = random.sample(range(len(usersDict)), 20)
        llista = []
        for escollit in escollits:
            llista.append(usersDict[escollit])
        return {'content': llista, 'length': len_usuaris, 'big': True}
    else:
        return {'content': usersDict, 'length': len_usuaris, 'big': False}
