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
    grok.require('cmf.ManagePortal')

    def get_helpers(self):
        portal = getSite()
        app = portal.restrictedTraverse('/')

        plone_site = []
        application = []

        for module in MODULES_TO_INSPECT:
            themodule = importlib.import_module(module)
            members = inspect.getmembers(themodule, inspect.isclass)

            for name, klass in members:
                if grok.View in klass.__bases__:
                    if getattr(klass, 'grokcore.component.directive.context').getName() == 'IApplication':
                        application.append(dict(url='{}/{}'.format(app.absolute_url(), getattr(klass, 'grokcore.component.directive.name', name.lower())), description=klass.__doc__))
                    else:
                        plone_site.append(dict(url='{}/{}'.format(portal.absolute_url(), getattr(klass, 'grokcore.component.directive.name', name.lower())), description=klass.__doc__))

        return (plone_site, application)
