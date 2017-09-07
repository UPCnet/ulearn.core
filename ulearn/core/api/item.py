# -*- coding: utf-8 -*-
from five import grok
import requests
from Products.CMFPlone.interfaces import IPloneSiteRoot
from ulearn.core.api import ApiResponse
from ulearn.core.api import REST
from ulearn.core.api import api_resource
from ulearn.core.api.root import APIRoot
from plone import api


class Item(REST):
    """
        /api/item

        http://localhost:8090/Plone/api/item/?url=BITLY_URL

    """

    grok.adapts(APIRoot, IPloneSiteRoot)
    grok.require('genweb.authenticated')

    @api_resource(required=['url'])
    def GET(self):
        """ Expanded bitly links """
        url = self.params['url']
        session = requests.Session()
        resp = session.head(url, allow_redirects=True)
        if 'came_from' in resp.url:
            expanded = resp.url.split('came_from=')[1].replace('%3A', ':')
        else:
            expanded = resp.url

        expanded = 'http://localhost:8090/Plone/news/noticia-2/'

        portal = api.portal.get()
        local_url = portal.absolute_url()
        results = []
        if local_url in expanded:
            item = expanded.split(local_url)[1]
            value = api.content.find(path=item)
            new = dict(title=value.title,
                       id=value.id,
                       description=value.description,
                       path=value.getURL(),
                       absolute_url=value.absolute_url_path(),
                       text=value.text.output,
                       filename=value.image.filename,
                       caption=value.image_caption,
                       creators=value.creators,
                       content_type=value.image.contentType,
                       portal_type=value.portal_type,
                       external_url=False

                       )
            results.append(new)
        else:
            value = api.content.find(path=local_url)
            new = dict(title='',
                       id='',
                       description='',
                       path='',
                       absolute_url=expanded,
                       text='',
                       filename='',
                       caption='',
                       creators='',
                       content_type='',
                       portal_type='',
                       external_url=True
                       )
            results.append(new)

        return ApiResponse(results)
