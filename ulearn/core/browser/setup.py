# -*- coding: utf-8 -*-
from Acquisition import aq_inner
from five import grok
from zope.component import queryUtility
from zope.component import getUtility
from zope.component import getMultiAdapter
from zope.component.hooks import getSite
from souper.soup import get_soup
from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import IPortletAssignmentMapping
from plone.dexterity.utils import createContentInContainer
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.CMFPlone.interfaces.constrains import ISelectableConstrainTypes
from genweb.portlets.browser.manager import ISpanStorage
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone import api
from zope.interface import alsoProvides
from mrs.max.utilities import IMAXClient
from ulearn.core.api.people import Person
from genweb.core.utils import remove_user_from_catalog
from repoze.catalog.query import Eq
from genweb.core.gwuuid import IGWUUID
import transaction
from datetime import datetime
from plone.namedfile.file import NamedBlobFile
from ulearn.core.browser.sharing import IElasticSharing
from ulearn.core.content.community import ICommunity
from genweb.core.utils import json_response
from genweb.core.utilities import IElasticSearch
from ulearn.core.browser.sharing import ElasticSharing

import json

import logging
logger = logging.getLogger(__name__)


class setupHomePage(grok.View):
    grok.context(IPloneSiteRoot)
    grok.require('zope2.ViewManagementScreens')

    def render(self):
        portal = getSite()
        frontpage = portal['front-page']
        # Add portlets programatically
        target_manager = queryUtility(IPortletManager, name='genweb.portlets.HomePortletManager1', context=frontpage)
        target_manager_assignments = getMultiAdapter((frontpage, target_manager), IPortletAssignmentMapping)
        from ulearn.theme.portlets.profile import Assignment as profileAssignment
        from ulearn.theme.portlets.communities import Assignment as communitiesAssignment
        from ulearn.theme.portlets.thinnkers import Assignment as thinnkersAssignment
        from mrs.max.portlets.maxui import Assignment as maxAssignment
        from ulearn.theme.portlets.homebuttonbar import Assignment as homebuttonbarAssignment
        from ulearn.theme.portlets.calendar import Assignment as calendarAssignment
        from ulearn.theme.portlets.stats import Assignment as statsAssignment
        from ulearn.theme.portlets.econnect import Assignment as econnectAssignment
        from ulearn.theme.portlets.angularrouteview import Assignment as angularrouteviewAssignment

        target_manager_assignments['profile'] = profileAssignment()
        target_manager_assignments['communities'] = communitiesAssignment()
        target_manager_assignments['thinnkers'] = thinnkersAssignment()

        target_manager = queryUtility(IPortletManager, name='genweb.portlets.HomePortletManager3', context=frontpage)
        target_manager_assignments = getMultiAdapter((frontpage, target_manager), IPortletAssignmentMapping)
        target_manager_assignments['angularroute'] = angularrouteviewAssignment()
        target_manager_assignments['buttons'] = homebuttonbarAssignment()
        target_manager_assignments['max'] = maxAssignment()

        portletManager = getUtility(IPortletManager, 'genweb.portlets.HomePortletManager3')
        spanstorage = getMultiAdapter((frontpage, portletManager), ISpanStorage)
        spanstorage.span = '8'

        target_manager = queryUtility(IPortletManager, name='genweb.portlets.HomePortletManager4', context=frontpage)
        target_manager_assignments = getMultiAdapter((frontpage, target_manager), IPortletAssignmentMapping)
        target_manager_assignments['calendar'] = calendarAssignment()
        target_manager_assignments['stats'] = statsAssignment()
        target_manager_assignments['econnect'] = econnectAssignment()


