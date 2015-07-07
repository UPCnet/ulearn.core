from five import grok
from Products.CMFPlone.interfaces import IPloneSiteRoot
from genweb.core.utils import json_response
from ulearn.core.api import REST
from ulearn.core.api.root import APIRoot
from plone.namedfile.file import NamedBlobImage
from plone.dexterity.utils import createContentInContainer
from plone.app.contenttypes.behaviors.richtext import IRichText

from plone import api
import requests


class News(REST):
    """
        /api/news
    """

    placeholder_type = 'new'
    placeholder_id = 'newid'

    grok.adapts(APIRoot, IPloneSiteRoot)
    grok.require('genweb.authenticated')


class New(REST):
    """
        /api/news/{newid}
    """
    grok.adapts(News, IPloneSiteRoot)
    grok.require('genweb.authenticated')

    def __init__(self, context, request):
        super(New, self).__init__(context, request)

    def POST(self):

        validation = self.validate()
        if validation is not True:
            return validation

        imgName = ''
        imgData = ''
        newid = self.params.pop('newid')
        title = self.params.pop('title')
        desc = self.params.pop('description')
        body = self.params.pop('body')
        img = self.params.pop('imgUrl')
        if img != '':
            imgName = (img.split('/')[-1]).decode('utf-8')
            imgData = requests.get(img).content

        result = self.create_new(newid, title, desc, body, imgData, imgName)

        self.response.setStatus(result.pop('status'))
        return self.json_response(result)

    def create_new(self, newid, title, desc, body, imgData, imgName):
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
                                                   checkConstraints=False)
                new_new.title = title
                new_new.text = IRichText['text'].fromUnicode(body)
                new_new.reindexObject()
            else:
                new_new = createContentInContainer(news_url,
                                                   'News Item',
                                                   title=newid,
                                                   description=desc,
                                                   checkConstraints=False)
                new_new.title = title
                new_new.text = IRichText['text'].fromUnicode(body)
                new_new.reindexObject()
            resp = {'message': 'New {} created'.format(newid), 'status': 201}
        else:
            new = brains[0].getObject()
            new.title = title
            new.description = desc
            if imgName != '':
                new.image = NamedBlobImage(data=imgData,
                                           filename=imgName,
                                           contentType='image/jpeg')
            new.text = IRichText['text'].fromUnicode(body)
            new.reindexObject()
            resp = {'message': 'New {} updated'.format(newid), 'status': 201}

        return resp