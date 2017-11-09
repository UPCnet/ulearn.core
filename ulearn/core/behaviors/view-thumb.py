# -*- coding: utf-8 -*-
from Products.Five.browser import BrowserView


class Thumbnail(BrowserView):

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        context = self.context

        if getattr(context, 'thumbnail_image', None):
            img_data = context.thumbnail_image.open().read()
            contentType = context.thumbnail_image.contentType
            filename = context.thumbnail_image.filename

            self.request.response.setHeader('content-type', contentType)
            self.request.response.setHeader(
                'content-disposition', 'inline; filename=' + str(filename))
            self.request.response.setHeader('content-length', len(img_data))
        else:
            img_data = None

        return img_data
