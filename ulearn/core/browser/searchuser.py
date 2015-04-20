# -*- encoding: utf-8 -*-
from plone import api
from zope.component.hooks import getSite
from zope.component import getUtility
from zope.component import getUtilitiesFor

from Products.CMFPlone.interfaces import IPloneSiteRoot

from souper.soup import Record
from souper.interfaces import ICatalogFactory
from repoze.catalog.query import Eq
from repoze.catalog.query import Or
from souper.soup import get_soup

from mrs.max.utilities import IMAXClient
from ulearn.core.content.community import ICommunity

import random
import unicodedata


def searchUsersFunction(context, request, search_string):
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
            if isinstance(search_string, str):
                search_string = search_string.decode('utf-8')

            soup = get_soup('user_properties', portal)
            normalized_query = unicodedata.normalize('NFKD', search_string).encode('ascii', errors='ignore')
            normalized_query = normalized_query.replace('.', ' ') + '*'
            users = [r for r in soup.query(Eq('searchable_text', normalized_query))]
        else:
            # User information directly from mutable_properties to avoid LDAP
            # searches and force to show only the truly registered users
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
            if isinstance(search_string, str):
                search_string = search_string.decode('utf-8')

            normalized_query = unicodedata.normalize('NFKD', search_string).encode('ascii', errors='ignore')
            normalized_query = normalized_query.replace('.', ' ') + '*'
            plone_results = [r for r in soup.query(Eq('searchable_text', normalized_query))]

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
                    for user in merged_results:
                        record = [r for r in soup.query(Eq('username', user))]
                        if record:
                            users.append(record[0])
                        else:
                            # User subscribed, but no local profile found, append empty profile for display
                            pass

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

    has_extended_properties = False
    client = api.portal.get_registry_record('mrs.max.browser.controlpanel.IMAXUISettings.domain')
    if 'user_properties_{}'.format(client) in [a[0] for a in getUtilitiesFor(ICatalogFactory)]:
        has_extended_properties = True
        extended_user_properties_utility = getUtility(ICatalogFactory, name='user_properties_{}'.format(client))

    user_properties_utility = getUtility(ICatalogFactory, name='user_properties')

    users_profile = []
    for user in users:
        if user is not None:
            if isinstance(user, Record):
                user_dict = {}
                for user_property in user_properties_utility.properties:
                    user_dict.update({user_property: user.attrs.get(user_property, '')})

                if has_extended_properties:
                    for user_property in extended_user_properties_utility.properties:
                        user_dict.update({user_property: user.attrs.get(user_property, '')})

                user_dict.update(dict(id=user.attrs['username']))
                user_dict.update(dict(foto=str(pm.getPersonalPortrait(user.attrs['username']))))
                user_dict.update(dict(url=portal.absolute_url() + '/profile/' + user.attrs['username']))
                users_profile.append(user_dict)

            else:
                user_dict = {}
                for user_property in user_properties_utility.properties:
                    user_dict.update({user_property: user.get(user_property, '')})
                    user_dict.update(dict(id=user.get('id', '')))
                    user_dict.update(dict(fullname=user.get('title', '')))

                if has_extended_properties:
                    for user_property in extended_user_properties_utility.properties:
                        user_dict.update({user_property: user.get(user_property, '')})

                user_dict.update(dict(foto=str(pm.getPersonalPortrait(user.get('id', '')))))
                user_dict.update(dict(url=portal.absolute_url() + '/profile/' + user.get('id', '')))
                users_profile.append(user_dict)

    len_usuaris = len(users_profile)
    if len_usuaris > 100:
        escollits = random.sample(range(len(users_profile)), 100)
        llista = []
        for escollit in escollits:
            llista.append(users_profile[escollit])
        return {'content': llista, 'length': len_usuaris, 'big': True}
    else:
        return {'content': users_profile, 'length': len_usuaris, 'big': False}
