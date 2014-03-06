# -*- encoding: utf-8 -*-
from zope.component import getMultiAdapter, getUtility
from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from itertools import chain
from Products.CMFPlone.utils import normalizeString
from zope.component.hooks import getSite

from mrs.max.utilities import IMAXClient
from ulearn.core.content.community import ICommunity

import plone.api
import random


def searchUsersFunction(context, request, search_string, user_properties=None):
    current_user = plone.api.user.get_current()
    oauth_token = current_user.getProperty('oauth_token', '')

    maxclient, settings = getUtility(IMAXClient)()
    maxclient.setActor(current_user.getId())
    maxclient.setToken(oauth_token)

    maxclient.people.get(qs={'username': search_string})


    len_usuaris = len(usersDict)
    if len_usuaris > 100:
        escollits = random.sample(range(len(usersDict)), 100)
        llista = []
        for escollit in escollits:
            llista.append(usersDict[escollit])
        return {'content': llista, 'length': len_usuaris, 'big': True}
    else:
        return {'content': usersDict, 'length': len_usuaris, 'big': False}



def searchUsersFunction_old(context, request, searchString, user_properties=None):
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
            if user_properties:
                user_dict = {}
                for user_property in user_properties:
                    user_dict.update({user_property: user.getProperty(user_property, '')})
                user_dict.update(dict(foto=str(mtool.getPersonalPortrait(user.id))))
                user_dict.update(dict(url=site.absolute_url() + '/profile/' + user.id))
                usersDict.append(user_dict)
            else:
                usersDict.append({
                    'id': user.id,
                    'fullname': user.getProperty('fullname', ''),
                    'ubicacio': user.getProperty('ubicacio', ''),
                    'location': user.getProperty('location', ''),
                    'email': user.getProperty('email', ''),
                    'telefon': user.getProperty('telefon', ''),
                    'foto': str(mtool.getPersonalPortrait(user.id)),
                    'url': site.absolute_url() + '/profile/' + user.id
                })

    len_usuaris = len(usersDict)
    if len_usuaris > 100:
        escollits = random.sample(range(len(usersDict)), 100)
        llista = []
        for escollit in escollits:
            llista.append(usersDict[escollit])
        return {'content': llista, 'length': len_usuaris, 'big': True}
    else:
        return {'content': usersDict, 'length': len_usuaris, 'big': False}
