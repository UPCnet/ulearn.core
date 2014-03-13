import unittest2 as unittest

from zope.component import getUtility
from plone.app.testing import login
from plone.app.testing import logout

from Products.CMFCore.utils import getToolByName

from ulearn.core.testing import ULEARN_CORE_FUNCTIONAL_TESTING
from mrs.max.utilities import IMAXClient

import requests
import os
import transaction


class TestUploads(unittest.TestCase):

    layer = ULEARN_CORE_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer['app']
        self.portal = self.layer['portal']

        maxclient, settings = getUtility(IMAXClient)()
        self.username = settings.max_restricted_username
        self.token = settings.max_restricted_token

    def oauth2Header(self, username, token, scope="widgetcli"):
        return {
            "X-Oauth-Token": token,
            "X-Oauth-Username": username,
            "X-Oauth-Scope": scope}

    def create_test_community(self):
        nom = u'community-test'
        description = 'Blabla'
        subscribed = ['usuari.iescude']
        image = None
        community_type = 'Open'
        twitter_hashtag = 'helou'
        login(self.portal, 'poweruser')
        self.portal.invokeFactory('ulearn.community', 'community-test',
                                 title=nom,
                                 description=description,
                                 subscribed=subscribed,
                                 image=image,
                                 community_type=community_type,
                                 twitter_hashtag=twitter_hashtag)
        logout()

        transaction.commit()
        return self.portal['community-test']

    def test_upload_file_to_community(self):
        community = self.create_test_community()
        avatar_file = open(os.path.join(os.path.dirname(__file__), "avatar.png"), "rb")
        files = {'file': ('avatar.png', avatar_file)}

        res = requests.post('{}/{}/upload'.format(self.portal.absolute_url(), community.id), headers=self.oauth2Header(self.username, self.token), files=files)

        transaction.commit()

        self.assertEqual(res.status_code, 201)
        self.assertTrue('avatar.png' in community['media'].objectIds())
