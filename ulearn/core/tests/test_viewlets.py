# -*- coding: utf-8 -*-
from ulearn.core.tests import uLearnTestBase
from ulearn.core.testing import ULEARN_CORE_INTEGRATION_TESTING
from ulearn.theme.browser.viewlets import gwCSSDevelViewlet
from ulearn.theme.browser.viewlets import gwCSSProductionViewlet
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

        ulearnthemeegg = pkg_resources.get_distribution('ulearn.theme')
        ulearnjsegg = pkg_resources.get_distribution('ulearn.js')

        resource_file_css = open('{}/ulearn/core/config.json'.format(ulearnthemeegg.location))
        resource_file_js = open('{}/ulearn/core/config.json'.format(ulearnjsegg.location))
        self.resources_conf_css = json.loads(resource_file_css.read())
        self.resources_conf_js = json.loads(resource_file_js.read())

    def test_css_development_resource_viewlet(self):

        viewlet = gwCSSDevelViewlet(self.portal, self.request, None, None)
        viewlet.update()
        resources = viewlet.get_resources()

        for resource in resources:
            self.assertTrue('++' in resource)

    def test_css_production_resource_viewlet(self):
        viewlet = gwCSSProductionViewlet(self.portal, self.request, None, None)
        viewlet.update()
        resources = viewlet.get_resources()

        for resource in resources:
            self.assertTrue('++' in resource)

        self.assertTrue(len(resources) == len(self.resources_conf_css['order']))

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

        self.assertTrue(len(resources) == len(self.resources_conf_js['order']))