class setupHomePageNews(grok.View):
    grok.context(IPloneSiteRoot)
    grok.require('zope2.ViewManagementScreens')

    def render(self):
        portal = getSite()
        frontpage = portal['front-page']
        # Add portlets programatically
        target_manager = queryUtility(IPortletManager, name='genweb.portlets.HomePortletManager1', context=frontpage)
        target_manager_assignments = getMultiAdapter((frontpage, target_manager), IPortletAssignmentMapping)
        from ulearn.theme.portlets.profile import Assignment as profileAssignment
        from ulearn.theme.portlets.communities import Assignment as communitiesAssignment
        from ulearn.theme.portlets.thinnkers import Assignment as thinnkersAssignment
        from mrs.max.portlets.maxui import Assignment as maxAssignment
        from ulearn.theme.portlets.flashesinformativos.flashesinformativos import Assignment as flashesinformativosAssignment
        from ulearn.theme.portlets.custombuttonbar.custombuttonbar import Assignment as custombuttonbarAssignment
        from ulearn.theme.portlets.mycommunities.mycommunities import Assignment as mycommunitiesAssignment
        from ulearn.theme.portlets.subscribednews.subscribednews import Assignment as subscribednewsAssignment
        from ulearn.theme.portlets.importantnews.importantnews import Assignment as importantnewsAssignment
        from ulearn.theme.portlets.calendar import Assignment as calendarAssignment
        from ulearn.theme.portlets.stats import Assignment as statsAssignment
        from ulearn.theme.portlets.econnect import Assignment as econnectAssignment
        from ulearn.theme.portlets.angularrouteview import Assignment as angularrouteviewAssignment

        target_manager_assignments['profile'] = profileAssignment()
        target_manager_assignments['communities'] = communitiesAssignment()
        target_manager_assignments['thinnkers'] = thinnkersAssignment()

        target_manager = queryUtility(IPortletManager, name='genweb.portlets.HomePortletManager3', context=frontpage)
        target_manager_assignments = getMultiAdapter((frontpage, target_manager), IPortletAssignmentMapping)
        target_manager_assignments['angularroute'] = angularrouteviewAssignment()
        target_manager_assignments['flashesinformativos'] = flashesinformativosAssignment()
        target_manager_assignments['custombuttons'] = custombuttonbarAssignment()
        target_manager_assignments['mycommunities'] = mycommunitiesAssignment()
        target_manager_assignments['my-subscribed-news'] = subscribednewsAssignment()
        target_manager_assignments['max'] = maxAssignment()

        portletManager = getUtility(IPortletManager, 'genweb.portlets.HomePortletManager3')
        spanstorage = getMultiAdapter((frontpage, portletManager), ISpanStorage)
        spanstorage.span = '8'

        target_manager = queryUtility(IPortletManager, name='genweb.portlets.HomePortletManager4', context=frontpage)
        target_manager_assignments = getMultiAdapter((frontpage, target_manager), IPortletAssignmentMapping)
        target_manager_assignments['importantnews'] = importantnewsAssignment()
        target_manager_assignments['calendar'] = calendarAssignment()
        target_manager_assignments['stats'] = statsAssignment()
        target_manager_assignments['econnect'] = econnectAssignment()


class createMenuFolders(grok.View):
    grok.context(IPloneSiteRoot)
    grok.require('zope2.ViewManagementScreens')

    def createOrGetObject(self, context, newid, title, type_name):
        if newid in context.contentIds():
            obj = context[newid]
        else:
            obj = createContentInContainer(context, type_name, title=title, checkConstrains=False)
            transaction.savepoint()
            if obj.id != newid:
                context.manage_renameObject(obj.id, newid)
            obj.reindexObject()
        return obj

    def newPrivateFolder(self, context, newid, title):
        return self.createOrGetObject(context, newid, title, u'privateFolder')

    def render(self):
        portal = getSite()
        gestion = self.newPrivateFolder(portal, 'gestion', u'Gestión')
        gestion.exclude_from_nav = False
        gestion.setLayout('folder_listing')
        behavior = ISelectableConstrainTypes(gestion)
        behavior.setConstrainTypesMode(1)
        behavior.setLocallyAllowedTypes(('Folder', 'privateFolder',))
        behavior.setImmediatelyAddableTypes(('Folder', 'privateFolder',))

        enlaces_cabecera = self.newPrivateFolder(gestion, 'menu', u'Menu')
        enlaces_cabecera.exclude_from_nav = False
        enlaces_cabecera.reindexObject()

        for language in portal['portal_languages'].getSupportedLanguages():
            language_folder = self.newPrivateFolder(enlaces_cabecera, language, language)
            language_folder.exclude_from_nav = False
            language_folder.reindexObject()
            behavior = ISelectableConstrainTypes(language_folder)
            behavior.setConstrainTypesMode(1)
            behavior.setLocallyAllowedTypes(('Folder', 'privateFolder', 'Link',))
            behavior.setImmediatelyAddableTypes(('Folder', 'privateFolder', 'Link',))


