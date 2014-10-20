from five import grok
from plone import api
from Acquisition import aq_parent
from Acquisition import aq_inner
from zope.component import getUtility
from zope.component import queryUtility
from zope.component import getMultiAdapter
from zope.component.hooks import getSite
from zope.interface import alsoProvides
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent
from OFS.interfaces import IApplication

from Products.CMFPlone.interfaces.constrains import ISelectableConstrainTypes

from plone.portlets.constants import CONTEXT_CATEGORY
from plone.portlets.interfaces import ILocalPortletAssignmentManager
from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import IPortletAssignmentMapping
from plone.dexterity.utils import createContentInContainer
from plone.subrequest import subrequest

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IPloneSiteRoot

from ulearn.core.interfaces import IDocumentFolder, ILinksFolder, IPhotosFolder, IEventsFolder
from ulearn.core.content.community import IInitializedCommunity
from ulearn.core.content.community import Community
from genweb.core.browser.helpers import listPloneSites

from ulearn.core.interfaces import IDiscussionFolder
from ulearn.core import _


from mrs.max.utilities import IMAXClient
from maxclient.rest import RequestError

from itertools import chain
import logging

logger = logging.getLogger(__name__)


class portletfix(grok.View):
    grok.context(IPloneSiteRoot)
    grok.require('zope2.ViewManagementScreens')

    def render(self):
        portal = getSite()
        pc = getToolByName(portal, "portal_catalog")
        communities = pc.searchResults(portal_type="ulearn.community")

        for community in communities:
            community = community.getObject()
            target_manager = queryUtility(IPortletManager, name='plone.leftcolumn', context=community)
            target_manager_assignments = getMultiAdapter((community, target_manager), IPortletAssignmentMapping)
            for portlet in target_manager_assignments.keys():
                del target_manager_assignments[portlet]

            target_manager = queryUtility(IPortletManager, name='plone.rightcolumn', context=community)
            target_manager_assignments = getMultiAdapter((community, target_manager), IPortletAssignmentMapping)
            for portlet in target_manager_assignments.keys():
                del target_manager_assignments[portlet]


class linkFolderFix(grok.View):
    grok.context(IPloneSiteRoot)
    grok.require('zope2.ViewManagementScreens')

    def render(self):
        portal = getSite()
        pc = getToolByName(portal, "portal_catalog")
        folder_ifaces = {IDocumentFolder.__identifier__: 'documents',
                         ILinksFolder.__identifier__: 'links',
                         IPhotosFolder.__identifier__: 'media',
                         IEventsFolder.__identifier__: 'events'}

        for iface in folder_ifaces.keys():
            results = pc.searchResults(object_provides=iface)
            for result in results:
                parent = aq_parent(aq_inner(result.getObject()))
                parent.manage_renameObjects((result.id,), (folder_ifaces[iface],))
                print("renamed {} to {} in community {}".format(result.id, folder_ifaces[iface], parent))


def createMAXUser(username):
    maxclient, settings = getUtility(IMAXClient)()
    maxclient.setActor(settings.max_restricted_username)
    maxclient.setToken(settings.max_restricted_token)

    try:
        maxclient.people[username].post()

        if maxclient.last_response_code == 201:
            logger.info('MAX user created for user: %s' % username)
        elif maxclient.last_response_code == 200:
            logger.info('MAX user already created for user: %s' % username)

    except RequestError:
        import ipdb;ipdb.set_trace()
    except:
        logger.error('Error creating MAX user for user: %s' % username)


class createMAXUserForAllExistingUsers(grok.View):
    grok.context(IPloneSiteRoot)
    grok.require('zope2.ViewManagementScreens')

    def render(self):
        mtool = getToolByName(self, 'portal_membership')

        searchView = getMultiAdapter((aq_inner(self.context), self.request), name='pas_search')

        searchString = ''

        self.request.set('__ignore_group_roles__', True)
        self.request.set('__ignore_direct_roles__', False)
        explicit_users = searchView.merge(chain(*[searchView.searchUsers(**{field: searchString}) for field in ['login', 'fullname', 'email']]), 'userid')

        for user_info in explicit_users:
            userId = user_info['id']
            user = mtool.getMemberById(userId)
            createMAXUser(user.getUserName())


class InitializeAllCommunities(grok.View):
    grok.context(IPloneSiteRoot)
    grok.require('zope2.ViewManagementScreens')

    def render(self):
        pc = api.portal.get_tool(name='portal_catalog')
        results = pc.searchResults(portal_type='ulearn.community')
        for result in results:
            community = result.getObject()
            if not IInitializedCommunity.providedBy(community):
                logger.error('Initializing community {}'.format(community.absolute_url()))
                alsoProvides(community, IInitializedCommunity)
                notify(ObjectModifiedEvent(community))


