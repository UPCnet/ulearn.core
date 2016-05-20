from five import grok
from plone.indexer import indexer

from zope.component import adapts
from zope.interface import implements, alsoProvides
from zope import schema

from plone.directives import form

from plone.app.contenttypes.interfaces import INewsItem

from ulearn.core import _


class IFlashNews(form.Schema):
    """Add new to show in flash news.
    """

    form.order_after(flash_news='remoteUrl')
    flash_news = schema.Bool(
        title=_(u"flash_info"),
        description=_(u"help_flash_info"),
        required=False,
        default=False
    )

alsoProvides(IFlashNews, form.IFormFieldProvider)


class FlashNews(object):
    implements(IFlashNews)
    adapts(INewsItem)

    def __init__(self, context):
        self.context = context

    def _set_flash_news(self, value):
        self.context.flash_news = value

    def _get_flash_news(self):
        return getattr(self.context, 'flash_news', None)

    flash_news = property(_get_flash_news, _set_flash_news)


@indexer(INewsItem)
def flash_news(obj):
    return obj.flash_news
grok.global_adapter(flash_news, name="flash_news")
