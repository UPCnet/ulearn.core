from five import grok
from zope.component.hooks import getSite

from Products.CMFPlone.interfaces import IPloneSiteRoot

from ulearn.theme.browser.interfaces import IUlearnTheme

import inspect
import importlib

MODULES_TO_INSPECT = ['genweb.core.browser.setup',
                      'ulearn.core.browser.setup',
                      'ulearn.core.browser.migrations']


class clouseau(grok.View):
    grok.context(IPloneSiteRoot)
    grok.layer(IUlearnTheme)

    def get_templates(self):
        portal = getSite()

        urls = []

        for module in MODULES_TO_INSPECT:
            themodule = importlib.import_module(module)
            members = inspect.getmembers(themodule, inspect.isclass)

            for name, klass in members:
                if grok.View in klass.__bases__:
                    urls.append('{}/{}'.format(portal.absolute_url(), name.lower()))

        return urls
