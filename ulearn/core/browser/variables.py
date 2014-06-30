from five import grok
from zope.component.hooks import getSite
from zope.component import queryUtility
from plone.registry.interfaces import IRegistry

from Products.CMFCore.utils import getToolByName

from mrs.max.browser.controlpanel import IMAXUISettings
from ulearn.core.content.community import ICommunity

TEMPLATE = """\
if (!window._MAXUI) {window._MAXUI = {}; }
window._MAXUI.username = '%(username)s';
window._MAXUI.oauth_token = '%(oauth_token)s';
window._MAXUI.oauth_grant_type = '%(oauth_grant_type)s';
window._MAXUI.max_server = '%(max_server)s';
window._MAXUI.max_server_alias = '%(max_server_alias)s';
window._MAXUI.avatar_url = '%(avatar_url)s';
window._MAXUI.profile_url = '%(profile_url)s'
window._MAXUI.contexts = '%(contexts)s';
window._MAXUI.activitySource = '%(activitySource)s';
window._MAXUI.language = '%(language)s';
window._MAXUI.hidePostboxOnTimeline = false;
window._MAXUI.domain = '%(max_domain)s';
"""


class communityVariables(grok.View):
    grok.name('communityVariables.js')
    grok.context(ICommunity)

    def render(self):
        self.request.response.addHeader('content-type', 'text/javascript;;charset=utf-8')
        self.request.response.addHeader('cache-control', 'must-revalidate, max-age=0, no-cache, no-store')
        portal_url = getSite().absolute_url()

        registry = queryUtility(IRegistry)
        settings = registry.forInterface(IMAXUISettings, check=False)

        pm = getToolByName(self.context, "portal_membership")
        if pm.isAnonymousUser():  # the user has not logged in
            username = ''
            oauth_token = ''
        else:
            member = pm.getAuthenticatedMember()
            username = member.getUserName()
            member = pm.getMemberById(username)
            oauth_token = member.getProperty('oauth_token', None)

        pl = getToolByName(self.context, "portal_languages")
        default_lang = pl.getDefaultLanguage()

        return TEMPLATE % dict(
            username=username,
            oauth_token=oauth_token,
            oauth_grant_type=settings.oauth_grant_type,
            max_server=settings.max_server,
            max_server_alias=settings.max_server_alias,
            avatar_url='%s/avatar/{0}' % (portal_url),
            profile_url='%s/author/{0}' % (portal_url),
            contexts=self.context.absolute_url(),
            activitySource='activities',
            language=default_lang,
            max_domain=settings.max_domain
        )
