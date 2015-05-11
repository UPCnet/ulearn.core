from zope.interface import Interface
from zope.filerepresentation.interfaces import IFileFactory


class IDocumentFolder(Interface):
    """ Marker for documents folder """


class ILinksFolder(Interface):
    """ Marker for links folder """


class IPhotosFolder(Interface):
    """ Marker for photos folder """


class IEventsFolder(Interface):
    """ Marker for events folder """


class IDiscussionFolder(Interface):
    """ Marker for discussion folder """


class IDXFileFactory(IFileFactory):
    """ adapter factory for DX types
    """


class IAppImage(Interface):
    """ Marker to identify content type Image uploaded via an app """


class IAppFile(Interface):
    """ Marker to identify content type File uploaded via an app """


class IVideo(Interface):
    """ Marker to identify content type Video """


class IUlearnUtils(Interface):
    """ Marker describing the functionality of the convenience methods
        placeholder ulearn.utils view.
    """
    def portal(self):
        """ Returns the portal object """

    def get_url_forget_password(self):
        """ return redirect url when forget user password """
