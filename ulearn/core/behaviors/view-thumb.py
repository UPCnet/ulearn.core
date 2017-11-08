# -*- coding: utf-8 -*-
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.Five.browser import BrowserView
from base64 import b64encode


class Thumbnail(BrowserView):
    __call__ = ViewPageTemplateFile('view-thumb.pt')

    def getImage(self):
        context = self.context

        if getattr(context, 'thumbnail_image', None):
            thumb = b64encode(context.thumbnail_image.data)
        else:
            thumb = None

        return thumb
