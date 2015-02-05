# -*- coding: utf-8 -*-
from five import grok
from zope.interface import Interface

from Products.CMFCore.utils import getToolByName
from zope.component import getUtility

from plone.memoize.view import memoize_contextless
from ulearn.core import _
from zope.i18nmessageid import MessageFactory

_cal = MessageFactory('cmf_calendar')

from ulearn.theme.browser.interfaces import IUlearnTheme
from datetime import datetime
from zope.component.hooks import getSite

from mrs.max.utilities import IMAXClient

import json
import calendar

from zope.schema.interfaces import IVocabularyFactory


def next_month(current):
    next_month = 1 if current.month == 12 else current.month + 1
    next_year = current.year + 1 if next_month == 1 else current.year
    last_day_of_next_month = calendar.monthrange(next_year, next_month)[1]
    next_day = current.day if current.day <= last_day_of_next_month else last_day_of_next_month
    return current.replace(month=next_month, year=next_year, day=next_day)


def last_day_of_month(dt):
    return calendar.monthrange(dt.year, dt.month)[1]


def first_moment_of_month(dt):
    return dt.replace(day=1, hour=0, minute=0, second=0)


def last_moment_of_month(dt):
    return dt.replace(day=last_day_of_month(dt), hour=23, minute=59, second=59)


def last_twelve_months_range():
    current_year = datetime.now().year
    last_year = current_year - 1
    current_month = datetime.now().month
    last_year_month = 1 if current_month == 12 else current_month + 1

    return (last_year, last_year_month, current_year, current_month)

STATS = ['activity', 'comments', 'documents', 'links', 'media']


class StatsView(grok.View):
    grok.context(Interface)
    grok.name('ulearn-stats')
    grok.require('genweb.authenticated')
    grok.layer(IUlearnTheme)

    def __init__(self, context, request):
        super(StatsView, self).__init__(context, request)
        self.catalog = getToolByName(self.portal(), 'portal_catalog')

    @memoize_contextless
    def portal(self):
        return getSite()

    def get_communities(self):
        all_communities = [{'hash': 'all', 'title': 'Totes les comunitats'}]
        return all_communities + [{'hash': community.community_hash, 'title': community.Title} for community in self.catalog.searchResults(portal_type='ulearn.community')]

    def get_months(self):
        all_months = []
        vocab = getUtility(IVocabularyFactory,
                           name='plone.app.vocabularies.Month')
        for field in vocab(self.context):
            all_months += [{'value': field.value + 1, 'title': field.title}]

        return all_months


class StatsQuery(grok.View):
    grok.context(Interface)
    grok.name('ulearn-stats-query')
    grok.require('genweb.authenticated')
    grok.layer(IUlearnTheme)

    def __init__(self, context, request):
        super(StatsQuery, self).__init__(context, request)
        catalog = getToolByName(self.portal(), 'portal_catalog')
        self.plone_stats = PloneStats(catalog)
        self.max_stats = MaxStats(self.get_max_client())

    @memoize_contextless
    def portal(self):
        return getSite()

    def get_max_client(self):
        maxclient, settings = getUtility(IMAXClient)()
        maxclient.setActor(settings.max_restricted_username)
        maxclient.setToken(settings.max_restricted_token)

        return maxclient

    def get_stats(self, stat_type, filters, start, end):
        """
        """
        stat_method = 'stat_{}'.format(stat_type)

        # First try to get stats from plone itself
        if hasattr(self.plone_stats, stat_method):
            return getattr(self.plone_stats, stat_method)(filters, start, end)
        elif hasattr(self.max_stats, stat_method):
            return getattr(self.max_stats, stat_method)(filters, start, end)
        else:
            return 0

    def render(self):
        search_filters = {}

        search_filters['community'] = self.request.form.get('community', None)
        search_filters['user'] = self.request.form.get('user', None)
        search_filters['keywords'] = self.request.form.get('keywords[]', None)
        search_filters['access_type'] = self.request.form.get('access_type', None)

        # Dates MUST follow YYYY-MM Format
        start_filter = self.request.form.get('start', '').strip()
        start_filter = start_filter or '{0}-01'.format(*datetime.now().timetuple())
        end_filter = self.request.form.get('end', '').strip()
        end_filter = end_filter or '{0}-12'.format(*datetime.now().timetuple())

        startyear, startmonth = start_filter.split('-')
        endyear, endmonth = end_filter.split('-')

        startyear = int(startyear)
        startmonth = int(startmonth)
        endyear = int(endyear)
        endmonth = int(endmonth)

        startday = calendar.monthrange(startyear, startmonth)[1]
        endday = calendar.monthrange(endyear, endmonth)[1]

        start = datetime(startyear, startmonth, startday)
        end = datetime(endyear, endmonth, endday)

        if end < start:
            end == start

        results = {
            'headers': STATS,
            'rows': []
        }

        current = start
        while current <= end:
            row = [current.strftime('%B')]
            for stat_type in STATS:
                value = self.get_stats(
                    stat_type,
                    search_filters,
                    start=first_moment_of_month(current),
                    end=last_moment_of_month(current))
                row.append(value)
            results['rows'].append(row)
            current = next_month(current)

        self.request.response.setHeader("Content-type", "application/json")
        return json.dumps(results)


class PloneStats(object):
    """
    """
    def __init__(self, catalog):
        self.catalog = catalog

    def stat_by_folder(self, filters, start, end, search_folder):
        """
        """
        # Prepare filtes search to get all the
        # target communities
        catalog_filters = dict(
            portal_type='ulearn.community'
        )

        if filters['community']:
            catalog_filters['community_hash'] = filters['community']

        # List all paths of the resulting comunities
        communities = self.catalog.searchResults(**catalog_filters)
        folder_paths = ['{}/{}'.format(community.getPath(), search_folder) for community in communities]

        # Prepare filters for the final search
        catalog_filters = dict(
            path={'query': folder_paths, 'depth': 2},
            created={'query': (start, end), 'range': 'min:max'}
        )

        if filters['user']:
            catalog_filters['Creator'] = filters['user']

        if filters['keywords']:
            catalog_filters['SearchableText'] = {'query': filters['keywords'], 'operator': 'or'}

        results = self.catalog.searchResults(**catalog_filters)
        return results.actual_result_count

    def stat_documents(self, filters, start, end):
        """
        """
        return self.stat_by_folder(filters, start, end, 'documents')

    def stat_links(self, filters, start, end):
        """
        """
        return self.stat_by_folder(filters, start, end, 'links')

    def stat_media(self, filters, start, end):
        """
        """
        return self.stat_by_folder(filters, start, end, 'media')


class MaxStats(object):
    def __init__(self, maxclient):
        self.maxclient = maxclient

    def stat_activity(self, filters, start, end):
        """
        """
        return 4

    def stat_comments(self, filters, start, end):
        """
        """
        return 5
