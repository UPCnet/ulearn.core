# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from plone.app.event.base import localized_now
from Products.CMFCore.utils import getToolByName
from ulearn.theme.portlets import calendar as portlet_calendar
from ulearn.core.testing import ULEARN_CORE_INTEGRATION_TESTING
from plone.app.testing import login
from plone.app.testing import logout
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import IPortletRenderer
from zope.component import getUtility
from zope.component import getMultiAdapter
from zope.component.hooks import setHooks
from zope.component.hooks import setSite

import unittest2 as unittest

import transaction

TZNAME = "Europe/Vienna"


class RendererTest(unittest.TestCase):
    layer = ULEARN_CORE_INTEGRATION_TESTING

    def setUp(self):
        portal = self.layer['portal']
        self.portal = portal
        self.request = self.layer['request']
        self.wft = getToolByName(self.portal, 'portal_workflow')
        setRoles(portal, TEST_USER_ID, ['Manager'])
        setHooks()
        setSite(portal)

        # Make sure Events use simple_publication_workflow
        # self.portal.portal_workflow.setChainForPortalTypes(
        #     ['Event'], ['simple_publication_workflow']
        # )

    def create_test_community(self):
        nom = u'community-test'
        description = 'Blabla'
        subscribed = [u'usuari.iescude']
        image = None
        community_type = 'Open'
        twitter_hashtag = 'helou'
        login(self.portal, 'usuari.iescude')
        self.portal.invokeFactory('ulearn.community', 'community-test',
                                 title=nom,
                                 description=description,
                                 subscribed=subscribed,
                                 image=image,
                                 community_type=community_type,
                                 twitter_hashtag=twitter_hashtag)
        logout()

        # transaction.commit()  # This is for not conflict with each other
        # TODO: Do the teardown properly
        return self.portal['community-test']

    def create_event(self, context, day, start, end, event_id='e1'):
        now = localized_now().replace(minute=0, second=0, microsecond=0)
        start = localized_now().replace(day=now.day + day, hour=now.hour + start)
        end = localized_now().replace(day=now.day + day, hour=now.hour + end)

        login(self.portal, 'usuari.iescude')
        context.events.invokeFactory('Event', event_id, start=start, end=end, timezone=TZNAME, whole_day=False)
        logout()
        return context.events[event_id]

    def renderer(self, context=None, request=None, view=None, manager=None,
                 assignment=None):
        context = context or self.portal
        request = request or self.request
        view = view or context.restrictedTraverse('@@plone')
        manager = manager or getUtility(
            IPortletManager,
            name='plone.rightcolumn',
            context=self.portal
        )
        assignment = assignment or portlet_calendar.Assignment()

        return getMultiAdapter(
            (context, request, view, manager, assignment), IPortletRenderer
        )

    def test_nearest_event_today_only(self):
        test_community = self.create_test_community()
        event = self.create_event(test_community, 0, 2, 3)

        portlet = self.renderer(context=test_community, assignment=portlet_calendar.Assignment())
        login(self.portal, 'usuari.iescude')
        portlet.update()
        rd = portlet.render()

        near_event = portlet.get_nearest_today_event()

        self.assertTrue(near_event)
        self.assertTrue('e1' in rd)
        logout()

    def test_nearest_event_today_tomorrow(self):
        test_community = self.create_test_community()
        event = self.create_event(test_community, 1, 2, 3)

        portlet = self.renderer(context=test_community, assignment=portlet_calendar.Assignment())
        login(self.portal, 'usuari.iescude')
        portlet.update()
        rd = portlet.render()

        near_event = portlet.get_nearest_today_event()

        self.assertTrue(not near_event)
        self.assertTrue('e1' in rd)
        logout()

    def test_nearest_event_today_two_events(self):
        test_community = self.create_test_community()
        event = self.create_event(test_community, 0, 2, 3)
        event_must_not_show = self.create_event(test_community, 0, 4, 5, event_id='e2')

        portlet = self.renderer(context=test_community, assignment=portlet_calendar.Assignment())
        login(self.portal, 'usuari.iescude')
        portlet.update()
        rd = portlet.render()

        near_event = portlet.get_nearest_today_event()

        self.assertTrue(near_event.id == event.id)
        self.assertTrue('e1' in rd and 'e2' in rd)
        logout()

    def test_next_three_events_today_two_events(self):
        test_community = self.create_test_community()
        event = self.create_event(test_community, 0, 2, 3)
        event_must_show = self.create_event(test_community, 0, 4, 5, event_id='e2')

        portlet = self.renderer(context=test_community, assignment=portlet_calendar.Assignment())
        login(self.portal, 'usuari.iescude')
        portlet.update()
        rd = portlet.render()

        next_three_events = portlet.get_next_three_events()

        self.assertTrue(next_three_events[0].id == event_must_show.id)
        self.assertTrue('e1' in rd and 'e2' in rd)
        logout()

    def test_dayname(self):
        portlet = self.renderer(context=self.portal, assignment=portlet_calendar.Assignment())
        login(self.portal, 'usuari.iescude')
        portlet.update()
        rd = portlet.render()

        today = portlet.today()

        # self.assertTrue(near_event)
        # self.assertTrue('e1' in rd)
        logout()
