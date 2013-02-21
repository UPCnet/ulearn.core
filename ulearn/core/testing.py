from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import IntegrationTesting
from plone.app.testing import FunctionalTesting

from plone.testing import z2

from zope.configuration import xmlconfig


class UlearncoreLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load ZCML
        import ulearn.core
        xmlconfig.file(
            'configure.zcml',
            ulearn.core,
            context=configurationContext
        )

        # Install products that use an old-style initialize() function
        #z2.installProduct(app, 'Products.PloneFormGen')

#    def tearDownZope(self, app):
#        # Uninstall products installed above
#        z2.uninstallProduct(app, 'Products.PloneFormGen')

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'ulearn.core:default')

ULEARN_CORE_FIXTURE = UlearncoreLayer()
ULEARN_CORE_INTEGRATION_TESTING = IntegrationTesting(
    bases=(ULEARN_CORE_FIXTURE,),
    name="UlearncoreLayer:Integration"
)
ULEARN_CORE_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(ULEARN_CORE_FIXTURE, z2.ZSERVER_FIXTURE),
    name="UlearncoreLayer:Functional"
)