class CreateDiscussionFolders(grok.View):
    grok.context(IPloneSiteRoot)
    grok.require('zope2.ViewManagementScreens')

    def render(self):
        pc = api.portal.get_tool(name="portal_catalog")
        communities = pc.searchResults(portal_type="ulearn.community")
        for community in communities:
            community = community.getObject()
            if not 'discussion' in community.objectIds():
                # Create the default discussion container and set title
                discussion = createContentInContainer(community, 'Folder', title='discussion', checkConstraints=False)
                discussion.setTitle(community.translate(_(u"Discussion")))

                discussion.setLayout('discussion_folder_view')

                alsoProvides(discussion, IDiscussionFolder)

                behavior = ISelectableConstrainTypes(discussion)
                behavior.setConstrainTypesMode(1)
                behavior.setLocallyAllowedTypes(('ulearn.discussion', 'Folder'))
                behavior.setImmediatelyAddableTypes(('ulearn.discussion', 'Folder'))

                # Blacklist the right column portlets on discussion
                right_manager = queryUtility(IPortletManager, name=u"plone.rightcolumn")
                blacklist = getMultiAdapter((discussion, right_manager), ILocalPortletAssignmentManager)
                blacklist.setBlacklistStatus(CONTEXT_CATEGORY, True)

                discussion.reindexObject()

                logger.info("Created discussion folder in {}".format(community.absolute_url()))

        return 'Done.'


class InitializeVideos(grok.View):
    grok.context(IPloneSiteRoot)
    grok.require('zope2.ViewManagementScreens')

    def render(self):
        pc = api.portal.get_tool(name="portal_catalog")
        communities = pc.searchResults(portal_type="ulearn.community")

        text = []
        for community in communities:
            community = community.getObject()
            media_folder = community.media

            behavior = ISelectableConstrainTypes(media_folder)
            behavior.setConstrainTypesMode(1)
            behavior.setLocallyAllowedTypes(('Image', 'ulearn.video', 'Folder'))
            behavior.setImmediatelyAddableTypes(('Image', 'ulearn.video', 'Folder'))

            if media_folder.title != 'Media':
                media_folder.setTitle(community.translate(_(u"Media")))

            text.append('Added type video to {}\n'.format(community.absolute_url()))
        return ''.join(text)


class MigrateCommunities(grok.View):
    """ It should be executed on an running instance with no MAX hooks enabled
        to avoid them to be executed when persisting the new communities objects
    """
    grok.context(IPloneSiteRoot)
    grok.name('migrate_to_new_communities')
    grok.require('zope2.ViewManagementScreens')

    def render(self):
        portal = api.portal.get()
        pc = api.portal.get_tool(name="portal_catalog")
        communities = pc.searchResults(portal_type="ulearn.community")

        text = []
        for community_brain in communities:
            # We assume that there will be only communities in Portal Site Root
            community = portal[community_brain.id]
            if community.__class__ != Community:
                portal._delOb(community_brain.id)

                community.__class__ = Community
                portal._setOb(community.id, community)

                text.append('Migrated community {}\n'.format(community.absolute_url()))
        return ''.join(text) + '\nDone!'


class ReinstalluLearn(grok.View):
    """ Reinstalls uLearn in the current Plone site. """
    grok.context(IPloneSiteRoot)
    grok.name('reinstall_ulearn')
    grok.require('cmf.ManagePortal')

    def render(self):
        context = aq_inner(self.context)
        output = []
        qi = getToolByName(context, 'portal_quickinstaller')

        if qi.isProductInstalled('ulearn.core'):
            qi.reinstallProducts(['ulearn.core'])
            output.append('{}: Successfully reinstalled ulearn.core'.format(context))
        return '\n'.join(output)


class ReinstalluLearnControlPanel(grok.View):
    """ Reinstalls uLearn in the current Plone site. """
    grok.context(IPloneSiteRoot)
    grok.name('reinstall_ulearncontrolpanel')
    grok.require('cmf.ManagePortal')

    def render(self):
        context = aq_inner(self.context)
        output = []

        setup = api.portal.get_tool('portal_setup')
        profile_id = 'profile-ulearn.core:default'
        step_id = 'plone.app.registry'
        setup.runImportStepFromProfile(profile_id, step_id,
                                       run_dependencies=True, purge_old=None)
        output.append('{}: Successfully reinstalled ulearn.core control panel'.format(context))

        return '\n'.join(output)


class BulkReinstalluLearn(grok.View):
    """
        Reinstall genweb.controlpanel in all the Plone instance of this Zope.
        Useful when added some parameter to the control panel and you want to
        apply it at the same time in all the existing Plone sites in the Zope.
    """
    grok.context(IApplication)
    grok.name('bulk_reinstall_ulearncontrolpanel')
    grok.require('cmf.ManagePortal')

    def render(self):
        context = aq_inner(self.context)
        plonesites = listPloneSites(context)
        output = []
        for plonesite in plonesites:
            response = subrequest('/'.join(plonesite.getPhysicalPath()) + '/reinstall_ulearncontrolpanel')
            output.append(response.getBody())
        return '\n'.join(output)