class ldapkillah(grok.View):
    grok.context(IPloneSiteRoot)
    grok.require('zope2.ViewManagementScreens')

    def render(self):
        portal = getSite()

        if getattr(portal.acl_users, 'ldapUPC', None):
            portal.acl_users.manage_delObjects('ldapUPC')

        if getattr(portal.acl_users, 'ldapexterns', None):
            portal.acl_users.manage_delObjects('ldapexterns')


class memberFolderSetup(grok.View):
    grok.context(IPloneSiteRoot)
    grok.require('zope2.ViewManagementScreens')

    def render(self):
        portal = getSite()
        if not getattr(portal, 'users', None):
            users_folder = createContentInContainer(portal, 'Folder', title='users', checkConstraints=False)
            users_folder.setDefaultPage('member_search_form')
            portal.manage_delObjects('Members')


class changeURLCommunities(grok.View):
    """ Aquesta vista canvia la url de les comunitats """
    grok.name('changeurlcommunities')
    grok.context(IPloneSiteRoot)

    render = ViewPageTemplateFile('views_templates/changeurlcommunities.pt')

    def update(self):
        try:
            from plone.protect.interfaces import IDisableCSRFProtection
            alsoProvides(self.request, IDisableCSRFProtection)
        except:
            pass
        if self.request.environ['REQUEST_METHOD'] == 'POST':
            pc = api.portal.get_tool('portal_catalog')
            communities = pc.searchResults(portal_type='ulearn.community')

            if self.request.form['url'] != '':
                url_nova = self.request.form['url']
                url_antiga = self.request.form['url_antiga']
                self.context.plone_log('Cercant comunitats per modificar la url...')

                for brain in communities:
                    obj = brain.getObject()
                    community = obj.adapted()
                    community_url = url_antiga + '/' + obj.id
                    community_url_nova = url_nova + '/' + obj.id
                    properties_to_update = dict(url=community_url_nova)

                    community.maxclient.contexts[community_url].put(**properties_to_update)
                    self.context.plone_log('Comunitat amb url: {} - Actualitzada per: {}'.format(community_url, community_url_nova))


class deleteUsers(grok.View):
    """ Delete users from the plone & max & communities """
    grok.name('deleteusers')
    grok.context(IPloneSiteRoot)

    render = ViewPageTemplateFile('views_templates/deleteusers.pt')

    def update(self):
        try:
            from plone.protect.interfaces import IDisableCSRFProtection
            alsoProvides(self.request, IDisableCSRFProtection)
        except:
            pass
        if self.request.environ['REQUEST_METHOD'] == 'POST':

            if self.request.form['users'] != '':
                users = self.request.form['users'].split(',')

                for user in users:
                    user = user.strip()
                    try:
                        person = Person(self.context, [user])
                        person.deleteMembers([user])
                        remove_user_from_catalog(user.lower())
                        pc = api.portal.get_tool(name='portal_catalog')
                        username = user
                        communities = pc.unrestrictedSearchResults(portal_type="ulearn.community")
                        for num, community in enumerate(communities):
                            obj = community._unrestrictedGetObject()
                            self.context.plone_log('Processant {} de {}. Comunitat {}'.format(num, len(communities), obj))
                            gwuuid = IGWUUID(obj).get()
                            portal = api.portal.get()
                            soup = get_soup('communities_acl', portal)

                            records = [r for r in soup.query(Eq('gwuuid', gwuuid))]

                            # Save ACL into the communities_acl soup
                            if records:
                                acl_record = records[0]
                                acl = acl_record.attrs['acl']
                                exist = [a for a in acl['users'] if a['id'] == unicode(username)]
                                if exist:
                                    acl['users'].remove(exist[0])
                                    acl_record.attrs['acl'] = acl
                                    soup.reindex(records=[acl_record])
                                    adapter = obj.adapted()
                                    adapter.set_plone_permissions(adapter.get_acl())

                        maxclient, settings = getUtility(IMAXClient)()
                        maxclient.setActor(settings.max_restricted_username)
                        maxclient.setToken(settings.max_restricted_token)
                        maxclient.people[username].delete()
                        logger.info('Deleted user: {}'.format(user))
                    except:
                        logger.error('User not deleted: {}'.format(user))
                        pass

                logger.info('Finished process. Deleted users: {}'.format(users))


