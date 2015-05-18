from five import grok
from hashlib import sha1
from plone.app.layout.viewlets.interfaces import IPortalHeader

from genweb.core.gwuuid import IGWUUID
from ulearn.core.content.community import ICommunity


class CommunityNGDirective(grok.Viewlet):
    grok.context(ICommunity)
    grok.name('ulearn.communityngdirective')
    grok.viewletmanager(IPortalHeader)

    def update(self):
        self.community_hash = sha1(self.context.absolute_url()).hexdigest()
        self.community_gwuuid = IGWUUID(self.context).get()
        self.community_url = self.context.absolute_url()
