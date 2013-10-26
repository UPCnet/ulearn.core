from five import grok
from Acquisition import aq_parent
from Acquisition import aq_inner
from zope.component import queryUtility
from zope.component import getMultiAdapter
from zope.component.hooks import getSite

from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import IPortletAssignmentMapping

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IPloneSiteRoot

from ulearn.core.interfaces import IDocumentFolder, ILinksFolder, IPhotosFolder, IEventsFolder


class portletfix(grok.View):
    grok.context(IPloneSiteRoot)

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
