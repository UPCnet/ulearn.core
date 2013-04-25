from OFS.Image import Image
from AccessControl import Unauthorized
from Products.PlonePAS.utils import scale_image
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.utils import _checkPermission
from Products.CMFCore.permissions import ManageUsers


def changeMemberPortrait(self, portrait, id=None):
    """update the portait of a member.

    We URL-quote the member id if needed.

    Note that this method might be called by an anonymous user who
    is getting registered.  This method will then be called from
    plone.app.users and this is fine.  When called from restricted
    python code or with a curl command by a hacker, the
    declareProtected line will kick in and prevent use of this
    method.
    """
    authenticated_id = self.getAuthenticatedMember().getId()
    if not id:
        id = authenticated_id
    safe_id = self._getSafeMemberId(id)
    if authenticated_id and id != authenticated_id:
        # Only Managers can change portraits of others.
        if not _checkPermission(ManageUsers, self):
            raise Unauthorized
    if portrait and portrait.filename:
        scaled, mimetype = scale_image(portrait, max_size=(176, 176))
        portrait = Image(id=safe_id, file=scaled, title='')
        membertool = getToolByName(self, 'portal_memberdata')
        membertool._setPortrait(portrait, safe_id)
