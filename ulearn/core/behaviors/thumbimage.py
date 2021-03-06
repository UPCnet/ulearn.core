# -*- coding: utf-8 -*-
from plone.namedfile import field as namedfile
from ulearn.core import _
from plone.autoform.interfaces import IFormFieldProvider
from zope.interface import provider
from plone.directives import form
from zope.interface import alsoProvides
from plone.autoform import directives
from plone.supermodel import model


@provider(IFormFieldProvider)
class IThumbimage(model.Schema):
    """Add Thumbnail image to News Items
    """

    directives.read_permission(thumbnail_image='Zope2.View')
    thumbnail_image = namedfile.NamedBlobImage(
        title=_(u"Thumbnail Image"),
        description=u"Image used in api, for App.",
        required=False,
    )

    # hide the field
    form.omitted('thumbnail_image')


alsoProvides(IThumbimage, form.IFormFieldProvider)
