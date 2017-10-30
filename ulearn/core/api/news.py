# -*- coding: utf-8 -*-
from five import grok
from Products.CMFPlone.interfaces import IPloneSiteRoot
from plone import api
from plone.app.contenttypes.behaviors.richtext import IRichText
from plone.dexterity.utils import createContentInContainer
from plone.namedfile.file import NamedBlobImage
from ulearn.core.api import ApiResponse
from ulearn.core.api import REST
from ulearn.core.api import api_resource
from ulearn.core.api.root import APIRoot
from datetime import datetime
from base64 import b64encode
from ulearn.core.api import ObjectNotFound
import requests


class News(REST):
    """
        /api/news
        and
        /api/news/NEW_ID

        Get all News by "X-Oauth-Username"
    """

    placeholder_type = 'new'
    placeholder_id = 'newid'

    grok.adapts(APIRoot, IPloneSiteRoot)
    grok.require('genweb.authenticated')

    @api_resource(required=[])
    def GET(self):
        show_news_in_app = api.portal.get_registry_record(name='ulearn.core.controlpanel.IUlearnControlPanelSettings.show_news_in_app')
        results = []
        news_per_page = 10  # Default items per page
        pagination_page = self.params.pop('page', None)
        if show_news_in_app:
            mountpoint_id = self.context.getPhysicalPath()[1]
            if mountpoint_id == self.context.id:
                default_path = api.portal.get().absolute_url_path() + '/news'
            else:
                default_path = '/' + mountpoint_id + '/' + api.portal.get().id + '/news'
            if pagination_page:
                # si page = 0, devolvemos la 1
                if pagination_page == '0':
                    pagination_page = 1
                start = int(news_per_page) * (int(pagination_page) - 1)
                end = int(news_per_page) * int(pagination_page)
                # Devolvemos paginado de 10 en 10
                news = api.content.find(
                    portal_type="News Item",
                    path=default_path,
                    sort_order='descending',
                    sort_on='effective',
                    is_inapp=True)[start:end]
            else:
                # No paginammos, solo devolvemos 10 primeras => ?page=1
                news = api.content.find(
                    portal_type="News Item",
                    path=default_path,
                    sort_order='descending',
                    sort_on='effective',
                    is_inapp=True)[0:10]
            for item in news:
                if item:
                    value = item.getObject()
                    if value.effective_date:
                        date = value.effective_date.strftime("%d/%m/%Y")
                    else:
                        date = value.creation_date.strftime("%d/%m/%Y")
                    if value.text:
                        text = value.text.output
                    else:
                        text = ''
                    is_inapp = getattr(item, 'is_inapp', None)
                    is_outoflist = getattr(item, 'is_outoflist', None)
                    is_flash = getattr(item, 'is_flash', None)
                    is_important = getattr(item, 'is_important', None)
                    new = dict(title=value.title,
                               id=value.id,
                               description=value.description,
                               path=item.getURL(),
                               absolute_url=value.absolute_url_path(),
                               text=text,
                               filename=value.image.filename,
                               caption=value.image_caption,
                               is_inapp=is_inapp,
                               is_outoflist=is_outoflist,
                               is_flash=is_flash,
                               is_important=is_important,
                               effective_date=date,
                               creators=value.creators,
                               raw_image=b64encode(value.image.data),
                               content_type=value.image.contentType,
                               )
                    results.append(new)

        return ApiResponse(results)


