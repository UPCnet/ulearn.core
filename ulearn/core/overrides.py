from wildcard.foldercontents.views import NewFolderContentsView
from Acquisition import aq_parent
from ulearn.core.content.community import ICommunity


class UlearnNewFolderContentsView(NewFolderContentsView):

    def isCommunityDocumentsFolder(self):
        parent = aq_parent(self.context)
        if ICommunity.providedBy(parent) \
           and self.context.portal_type == 'Folder'\
           and self.context.id == 'documents':
            return True
        return False
