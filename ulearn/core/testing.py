from zope.component import getUtility
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import IntegrationTesting
from plone.app.testing import FunctionalTesting
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from plone.app.testing import login
from plone.app.testing import logout

from plone.testing import z2
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE

from zope.configuration import xmlconfig
from zope.interface import alsoProvides

from mrs.max.utilities import IMAXClient
from mrs.max.utilities import set_user_oauth_token

from ulearn.theme.browser.interfaces import IUlearnTheme


def setup_max(restricted, password):
    maxclient, settings = getUtility(IMAXClient)()
    token = maxclient.getToken(restricted, password)
    settings.max_restricted_username = restricted
    settings.max_restricted_token = token

    set_user_oauth_token(restricted, token)


def set_browserlayer(request):
    """Set the BrowserLayer for the request.

    We have to set the browserlayer manually, since importing the profile alone
    doesn't do it in tests.
    """
    alsoProvides(request, IUlearnTheme)


class UlearncoreLayer(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE, PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load ZCML
        import ulearn.core
        xmlconfig.file(
            'configure.zcml',
            ulearn.core,
            context=configurationContext
        )

        # Needed to make p.a.iterate permissions available as g.core needs them
        import plone.app.iterate.permissions

#    def tearDownZope(self, app):
#        # Uninstall products installed above
#        z2.uninstallProduct(app, 'Products.PloneFormGen')

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'ulearn.core:default')

        portal.acl_users.userFolderAddUser('admin', 'secret', ['Manager'], [])
        portal.acl_users.userFolderAddUser('user', 'secret', ['Member'], [])
        portal.acl_users.userFolderAddUser('poweruser', 'secret', ['Member', 'WebMaster'], [])
        portal.acl_users.userFolderAddUser('victor.fernandez', 'secret', ['Member'], [])
        portal.acl_users.userFolderAddUser('janet.dura', 'secret', ['Member'], [])
        portal.acl_users.userFolderAddUser('usuari.iescude', 'secret', ['Member', 'WebMaster'], [])

        login(portal, 'admin')
        setup_max(u'usuari.iescude', 'holahola')
        portal.portal_workflow.setDefaultChain("genweb_intranet")
        logout()
        # setRoles(portal, TEST_USER_ID, ['Manager'])

ULEARN_CORE_FIXTURE = UlearncoreLayer()
ULEARN_CORE_INTEGRATION_TESTING = IntegrationTesting(
    bases=(ULEARN_CORE_FIXTURE,),
    name="UlearncoreLayer:Integration"
)
ULEARN_CORE_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(ULEARN_CORE_FIXTURE, z2.ZSERVER_FIXTURE),
    name="UlearncoreLayer:Functional"
)