class New(REST):
    """
        /api/news/{newid}
    """
    grok.adapts(News, IPloneSiteRoot)
    grok.require('genweb.authenticated')

    def __init__(self, context, request):
        super(New, self).__init__(context, request)

    @api_resource(required=['newid', 'title', 'description', 'body', 'start'])
    def POST(self):
        imgName = ''
        imgData = ''
        newid = self.params.pop('newid')
        title = self.params.pop('title')
        desc = self.params.pop('description')
        body = self.params.pop('body')
        date_start = self.params.pop('start')
        date_end = self.params.pop('end', None)
        img = self.params.pop('imgUrl', None)
        if img:
            imgName = (img.split('/')[-1]).decode('utf-8')
            imgData = requests.get(img).content

        result = self.create_new(newid,
                                 title,
                                 desc,
                                 body,
                                 imgData,
                                 imgName,
                                 date_start,
                                 date_end)

        return result

    @api_resource(required=['newid'])
    def GET(self):
        newid = self.params['newid']
        mountpoint_id = self.context.getPhysicalPath()[1]
        if mountpoint_id == self.context.id:
            default_path = api.portal.get().absolute_url_path() + '/news'
        else:
            default_path = '/' + mountpoint_id + '/' + api.portal.get().id + '/news'
        item = api.content.find(portal_type="News Item", path=default_path, id=newid)
        if item:
            newitem = item[0]
            value = newitem.getObject()
            if value.effective_date:
                date = value.effective_date.strftime("%d/%m/%Y")
            else:
                date = value.creation_date.strftime("%d/%m/%Y")
            new = dict(title=value.title,
                       id=value.id,
                       description=value.description,
                       path=value.absolute_url(),
                       absolute_url=value.absolute_url_path(),
                       text=value.text.output,
                       filename=value.image.filename,
                       caption=value.image_caption,
                       is_inapp=newitem.is_inapp,
                       is_outoflist=newitem.is_outoflist,
                       is_flash=newitem.is_flash,
                       is_important=newitem.is_important,
                       effective_date=date,
                       creators=value.creators,
                       raw_image=b64encode(value.image.data),
                       content_type=value.image.contentType,
                       )
        else:
            raise ObjectNotFound('News Item not found')

        return ApiResponse(new)

    def create_new(self, newid, title, desc, body, imgData, imgName, date_start, date_end):
        date_start = date_start.split('/')
        time_start = date_start[3].split(':')

        portal_url = api.portal.get()
        news_url = portal_url['news']
        pc = api.portal.get_tool('portal_catalog')
        brains = pc.unrestrictedSearchResults(portal_type='News Item', id=newid)
        if not brains:
            if imgName != '':
                new_new = createContentInContainer(news_url,
                                                   'News Item',
                                                   title=newid,
                                                   image=NamedBlobImage(data=imgData,
                                                                        filename=imgName,
                                                                        contentType='image/jpeg'),
                                                   description=desc,
                                                   timezone="Europe/Madrid",
                                                   checkConstraints=False)
            else:
                new_new = createContentInContainer(news_url,
                                                   'News Item',
                                                   title=newid,
                                                   description=desc,
                                                   timezone="Europe/Madrid",
                                                   checkConstraints=False)
            new_new.title = title
            new_new.setEffectiveDate(datetime(int(date_start[2]),
                                              int(date_start[1]),
                                              int(date_start[0]),
                                              int(time_start[0]),
                                              int(time_start[1])
                                              )
                                     )
            if date_end:
                date_end = date_end.split('/')
                time_end = date_end[3].split(':')
                new_new.setExpirationDate(datetime(int(date_end[2]),
                                                   int(date_end[1]),
                                                   int(date_end[0]),
                                                   int(time_end[0]),
                                                   int(time_end[1])
                                                   )
                                          )
            new_new.text = IRichText['text'].fromUnicode(body)
            new_new.reindexObject()
            resp = ApiResponse.from_string('News Item {} created'.format(newid), code=201)
        else:
            new = brains[0].getObject()
            new.title = title
            new.description = desc
            new.setEffectiveDate(datetime(int(date_start[2]),
                                          int(date_start[1]),
                                          int(date_start[0]),
                                          int(time_start[0]),
                                          int(time_start[1])
                                          )
                                 )
            if date_end:
                new.setExpirationDate(datetime(int(date_end[2]),
                                               int(date_end[1]),
                                               int(date_end[0]),
                                               int(time_end[0]),
                                               int(time_end[1])
                                               )
                                      )
            if imgName != '':
                new.image = NamedBlobImage(data=imgData,
                                           filename=imgName,
                                           contentType='image/jpeg')
            new.text = IRichText['text'].fromUnicode(body)
            new.reindexObject()
            resp = ApiResponse.from_string('News Item {} updated'.format(newid), code=200)

        return resp
