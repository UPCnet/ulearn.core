# -*- encoding: utf-8 -*-
from plone import api
from zope.component.hooks import getSite
from zope.component import getUtility

from Products.CMFPlone.utils import normalizeString
from Products.CMFPlone.interfaces import IPloneSiteRoot

from souper.soup import Record
from repoze.catalog.query import Eq
from repoze.catalog.query import Or
from repoze.catalog.query import All
from souper.soup import get_soup

from mrs.max.utilities import IMAXClient
from ulearn.core.content.community import ICommunity

import random


def searchUsersFunction(context, request, search_string, user_properties=None):
    portal = getSite()
    pm = api.portal.get_tool(name='portal_membership')
    nonvisibles = api.portal.get_registry_record(name="ulearn.core.controlpanel.IUlearnControlPanelSettings.nonvisibles")

    current_user = api.user.get_current()
    oauth_token = current_user.getProperty('oauth_token', '')

    maxclient, settings = getUtility(IMAXClient)()
    maxclient.setActor(current_user.getId())
    maxclient.setToken(oauth_token)

    users = portal.acl_users.mutable_properties.enumerateUsers()

    if IPloneSiteRoot.providedBy(context):
        # Search by string (partial) and return a list of Records from the user
        # catalog
        if search_string:
            soup = get_soup('user_properties', portal)
            users = [r for r in soup.query(Or(Eq('username', search_string + '*'),
                                              Eq('fullname', search_string + '*'),
                                              Eq('telefon', search_string + '*'),
                                              Eq('email', search_string + '*'),
                                              Eq('ubicacio', search_string + '*')))]
        else:
            # User information directly from mutable_properties to avoid LDAP searches
            # plone_results = [userinfo.get('login') for userinfo in portal.acl_users.mutable_properties.enumerateUsers()]
            # users = [pm.getMemberById(user) for user in plone_results]
            if nonvisibles:
                filtered = []
                for user in users:
                    if user is not None:
                        if user.attrs['username'] not in nonvisibles:
                            filtered.append(user)
                users = filtered

    if ICommunity.providedBy(context):
        if search_string:
            maxclientrestricted, settings = getUtility(IMAXClient)()
            maxclientrestricted.setActor(settings.max_restricted_username)
            maxclientrestricted.setToken(settings.max_restricted_token)
            max_users = maxclientrestricted.contexts[context.absolute_url()].subscriptions.get(qs={'username': search_string, 'limit': 0})

            soup = get_soup('user_properties', portal)
            plone_results = [r for r in soup.query(Or(Eq('username', search_string + '*'),
                                                      Eq('fullname', search_string + '*'),
                                                      Eq('telefon', search_string + '*'),
                                                      Eq('email', search_string + '*'),
                                                      Eq('ubicacio', search_string + '*')))]

            if max_users:
                merged_results = list(set([plone_user.attrs['username'] for plone_user in plone_results]) &
                                      set([max_user['username'] for max_user in max_users]))
                users = []
                for user in merged_results:
                    users.append([r for r in soup.query(Or(Eq('username', user + '*')))][0])

            else:
                merged_results = []
                users = []
                for plone_user in plone_results:
                    max_results = maxclientrestricted.contexts[context.absolute_url()].subscriptions.get(qs={'username': plone_user.attrs['username'], 'limit': 0})
                    merged_results_user = list(set([plone_user.attrs['username']]) &
                                               set([max_user['username'] for max_user in max_results]))
                    if merged_results_user != []:
                        merged_results.append(merged_results_user[0])

                if merged_results:
                    users = [r for r in soup.query(All('username', merged_results))]

        else:
            soup = get_soup('user_properties', portal)
            maxclientrestricted, settings = getUtility(IMAXClient)()
            maxclientrestricted.setActor(settings.max_restricted_username)
            maxclientrestricted.setToken(settings.max_restricted_token)
            max_users = maxclientrestricted.contexts[context.absolute_url()].subscriptions.get(qs={'limit': 0})
            max_users = [user.get('username') for user in max_users]

            users = []
            for user in max_users:
                record = [r for r in soup.query(Eq('username', user))]
                if record:
                    users.append(record[0])
                else:
                    # User subscribed, but no local profile found, append empty profile for display
                    pass

            if nonvisibles:
                filtered = []
                for user in users:
                    if user is not None:
                        if user.attrs['username'] not in nonvisibles:
                            filtered.append(user)
                users = filtered

    users_profile = []
    for user in users:
        if user is not None:
            if isinstance(user, Record):
                if user_properties:
                    # Per revisar
                    user_dict = {}
                    for user_property in user_properties:
                        user_dict.update({user_property: user.attrs.get(user_property, '')})
                    user_dict.update(dict(id=user.attrs['username']))
                    user_dict.update(dict(foto=str(pm.getPersonalPortrait(user.attrs['username']))))
                    user_dict.update(dict(url=portal.absolute_url() + '/profile/' + user.attrs['username']))
                    users_profile.append(user_dict)
                else:
                    users_profile.append({
                        'id': user.attrs['username'],
                        'fullname': user.attrs.get('fullname', ''),
                        'ubicacio': user.attrs.get('ubicacio', ''),
                        'location': user.attrs.get('location', ''),
                        'email': user.attrs.get('email', ''),
                        'telefon': user.attrs.get('telefon', ''),
                        'foto': str(pm.getPersonalPortrait(user.attrs['username'])),
                        'url': portal.absolute_url() + '/profile/' + user.attrs['username']
                    })
            else:
                if user_properties:
                    user_dict = {}
                    for user_property in user_properties:
                        user_dict.update({user_property: user.get(user_property, '')})
                    user_dict.update(dict(foto=str(pm.getPersonalPortrait(user.id))))
                    user_dict.update(dict(url=portal.absolute_url() + '/profile/' + user.id))
                    users_profile.append(user_dict)
                else:
                    users_profile.append({
                        'id': user.get('id', ''),
                        'fullname': user.get('title', ''),
                        'ubicacio': user.get('ubicacio', ''),
                        'location': user.get('location', ''),
                        'email': user.get('email', ''),
                        'telefon': user.get('telefon', ''),
                        'foto': str(pm.getPersonalPortrait(user.get('id', ''))),
                        'url': portal.absolute_url() + '/profile/' + user.get('id', '')
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
