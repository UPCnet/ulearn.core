import unittest2 as unittest

from Products.CMFCore.utils import getToolByName

from ulearn.core.testing import ULEARN_CORE_FUNCTIONAL_TESTING

import requests
import os


class TestUploads(unittest.TestCase):

    layer = ULEARN_CORE_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer['app']
        self.portal = self.layer['portal']
        import ipdb;ipdb.set_trace()

    def test_upload_file_to_community(self):
        avatar_file = open(os.path.join(os.path.dirname(__file__), "image.png"), "rb")
        files = {'file': ('image.png', avatar_file)}

        res = requests.post('http://localhost:55001/{}/upload'.format(community_id), headers=oauth2Header(username), files=files)
        self.assertEqual(res.status_code, 201)
