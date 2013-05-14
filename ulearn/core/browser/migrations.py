from five import grok
from zope.component import queryUtility
from zope.component import getMultiAdapter
from zope.component.hooks import getSite

from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import IPortletAssignmentMapping

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IPloneSiteRoot


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
