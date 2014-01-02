# -*- coding: utf-8 -*-
from five import grok
from zope import schema
from plone.directives import form
from ulearn.core import _
from plone.app.textfield import RichText


class IOportunity(form.Schema):
    """ A innovation oportunity
    """

    title = schema.TextLine(
        title=_(u"Nom"),
        description=_(u"Nom de l'oportunitat"),
        required=True
    )

    description = schema.Text(
        title=_(u"Descripció"),
        description=_(u"La descripció de l'oportunitat"),
        required=False
    )

    autor = schema.Text(
        title=_(u"Autor"),
        description=_(u"Autor de l'oportunitat"),
        required=False
    )

    fans = schema.Text(
        title=_(u"Fans"),
        description=_(u"Fans"),
        required=False
    )

    tags = schema.TextLine(
        title=_(u"Tags"),
        description=_(u"Tags de l'oportunitat"),
        required=False
    )

    text = RichText(
        title=_(u"Text"),
        description=_(u"Text de l'oportunitat"),
        required=False
    )