class deleteUsersInCommunities(grok.View):
    """ Delete users from the plone & max & communities """
    grok.name('deleteusersincommunities')
    grok.context(IPloneSiteRoot)

    render = ViewPageTemplateFile('views_templates/deleteusersincommunities.pt')

    def update(self):
        try:
            from plone.protect.interfaces import IDisableCSRFProtection
            alsoProvides(self.request, IDisableCSRFProtection)
        except:
            pass

        if self.request.environ['REQUEST_METHOD'] == 'POST':

            if self.request.form['users'] != '':
                users = self.request.form['users'].split(',')

                for user in users:
                    user = user.strip()
                    try:
                        pc = api.portal.get_tool(name='portal_catalog')
                        username = user
                        communities = pc.unrestrictedSearchResults(portal_type="ulearn.community")
                        for num, community in enumerate(communities):
                            obj = community._unrestrictedGetObject()
                            self.context.plone_log('Processant {} de {}. Comunitat {}'.format(num, len(communities), obj))
                            gwuuid = IGWUUID(obj).get()
                            portal = api.portal.get()
                            soup = get_soup('communities_acl', portal)

                            records = [r for r in soup.query(Eq('gwuuid', gwuuid))]

                            # Save ACL into the communities_acl soup
                            if records:
                                acl_record = records[0]
                                acl = acl_record.attrs['acl']
                                exist = [a for a in acl['users'] if a['id'] == unicode(username)]
                                if exist:
                                    acl['users'].remove(exist[0])
                                    acl_record.attrs['acl'] = acl
                                    soup.reindex(records=[acl_record])
                                    adapter = obj.adapted()
                                    adapter.set_plone_permissions(adapter.get_acl())

                        logger.info('Deleted user in communities: {}'.format(user))
                    except:
                        logger.error('User not deleted in communities: {}'.format(user))
                        pass

                logger.info('Finished. Deleted users from communities: {}'.format(users))


def getDestinationFolder(stats_folder, create_month=True):
    """
    This function creates if it doesn't exist a folder in <stats_folder>/<year>/<month>.
    If  create_month is False, then only the <year> folder is created
    """
    portal = api.portal.get()
    # Create 'stats_folder' folder if not exists
    for stats_folder_part in stats_folder.split('/'):
        if portal.get(stats_folder_part) is None:
            makeFolder(portal, stats_folder_part)
        portal = portal.get(stats_folder_part)

    today = datetime.now()
    # context = aq_inner(portal)
    # tool = getToolByName(context, 'translation_service')
    # month = tool.translate(today.strftime("%B"), 'ulearn', context=context).encode()
    month = 'march'
    month = month.lower()
    year = today.strftime("%G")
    # Create year folder and month folder if not exists
    if portal.get(year) is None:
        makeFolder(portal, year)
        if create_month:
            portal = portal.get(year)
            makeFolder(portal, month)
    # Create month folder if not exists
    else:
        portal = portal.get(year)
        if portal.get(month) is None and create_month:
            makeFolder(portal, month)
            portal = portal.get(month)
    return portal


def makeFolder(portal, name):
    transaction.begin()
    obj = createContentInContainer(portal, 'Folder', id='{}'.format(name), title='{}'.format(name), description='{}'.format(name))
    obj.reindexObject()
    transaction.commit()


