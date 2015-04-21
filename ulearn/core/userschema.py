# -*- encoding: utf-8 -*-
from zope import schema
from zope.interface import Interface
from zope.interface import implements

# from mrs.max.userdataschema import IEnhancedUserDataSchema
from mrs.max.userdataschema import EnhancedUserDataPanelAdapter
# from mrs.max.userdataschema import UserDataSchemaProvider

from plone.app.users.browser.formlib import FileUpload
from plone.app.users.userdataschema import IUserDataSchemaProvider
from plone.app.users.userdataschema import checkEmailAddress

from ulearn.core import _


class IUlearnUserSchema(Interface):
    """ Redefinition of all the fields because of the ordering """

    fullname = schema.TextLine(
        title=_(u'label_full_name', default=u'Full Name'),
        description=_(u'help_full_name_creation',
                      default=u'Enter full name, e.g. John Smith.'),
        required=True)

    email = schema.ASCIILine(
        title=_(u'label_email', default=u'E-mail'),
        description=u'',
        required=True,
        constraint=checkEmailAddress)

    home_page = schema.TextLine(
        title=_(u'label_homepage', default=u'Home page'),
        description=_(u'help_homepage',
                      default=u'The URL for your external home page, '
                      'if you have one.'),
        required=False)

    description = schema.Text(
        title=_(u'label_biography', default=u'Biography'),
        description=_(u'help_biography',
                      default=u'A short overview of who you are and what you '
                      'do. Will be displayed on your author page, linked '
                      'from the items you create.'),
        required=False)

    location = schema.TextLine(
        title=_(u'label_location', default=u'Location'),
        description=_(u'help_location',
                      default=u'Your location - either city and '
                      'country - or in a company setting, where '
                      'your office is located.'),
        required=False)

    portrait = FileUpload(title=_(u'label_portrait', default=u'Portrait'),
        description=_(u'help_portrait',
                      default=u'To add or change the portrait: click the '
                      '"Browse" button; select a picture of yourself. '
                      'Recommended image size is 75 pixels wide by 100 '
                      'pixels tall.'),
        required=False)

    pdelete = schema.Bool(
        title=_(u'label_delete_portrait', default=u'Delete Portrait'),
        description=u'',
        required=False)

    twitter_username = schema.TextLine(
        title=_(u'label_twitter', default=u'Twitter username'),
        description=_(u'help_twitter',
                      default=u'Fill in your Twitter username.'),
        required=False,
    )

    ubicacio = schema.TextLine(
        title=_(u'label_ubicacio', default=u'Ubicació'),
        description=_(u'help_ubicacio',
                      default=u'Equip, Àrea / Companyia / Departament'),
        required=False,
    )

    telefon = schema.TextLine(
        title=_(u'label_telefon', default=u'Telèfon'),
        description=_(u'help_telefon',
                      default=u'Contacte telefònic'),
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
        return self._getProperty('ubicacio')

    def set_ubicacio(self, value):
        return self.context.setMemberProperties({'ubicacio': value})
    ubicacio = property(get_ubicacio, set_ubicacio)

    def get_telefon(self):
        return self._getProperty('telefon')

    def set_telefon(self, value):
        return self.context.setMemberProperties({'telefon': value})
    telefon = property(get_telefon, set_telefon)
