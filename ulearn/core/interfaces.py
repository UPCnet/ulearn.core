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


class IDXFileFactory(IFileFactory):
    """ adapter factory for DX types
    """