class ImportFileToFolder(grok.View):
    """
    This view takes 2 arguments on the request GET data :
    folder: the path without the '/' at the beginning, which is the base folder
        where the 'year' folders should be created
    local_file: the complete path and filename of the file on server. Be carefully if the view is called
        and there are many instanes. The best way is to call it through <ip>:<instance_port>

    To test it: run python script with requests and:
    payload={'folder':'test','local_file': '/home/vicente.iranzo/mongodb_VPN_2016_upcnet.xls'}
    r = requests.post('http://localhost:8080/Plone/importfiletofolder', params=payload, auth=HTTPBasicAuth('admin', 'admin'))
    """
    grok.context(IPloneSiteRoot)
    grok.name('importfiletofolder')
    grok.require('genweb.webmaster')

    render = ViewPageTemplateFile('views_templates/importfiletofolder.pt')

    def update(self):
        try:
            from plone.protect.interfaces import IDisableCSRFProtection
            alsoProvides(self.request, IDisableCSRFProtection)
        except:
            pass
        if self.request.environ['REQUEST_METHOD'] == 'POST':
            portal = api.portal.get()
            folder_name = self.request.get("folder")
            local_file = self.request.get("local_file")

            f = open(local_file, 'r')
            content = f.read()
            f.close()

            for folder_name_part in folder_name.split('/'):
                if portal.get(folder_name_part) is None:
                    makeFolder(portal, folder_name_part)
                portal = portal.get(folder_name_part)

            file = NamedBlobFile(
                data=content,
                filename=u'{}'.format(local_file),
                contentType='application/xls'
            )
            createContentInContainer(
                portal,
                'AppFile',
                id='{}'.format(local_file.split('/')[-1]),
                title='{}'.format(local_file.split('/')[-1]),
                file=file,
                checkConstraints=False
            )


class listAllCommunitiesObjects(grok.View):
    """ returns a json with all the comunities and the number of objects of each one"""
    grok.name('listallcommunitiesobjects')
    grok.context(IPloneSiteRoot)
    # only for admin users
    grok.require('cmf.ManagePortal')

    def render(self):
        pc = api.portal.get_tool(name='portal_catalog')
        communities = pc.unrestrictedSearchResults(portal_type="ulearn.community")
        result_list = []
        for num, community in enumerate(communities):
            num_docs = len(pc(path={"query": community.getPath(), "depth": 2}))
            new_com = {"community_name": community.getPath(),
                       "community_docs": str(num_docs),
                       }
            result_list.append(new_com)
        return json.dumps(result_list)


class updateSharingCommunityElastic(grok.View):
    """ Aquesta vista actualitza tots els objectes de la comunitat al elasticsearch """
    grok.name('updatesharingcommunityelastic')
    grok.context(IPloneSiteRoot)

    render = ViewPageTemplateFile('views_templates/updatesharingcommunityelastic.pt')

    def update(self):
        try:
            from plone.protect.interfaces import IDisableCSRFProtection
            alsoProvides(self.request, IDisableCSRFProtection)
        except:
            pass
        if self.request.environ['REQUEST_METHOD'] == 'POST':
            pc = api.portal.get_tool('portal_catalog')
            portal = getSite()
            absolute_path = '/'.join(portal.getPhysicalPath())

            if self.request.form['id'] != '':
                id_community = absolute_path + '/' + self.request.form['id']
                self.context.plone_log('Actualitzant Elasticsearch dades comunitat {}'.format(id_community))
                community = pc.unrestrictedSearchResults(path=id_community)

                if community:
                    obj = community[0]._unrestrictedGetObject()

                try:
                    self.elastic = getUtility(IElasticSearch)
                    self.elastic().search(index=ElasticSharing().get_index_name())
                except:
                    self.elastic().indices.create(
                        index=ElasticSharing().get_index_name(),
                        body={
                            'mappings': {
                                'sharing': {
                                    'properties': {
                                        'path': {'type': 'string'},
                                        'principal': {'type': 'string', 'index': 'not_analyzed'},
                                        'roles': {'type': 'string'},
                                        'uuid': {'type': 'string'}
                                    }
                                }
                            }
                        }
                    )

                for brain in community:
                    obj = brain._unrestrictedGetObject()
                    if not ICommunity.providedBy(obj):
                        elastic_sharing = queryUtility(IElasticSharing)
                        elastic_sharing.modified(obj)
                        self.context.plone_log('Actualitzat objecte: {}, de la comunitat: {}'.format(obj, id_community))


