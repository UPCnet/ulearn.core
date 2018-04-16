# -*- coding: utf-8 -*-

import httplib2
import json
from os import path
from Acquisition import aq_inner
from apiclient.discovery import build
from datetime import datetime
from dateutil.relativedelta import relativedelta
from five import grok
from oauth2client.client import SignedJwtAssertionCredentials
from plone import api
from plone.app.layout.viewlets.content import ContentHistoryView
from Products.CMFCore.utils import _checkPermission, getToolByName
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

# ToDo list
###############################################################################
# 1. Internationalize strings that don't come from data (i18n)
###############################################################################

class statsOverview(grok.View):
    grok.context(IPloneSiteRoot)
    grok.name('stats_overview')
    grok.require('cmf.ManagePortal')

    workingDirectory = ""
    dateIntervals = []
    datePoints = ["1d", "15d", "1m", "3m", "6m", "1y", "+1y"]
    sections = ["Accessed", "Modified"]
    accessedIndex = 0
    separator = "/"
    dataset = {}

    def getDataset(self):
        return json.dumps(self.dataset, separators=(',', ':'))

    def getSeparator(self):
        return "\"%s\"" % self.separator

    def getAccumulatedTable(self, table):
        accTable = []
        for row in table:
            accTable.append([])
            for cell in row:
                accTable[-1].append(cell)
            for i in xrange(1, len(self.datePoints)):
                accTable[-1][i + 1] += accTable[-1][i]
        return accTable

    def getDateIntervals(self):

        def textToDate(text):
            unit = text[-1]
            value = -int(text[:-1])
            date = datetime.today()
            if unit == 'd':
                date += relativedelta(days=value)
            elif unit == 'm':
                date += relativedelta(months=value)
            elif unit == 'y':
                date += relativedelta(years=value)
            return date

        # by construction, the returned list is already sorted by default
        # use sorted([]) if self.datePoints isn't sorted
        return [textToDate(point) for point in self.datePoints[:-1]] + [datetime.min]

    def getAllAccessedTables(self, upToDate):

        def getStoredAnalytics():
            storedAnalytics = file(path.join(self.workingDirectory, "stats_overview.json"), "r")
            data = json.loads(storedAnalytics.read())
            storedAnalytics.close()
            return data

        def getUpToDateAnalytics(communityShortpaths):
            keyFile = file(path.join(self.workingDirectory, "stats_overview.p12"), 'rb')
            keyContents = keyFile.read()
            keyFile.close()

            credentials = SignedJwtAssertionCredentials(
                'comunitatsupc-python-analytics@'
                'comunitats-upc.iam.gserviceaccount.com',
                keyContents,
                scope='https://www.googleapis.com/auth/analytics.readonly',
            )
            http = credentials.authorize(httplib2.Http())
            service = build('analytics', 'v3', http=http)

            falsePrefixes = ['/8/comunitats',
                             '/acl_users/credentials_cookie_auth/require_login?'
                             'came_from=https://comunitats.upc.edu']

            gaFilters = ','.join('ga:pagePath=~/' + communityShortpath
                                 for communityShortpath in communityShortpaths)

            numResults = 0
            totalResults = 0
            first = True
            data = {}
            while numResults < totalResults or first:
                first = False
                dataQuery = service.data().ga().get(**{
                    'ids': 'ga:130554564',
                    'start_date': '2005-01-01',
                    'end_date': '9999-12-31',
                    'metrics': 'ga:pageviews',
                    'dimensions': 'ga:pagePath,ga:dateHourMinute',
                    'filters': gaFilters,
                    'max_results': '10000',
                    'start_index': str(numResults + 1),
                    'sort': 'ga:dateHourMinute'
                })
                analyticsData = dataQuery.execute()
                numResults += len(analyticsData['rows'])
                totalResults = int(analyticsData['totalResults'])

                # row := [communityShortpath, date, visits]
                for row in analyticsData['rows']:
                    for prefix in falsePrefixes:
                        row[0] = row[0].replace(prefix, '')
                    row[0] = row[0].split('/')[1].split('?')[0]
                    if not row[0] in data:
                        data[row[0]] = []
                    data[row[0]].append([row[1], int(row[2])])

            for communityShortpath in data:
                data[communityShortpath].reverse()

            storedAnalytics = file(path.join(self.workingDirectory, "stats_overview.json"), "wb")
            storedAnalytics.write(json.dumps(data, separators=(',', ':')))
            storedAnalytics.close()

            return data

        communityTitles = {}
        communityShortpaths = []
        for community in api.portal.get_tool(name='portal_catalog').unrestrictedSearchResults(portal_type='ulearn.community'):
            communityShortpath = community.getPath().split('/')[3]
            communityShortpaths.append(communityShortpath)
            communityTitles[communityShortpath] = community.Title

        if upToDate:
            data = getUpToDateAnalytics(communityShortpaths)
        else:
            data = getStoredAnalytics()

        accessedTable = []
        for communityShortpath in data:
            index = 0
            accessedTable.append([communityTitles[communityShortpath]]
                                 + [0] * len(self.datePoints))
            for entry in data[communityShortpath]:
                accessedDate = datetime.strptime(entry[0], "%Y%m%d%H%M%S")
                while accessedDate < self.dateIntervals[index]:
                    index += 1
                accessedTable[-1][index + 1] += entry[1]

        return [accessedTable, self.getAccumulatedTable(accessedTable)]

    def getAllModifiedTables(self):

        def fullHistory(file):
            context = file.getObject()
            result = [file.modified.asdatetime().replace(tzinfo=None),
                     file.created.asdatetime().replace(tzinfo=None)]

            pr = getToolByName(context, "portal_repository", None)
            if pr and pr.isVersionable(context):
                history = pr.getHistoryMetadata(context);
                if history:
                    for i in xrange(history.getLength(countPurged=False)):
                        result.append(datetime.fromtimestamp(
                            history.retrieve(i, countPurged=False)
                            ["metadata"]["sys_metadata"]["timestamp"]
                        ).replace(tzinfo=None))

            for workflow in context.workflow_history:
                for entry in context.workflow_history[workflow]:
                    result.append(entry["time"].asdatetime().
                                  replace(tzinfo=None))

            result.sort(reverse=True)
            return result

        modifiedTable = [[], []]
        catalog = api.portal.get_tool(name='portal_catalog')
        for community in catalog.unrestrictedSearchResults(
            portal_type='ulearn.community'):
            for i in xrange(len(modifiedTable)):
                modifiedTable[i].append([community.Title] + [0] * len(self.datePoints))
            for file in catalog.unrestrictedSearchResults(
                    path=community.getPath()):
                index = 0
                current = 0
                for entry in fullHistory(file):
                    while entry < self.dateIntervals[index]:
                        index += 1
                        current = 0
                    modifiedTable[0][-1][index + 1] += 1
                    current += 1
                    if current == 1:
                        modifiedTable[1][-1][index + 1] += 1

        modifiedAccTable = [self.getAccumulatedTable(table) for table in modifiedTable]

        returnTable = []
        returnAccTable = []
        for i in xrange(len(modifiedTable[0])):  # [0] or [1] or modAccTable[0] or mAT[1]
            returnTable.append([modifiedTable[0][i][0]])
            returnAccTable.append([modifiedAccTable[0][i][0]])
            for j in xrange(1, len(modifiedTable[0][i])):  # same as last comment
                returnTable[-1].append(str(modifiedTable[0][i][j]) + self.separator + str(modifiedTable[1][i][j]))
                returnAccTable[-1].append(str(modifiedAccTable[0][i][j]) + self.separator + str(modifiedAccTable[1][i][j]))

        return [returnTable, returnAccTable]

    def render(self):
        self.dateIntervals = self.getDateIntervals()
        self.workingDirectory = path.join(path.dirname(__file__))
        self.accessedIndex = 0
        self.dataset[self.sections[self.accessedIndex]] = self.getAllAccessedTables("update" in self.request.form)
        if "update" in self.request.form:
            return self.getDataset()
        self.dataset[self.sections[1 - self.accessedIndex]] = self.getAllModifiedTables()
        return ViewPageTemplateFile('stats_overview.pt')(self)
