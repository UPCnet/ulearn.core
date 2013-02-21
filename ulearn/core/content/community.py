from five import grok
from zope import schema

from plone.directives import form, dexterity
from plone.app.textfield import RichText

from ulearn.core import _


class ICommunity(form.Schema):
    """ A manageable community
    """

    name = schema.TextLine(
            title=_(u"Nom"),
            description=_(u"Nom de la comunitat"),
        )

    # subscribed = schema.List(
    #         title=_(u"Subscrits"),
    #         description=_(u"Llista amb les persones subscrites"),
    #     )
