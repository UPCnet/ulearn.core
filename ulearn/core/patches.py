# -*- encoding: utf-8 -*-
import copy


def enumerateUsers(self, id=None, login=None,
                       exact_match=False, **kw):
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

        user_info = [{'id': self.prefix + user_id,
                      'login': user_id,
                      'title': data.get('fullname', user_id),
                      'description': data.get('fullname', user_id),
                      'email': data.get('email', ''),
                      'ubicacio': data.get('ubicacio', ''),
                      'location': data.get('location', ''),
                      'telefon': data.get('telefon', ''),
                      'pluginid': plugin_id} for (user_id, data) in users]

        return tuple(user_info)
