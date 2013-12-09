# -*- encoding: utf-8 -*-
from mrs.max.userdataschema import IEnhancedUserDataSchema
from mrs.max.userdataschema import EnhancedUserDataPanelAdapter
from mrs.max.userdataschema import UserDataSchemaProvider

from plone.app.users.userdataschema import IUserDataSchemaProvider
from zope import schema
from zope.interface import implements
from ulearn.core import _


class IUlearnUserSchema(IEnhancedUserDataSchema):

    ubicacio = schema.TextLine(
        title=_(u'label_ubicacio', default=u'Ubicació'),
        description=_(u'help_ubicacio',
                      default=u"Equip, Àrea / Companyia / Departament"),
        required=False,
        )

    telefon = schema.TextLine(
        title=_(u'label_telefon', default=u'Telèfon'),
        description=_(u'help_telefon',
                      default=u"Contacte telefònic"),
        required=False,
        )


class UlearnUserSchema(object):
    implements(IUserDataSchemaProvider)

    def getSchema(self):
        """
        """
        return IUlearnUserSchema


class ULearnUserDataPanelAdapter(EnhancedUserDataPanelAdapter):
    def get_ubicacio(self):
        return self.context.getProperty('ubicacio', '')

    def set_ubicacio(self, value):
        return self.context.setMemberProperties({'ubicacio': value})
    ubicacio = property(get_ubicacio, set_ubicacio)

    def get_telefon(self):
        return self.context.getProperty('telefon', '')

    def set_telefon(self, value):
        return self.context.setMemberProperties({'telefon': value})
    telefon = property(get_telefon, set_telefon)
