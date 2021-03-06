from cStringIO import StringIO
from OFS.Image import Image
from PIL import ImageOps
from five import grok
from Products.CMFCore.utils import getToolByName
from Products.PlonePAS.interfaces.membership import IMembershipTool
from genweb.core.adapters.portrait import IPortraitUploadAdapter
from mrs.max.utilities import IMAXClient
from ulearn.theme.browser.interfaces import IUlearnTheme
from zope.component import getUtility

import logging
import PIL

logger = logging.getLogger(__name__)


@grok.implementer(IPortraitUploadAdapter)
@grok.adapter(IMembershipTool, IUlearnTheme)
class PortraitUploadAdapter(object):
    """ Default adapter for portrait custom actions """
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, portrait, safe_id):
        if portrait and portrait.filename:
            # scaled, mimetype = scale_image(portrait, max_size=(250, 250))
            scaled, mimetype = convertSquareImage(portrait)
            if scaled:
                portrait = Image(id=safe_id, file=scaled, title='')
                membertool = getToolByName(self.context, 'portal_memberdata')
                membertool._setPortrait(portrait, safe_id)

                # Update the user's avatar on MAX
                # the next line to user's that have '-' in id
                safe_id = safe_id.replace('--', '-')
                scaled.seek(0)

                # Upload to MAX server using restricted user credentials
                maxclient, settings = getUtility(IMAXClient)()
                maxclient.setActor(settings.max_restricted_username)
                maxclient.setToken(settings.max_restricted_token)
                try:
                    maxclient.people[safe_id].avatar.post(upload_file=scaled)
                except Exception as exc:
                    logger.error(exc.message)


def convertSquareImage(image_file):
    CONVERT_SIZE = (250, 250)
    try:
        image = PIL.Image.open(image_file)
    except:
        new_file = None
        mimetype = 'image/jpg'
        return new_file, mimetype

    format = image.format
    mimetype = 'image/%s' % format.lower()
    result = ImageOps.fit(image, CONVERT_SIZE, method=PIL.Image.ANTIALIAS, centering=(0.5, 0.5))

    # Bypass CMYK problem in conversion
    if result.mode not in ["1", "L", "P", "RGB", "RGBA"]:
        result = result.convert("RGB")

    new_file = StringIO()
    result.save(new_file, format, quality=88)
    new_file.seek(0)

    return new_file, mimetype