class updateSharingCommunitiesElastic(grok.View):
    """ Aquesta vista actualitza el sharing de tots els objectes de totes les comunitats al elasticsearch """
    grok.name('updatesharingcommunitieselastic')
    grok.context(IPloneSiteRoot)

    def render(self):
        try:
            from plone.protect.interfaces import IDisableCSRFProtection
            alsoProvides(self.request, IDisableCSRFProtection)
        except:
            pass

        pc = api.portal.get_tool('portal_catalog')
        portal = getSite()
        absolute_path = '/'.join(portal.getPhysicalPath())

        communities = pc.unrestrictedSearchResults(portal_type="ulearn.community")
        for num, community in enumerate(communities):
            obj = community._unrestrictedGetObject()
            id_community = absolute_path + '/' + obj.id
            self.context.plone_log('Processant {} de {}. Comunitat {}'.format(num, len(communities), obj))
            community = pc.unrestrictedSearchResults(path=id_community)

            try:
                self.elastic = getUtility(IElasticSearch)
                self.elastic().search(index=ElasticSharing().get_index_name())
            except:
                self.elastic().indices.create(
                    index=ElasticSharing().get_index_name(),
                    body={
                        'mappings': {
                            'sharing': {
                                'properties': {
                                    'path': {'type': 'string'},
                                    'principal': {'type': 'string', 'index': 'not_analyzed'},
                                    'roles': {'type': 'string'},
                                    'uuid': {'type': 'string'}
                                }
                            }
                        }
                    }
                )

            for brain in community:
                obj = brain._unrestrictedGetObject()
                if not ICommunity.providedBy(obj):
                    elastic_sharing = queryUtility(IElasticSharing)
                    elastic_sharing.modified(obj)

                    self.context.plone_log('Actualitzat objecte: {}, de la comunitat: {}'.format(obj, id_community))

        logger.info('Finished update sharing in communities: {}'.format(portal.absolute_url()))
        self.response.setBody('OK')


class createElasticSharing(grok.View):
    """ Aquesta vista crea l'index de l'elasticsearch i li diu que el camp principal pot tenir caracters especials 'index': 'not_analyzed' """
    grok.name('createelasticsharing')
    grok.context(IPloneSiteRoot)

    def render(self):
        try:
            from plone.protect.interfaces import IDisableCSRFProtection
            alsoProvides(self.request, IDisableCSRFProtection)
        except:
            pass

        try:
            self.elastic = getUtility(IElasticSearch)
            self.elastic().search(index=ElasticSharing().get_index_name())
        except:
            self.elastic().indices.create(
                index=ElasticSharing().get_index_name(),
                body={
                    'mappings': {
                        'sharing': {
                            'properties': {
                                'path': {'type': 'string'},
                                'principal': {'type': 'string', 'index': 'not_analyzed'},
                                'roles': {'type': 'string'},
                                'uuid': {'type': 'string'}
                            }
                        }
                    }
                }
            )

            self.response.setBody('OK')


class viewUsersWithNotUpdatedPhoto(grok.View):
    grok.context(IPloneSiteRoot)
    grok.require('zope2.ViewManagementScreens')

    @json_response
    def render(self):
        portal = api.portal.get()
        soup = get_soup('user_properties', portal)
        records = [r for r in soup.data.items()]

        result = {}
        for record in records:
            userID = record[1].attrs['id']
            if userID != 'admin':
                mtool = getToolByName(self.context, 'portal_membership')
                portrait = mtool.getPersonalPortrait(userID)
                typePortrait = portrait.__class__.__name__
                if typePortrait == 'FSImage' or (typePortrait == 'Image' and portrait.size == 9715 or portrait.size == 4831):
                    fullname = record[1].attrs['fullname'] if 'fullname' in record[1].attrs else ''
                    userInfo = {'fullname' : fullname}
                    result[userID] = userInfo

        return result


class deletePhotoFromUser(grok.View):
    """ Delete photo from user, add parameter ?user=nom.cognom """
    grok.name('deletephotofromuser')
    grok.context(IPloneSiteRoot)
    grok.require('zope2.ViewManagementScreens')

    def render(self):
        # /deleteUserPhoto?user=nom.cognom
        try:
            from plone.protect.interfaces import IDisableCSRFProtection
            alsoProvides(self.request, IDisableCSRFProtection)
        except:
            pass

        if 'user' in self.request.form and self.request.form['user'] != '':
            user = api.user.get(username=self.request.form['user'])
            if user:
                context = aq_inner(self.context)
                try:
                    context.portal_membership.deletePersonalPortrait(self.request.form['user'])
                    return 'Done, photo has been removed from user ' + self.request.form['user']
                except:
                    return 'Error while deleting photo from user ' + self.request.form['user']
            else:
                return 'Error, user ' + self.request.form['user'] + ' not exist'
        else:
            return 'Add parameter ?user=nom.cognom in url'
