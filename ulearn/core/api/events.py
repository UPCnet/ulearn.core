from five import grok
from Products.CMFPlone.interfaces import IPloneSiteRoot
from genweb.core.utils import json_response
from ulearn.core.api import REST
from ulearn.core.api.root import APIRoot
from plone.dexterity.utils import createContentInContainer
from plone.app.contenttypes.behaviors.richtext import IRichText
from datetime import datetime
from plone import api


class Events(REST):
    """
        /api/events
    """

    placeholder_type = 'event'
    placeholder_id = 'eventid'

    grok.adapts(APIRoot, IPloneSiteRoot)
    grok.require('genweb.authenticated')


class Event(REST):
    """
        /api/events/{eventid}
    """
    grok.adapts(Events, IPloneSiteRoot)
    grok.require('genweb.authenticated')

    def __init__(self, context, request):
        super(Event, self).__init__(context, request)

    def POST(self):

        validation = self.validate()
        if validation is not True:
            return validation

        eventid = self.params.pop('eventid')
        title = self.params.pop('title')
        desc = self.params.pop('description')
        body = self.params.pop('body')
        date_start = self.params.pop('start')
        date_end = self.params.pop('end')

        result = self.create_event(eventid,
                                   title,
                                   desc,
                                   body,
                                   date_start,
                                   date_end)

        self.response.setStatus(result.pop('status'))
        return self.json_response(result)

    def create_event(self, eventid, title, desc, body, date_start, date_end):
        date_start = date_start.split('/')
        time_start = date_start[3].split(':')
        date_end = date_end.split('/')
        time_end = date_end[3].split(':')
        portal_url = api.portal.get()
        news_url = portal_url['events']
        pc = api.portal.get_tool('portal_catalog')
        brains = pc.unrestrictedSearchResults(portal_type='Event', id=eventid)
        if not brains:
            new_event = createContentInContainer(news_url,
                                                 'Event',
                                                 title=eventid,
                                                 start=datetime(int(date_start[2]),
                                                                int(date_start[1]),
                                                                int(date_start[0]),
                                                                int(time_start[0]),
                                                                int(time_start[1])
                                                                ),
                                                 end=datetime(int(date_end[2]),
                                                              int(date_end[1]),
                                                              int(date_end[0]),
                                                              int(time_end[0]),
                                                              int(time_end[1])
                                                              ),
                                                 timezone="Europe/Madrid",
                                                 checkConstraints=False)
            new_event.title = title
            new_event.description = desc
            new_event.text = IRichText['text'].fromUnicode(body)
            new_event.reindexObject()
            resp = {'message': 'Event {} created'.format(eventid), 'status': 201}
        else:
            event = brains[0].getObject()
            event.title = title
            event.text = IRichText['text'].fromUnicode(body)
            event.reindexObject()
            resp = {'message': 'Event {} updated'.format(eventid), 'status': 201}

        return resp
