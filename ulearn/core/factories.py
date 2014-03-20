import transaction
from thread import allocate_lock

from zope.component import getMultiAdapter
from zope.component import adapts
from zope.container.interfaces import INameChooser
from zope.lifecycleevent import ObjectModifiedEvent
from zope.event import notify
from zope.interface import implements

from Products.Archetypes.event import ObjectInitializedEvent
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.interfaces._content import IFolderish

try:
    from plone.namedfile.file import NamedBlobImage
    from plone.namedfile.file import NamedBlobFile
except ImportError:
    # only for dext
    pass

from ulearn.core.interfaces import IDXFileFactory

upload_lock = allocate_lock()


class DXFileFactory(object):
    """ Ripped out from above """
    implements(IDXFileFactory)
    adapts(IFolderish)

    def __init__(self, context):
        self.context = context

    def __call__(self, name, content_type, data, title, request):
        # contextual import to prevent ImportError
        from plone.dexterity.utils import createContentInContainer

        ctr = getToolByName(self.context, 'content_type_registry')
        type_ = ctr.findTypeName(name.lower(), '', '') or 'File'

        name = name.decode("utf8")
        title = title.decode("utf8")

        chooser = INameChooser(self.context)

        # otherwise I get ZPublisher.Conflict ConflictErrors
        # when uploading multiple files
        upload_lock.acquire()

        def trim_title(title):
            pview = getMultiAdapter((self.context, request), name='plone')
            return pview.cropText(title, 40)

        newid = chooser.chooseName(title, self.context.aq_parent)
        try:
            transaction.begin()

            # Try to determine which kind of NamedBlob we need
            # This will suffice for standard p.a.contenttypes File/Image
            # and any other custom type that would have 'File' or 'Image' in
            # its type name
            if 'File' in type_:
                file = NamedBlobFile(data=data.read(),
                                     filename=unicode(data.filename),
                                     contentType=content_type)
                obj = createContentInContainer(self.context,
                                               type_,
                                               id=newid,
                                               title=trim_title(title),
                                               description=title,
                                               file=file)
            elif 'Image' in type_:
                image = NamedBlobImage(data=data.read(),
                                       filename=unicode(data.filename),
                                       contentType=content_type)
                obj = createContentInContainer(self.context,
                                               type_,
                                               id=newid,
                                               title=trim_title(title),
                                               description=title,
                                               image=image)

            # obj.title = name
            obj.reindexObject()
            transaction.commit()

        finally:
            upload_lock.release()

        return obj
