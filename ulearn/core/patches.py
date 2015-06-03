# -*- encoding: utf-8 -*-
import copy

from plone import api
from zope.component import getUtility
from zope.component import getUtilitiesFor
from souper.interfaces import ICatalogFactory


# We are patching the enumerateUsers method of the mutable_properties plugin to
# make it return all the available user properties extension
def enumerateUsers(self, id=None, login=None, exact_match=False, **kw):
        """ See IUserEnumerationPlugin.
        """
        plugin_id = self.getId()

        # This plugin can't search for a user by id or login, because there is
        # no such keys in the storage (data dict in the comprehensive list)
        # If kw is empty or not, we continue the search.
        if id is not None or login is not None:
            return ()

        criteria = copy.copy(kw)

        users = [(user, data) for (user, data) in self._storage.items()
                if self.testMemberData(data, criteria, exact_match)
                and not data.get('isGroup', False)]

        has_extended_properties = False
        extender_name = api.portal.get_registry_record('genweb.controlpanel.core.IGenwebCoreControlPanelSettings.user_properties_extender')

        if extender_name in [a[0] for a in getUtilitiesFor(ICatalogFactory)]:
            has_extended_properties = True
            extended_user_properties_utility = getUtility(ICatalogFactory, name=extender_name)

        user_properties_utility = getUtility(ICatalogFactory, name='user_properties')

        users_profile = []
        for user_id, user in users:
            if user is not None:
                user_dict = {}
                for user_property in user_properties_utility.properties:
                    user_dict.update({user_property: user.get(user_property, '')})

                if has_extended_properties:
                    for user_property in extended_user_properties_utility.properties:
                        user_dict.update({user_property: user.get(user_property, '')})

                user_dict.update(dict(id=user_id))
                user_dict.update(dict(login=user_id))
                user_dict.update(dict(title=user.get('fullname', user_id)))
                user_dict.update(dict(description=user.get('fullname', user_id)))
                user_dict.update({'pluginid': plugin_id})
                users_profile.append(user_dict)

        return tuple(users_profile)
