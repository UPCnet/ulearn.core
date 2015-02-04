# -*- coding: utf-8 -*-
from five import grok
from zope.interface import Interface

from Products.CMFCore.utils import getToolByName
from zope.component import getUtility

from ulearn.core import _
from ulearn.theme.browser.interfaces import IUlearnTheme
from datetime import datetime

from mrs.max.utilities import IMAXClient

import json
import calendar


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


STATS = ['activity', 'comments', 'documents', 'links', 'media']


class StatsQuery(grok.View):
    grok.context(Interface)
    grok.name('ulearn-stats')
    grok.require('genweb.authenticated')
    grok.layer(IUlearnTheme)

    def __init__(self, context, request):
        super(StatsQuery, self).__init__(context, request)
        catalog = getToolByName(context, 'portal_catalog')
        self.plone_stats = PloneStats(catalog)
        self.max_stats = MaxStats(self.get_max_client())

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
        search_filters['keywords'] = self.request.form.get('keywords', None)
        search_filters['access_type'] = self.request.form.get('access_type', None)

        # Dates MUST follow YYYY-MM Format
        start_filter = self.request.form.get('start', '{0}-01'.format(*datetime.now().timetuple()))
        end_filter = self.request.form.get('end', '{0}-12'.format(*datetime.now().timetuple()))

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
            current = next_month(current)
            row = [current.month, ]
            for stat_type in STATS:
                value = self.get_stats(
                    stat_type,
                    search_filters,
                    start=first_moment_of_month(current),
                    end=last_moment_of_month(current))
                row.append(value)
            results['rows'].append(row)

        self.request.response.setHeader("Content-type", "application/json")
        return json.dumps(results)


class PloneStats(object):
    """
    """
    def __init__(self, catalog):
        self.catalog = catalog

    def stat_documents(self, filters, start, end):
        """
        """

        if filters['community'] is not None:
            community = self.catalog.searchResults(portal_type='ulearn.community',
                                                   id=filters['community']
                                                   )
            folder_path = community[0].getPath() + '/documents'
        else:
            communities = self.catalog.searchResults(portal_type='ulearn.community')
            folder_path = []
            for c in communities:
                community = c.getPath() + '/documents'
                folder_path.append(community)

        date_range_query = {'query': (start, end), 'range': 'min:max'}

        if filters['user'] is not None and filters['keywords'] is None:
            results = self.catalog.searchResults(path={'query': folder_path, 'depth': 2},
                                                 Creator=filters['user'],
                                                 created=date_range_query
                                                 )

        if filters['keywords'] is not None and filters['user'] is None:
            results = self.catalog.searchResults(path={'query': folder_path, 'depth': 2},
                                                 Subject={'query': filters['keywords'], 'operator': 'or'},
                                                 created=date_range_query
                                                 )

        if filters['user'] is not None and filters['keywords'] is not None:
            results = self.catalog.searchResults(path={'query': folder_path, 'depth': 2},
                                                 Creator=filters['user'],
                                                 Subject={'query': filters['keywords'], 'operator': 'or'},
                                                 created=date_range_query
                                                 )

        if filters['user'] is None and filters['keywords'] is None:
            results = self.catalog.searchResults(path={'query': folder_path, 'depth': 2},
                                                 created=date_range_query
                                                 )

        return results.actual_result_count

    def stat_links(self, filters, start, end):
        """
        """

        if filters['community'] is not None:
            community = self.catalog.searchResults(portal_type='ulearn.community',
                                                   id=filters['community']
                                                   )
            folder_path = community[0].getPath() + '/links'
        else:
            communities = self.catalog.searchResults(portal_type='ulearn.community')
            folder_path = []
            for c in communities:
                community = c.getPath() + '/links'
                folder_path.append(community)

        date_range_query = {'query': (start, end), 'range': 'min:max'}

        if filters['user'] is not None and filters['keywords'] is None:
            results = self.catalog.searchResults(path={'query': folder_path, 'depth': 2},
                                                 Creator=filters['user'],
                                                 created=date_range_query
                                                 )

        if filters['keywords'] is not None and filters['user'] is None:
            results = self.catalog.searchResults(path={'query': folder_path, 'depth': 2},
                                                 Subject={'query': filters['keywords'], 'operator': 'or'},
                                                 created=date_range_query
                                                 )

        if filters['user'] is not None and filters['keywords'] is not None:
            results = self.catalog.searchResults(path={'query': folder_path, 'depth': 2},
                                                 Creator=filters['user'],
                                                 Subject={'query': filters['keywords'], 'operator': 'or'},
                                                 created=date_range_query
                                                 )

        if filters['user'] is None and filters['keywords'] is None:
            results = self.catalog.searchResults(path={'query': folder_path, 'depth': 2},
                                                 created=date_range_query
                                                 )

        return results.actual_result_count

    def stat_media(self, filters, start, end):
        """
        """

        if filters['community'] is not None:
            community = self.catalog.searchResults(portal_type='ulearn.community',
                                                   id=filters['community']
                                                   )
            folder_path = community[0].getPath() + '/media'
        else:
            communities = self.catalog.searchResults(portal_type='ulearn.community')
            folder_path = []
            for c in communities:
                community = c.getPath() + '/media'
                folder_path.append(community)

        date_range_query = {'query': (start, end), 'range': 'min:max'}

        if filters['user'] is not None and filters['keywords'] is None:
            results = self.catalog.searchResults(path={'query': folder_path, 'depth': 2},
                                                 Creator=filters['user'],
                                                 created=date_range_query
                                                 )

        if filters['keywords'] is not None and filters['user'] is None:
            results = self.catalog.searchResults(path={'query': folder_path, 'depth': 2},
                                                 Subject={'query': filters['keywords'], 'operator': 'or'},
                                                 created=date_range_query
                                                 )

        if filters['user'] is not None and filters['keywords'] is not None:
            results = self.catalog.searchResults(path={'query': folder_path, 'depth': 2},
                                                 Creator=filters['user'],
                                                 Subject={'query': filters['keywords'], 'operator': 'or'},
                                                 created=date_range_query
                                                 )

        if filters['user'] is None and filters['keywords'] is None:
            results = self.catalog.searchResults(path={'query': folder_path, 'depth': 2},
                                                 created=date_range_query
                                                 )

        return results.actual_result_count


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
