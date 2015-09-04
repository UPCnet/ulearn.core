# -*- coding: utf-8 -*-
import unittest2 as unittest
from zope.component import getUtility
from zope.component import getMultiAdapter
from ulearn.core.tests import uLearnTestBase
from ulearn.core.testing import ULEARN_CORE_INTEGRATION_TESTING
from ulearn.js.browser.viewlets import gwJSDevelViewlet
from ulearn.js.browser.viewlets import gwJSProductionViewlet

import json
import pkg_resources


class TestExample(uLearnTestBase):

    layer = ULEARN_CORE_INTEGRATION_TESTING

    def setUp(self):
        self.app = self.layer['app']
        self.portal = self.layer['portal']
        self.request = self.layer['request']

        ulearnjsegg = pkg_resources.get_distribution('ulearn.js')
        resource_file = open('{}/ulearn/core/config.json'.format(ulearnjsegg.location))
        self.resources_conf = json.loads(resource_file.read())

    def test_js_development_resource_viewlet(self):

        viewlet = gwJSDevelViewlet(self.portal, self.request, None, None)
        viewlet.update()
        resources = viewlet.get_resources()

        for resource in resources:
            self.assertTrue('++' in resource)

    def test_js_production_resource_viewlet(self):
        viewlet = gwJSProductionViewlet(self.portal, self.request, None, None)
        viewlet.update()
        resources = viewlet.get_resources()

        for resource in resources:
            self.assertTrue('++' in resource)

        self.assertTrue(len(resources) == len(self.resources_conf['order']))
