# -*- encoding: utf-8 -*-
from Acquisition import aq_inner
from itertools import chain
from zope.component.hooks import getSite
from zope.component import getMultiAdapter, getUtility
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import normalizeString
from Products.CMFPlone.interfaces import IPloneSiteRoot

from mrs.max.utilities import IMAXClient
from ulearn.core.content.community import ICommunity

import plone.api
import random


def searchUsersFunction(context, request, search_string, user_properties=None):
    portal = getSite()
    pm = plone.api.portal.get_tool(name='portal_membership')
    nonvisibles = plone.api.portal.get_registry_record(name="ulearn.core.controlpanel.IUlearnControlPanelSettings.nonvisibles")
    searchView = getMultiAdapter((aq_inner(context), request), name='pas_search')

    current_user = plone.api.user.get_current()
    oauth_token = current_user.getProperty('oauth_token', '')

    maxclient, settings = getUtility(IMAXClient)()
    maxclient.setActor(current_user.getId())
    maxclient.setToken(oauth_token)

    if IPloneSiteRoot.providedBy(context):
        if search_string:
            max_results = maxclient.people.get(qs={'username': search_string})

            plone_results = searchView.merge(chain(*[searchView.searchUsers(**{field: search_string}) for field in ['name', 'fullname', 'email', 'twitter_username', 'ubicacio', 'location']]), 'userid')

            merged_results = list(set([plone_user['userid'] for plone_user in plone_results]) &
                                  set([max_user['username'] for max_user in max_results]))

            users = [pm.getMemberById(user) for user in merged_results]
        else:
            plone_results = [userinfo.get('login') for userinfo in portal.acl_users.mutable_properties.enumerateUsers()]
            users = [pm.getMemberById(user) for user in plone_results]

            if nonvisibles:
                filtered = []
                for user in users:
                    if user.id not in nonvisibles:
                        filtered.append(user)
                users = filtered

    if ICommunity.providedBy(context):
        if search_string:
            max_users = maxclient.contexts[context.absolute_url()].subscriptions.get(qs={'username': search_string, 'limit': 0})

            plone_results = searchView.merge(chain(*[searchView.searchUsers(**{field: search_string}) for field in ['name', 'fullname', 'email', 'twitter_username', 'ubicacio', 'location']]), 'userid')

            merged_results = list(set([plone_user['userid'] for plone_user in plone_results]) &
                                  set([max_user['username'] for max_user in max_results]))

            users = [pm.getMemberById(user) for user in merged_results]
        else:
            maxclientrestricted, settings = getUtility(IMAXClient)()
            maxclientrestricted.setActor(settings.max_restricted_username)
            maxclientrestricted.setToken(settings.max_restricted_token)
            max_users = maxclientrestricted.contexts[context.absolute_url()].subscriptions.get(qs={'limit': 0})
            users = [pm.getMemberById(user.get('username')) for user in max_users]

    users_profile = []
    for user in users:
        if user is not None:
            if user_properties:
                user_dict = {}
                for user_property in user_properties:
                    user_dict.update({user_property: user.getProperty(user_property, '')})
                user_dict.update(dict(foto=str(pm.getPersonalPortrait(user.id))))
                user_dict.update(dict(url=portal.absolute_url() + '/profile/' + user.id))
                users_profile.append(user_dict)
            else:
                users_profile.append({
                    'id': user.id,
                    'fullname': user.getProperty('fullname', ''),
                    'ubicacio': user.getProperty('ubicacio', ''),
                    'location': user.getProperty('location', ''),
                    'email': user.getProperty('email', ''),
                    'telefon': user.getProperty('telefon', ''),
                    'foto': str(pm.getPersonalPortrait(user.id)),
                    'url': portal.absolute_url() + '/profile/' + user.id
                })

    len_usuaris = len(users_profile)
    if len_usuaris > 100:
        escollits = random.sample(range(len(users_profile)), 100)
        llista = []
        for escollit in escollits:
            llista.append(users_profile[escollit])
        return {'content': llista, 'length': len_usuaris, 'big': True}
    else:
        return {'content': users_profile, 'length': len_usuaris, 'big': False}


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
