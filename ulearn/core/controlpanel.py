# -*- coding: utf-8 -*-
from zope import schema
from z3c.form import button

from plone.supermodel import model
from plone.app.registry.browser import controlpanel

from Products.statusmessages.interfaces import IStatusMessage

from ulearn.core import _


class IUlearnControlPanelSettings(model.Schema):
    """ Global Ulearn settings. This describes records stored in the
    configuration registry and obtainable via plone.registry.
    """

    campus_url = schema.TextLine(
        title=_(u"campus_url",
                default=u"URL del campus"),
        description=_(u"help_campus_url",
                default=u"Afegiu la URL del campus associat a aquestes comunitats."),
        required=False,
        default=u"",
    )

    threshold_winwin1 = schema.TextLine(
        title=_(u"llindar_winwin1",
                default=u"Llindar del winwin 1"),
        description=_(u"help_llindar_winwin1",
                default=u"Aquest és el llindar del winwin #1."),
        required=False,
        default=u"50",
    )

    threshold_winwin2 = schema.TextLine(
        title=_(u"llindar_winwin2",
                default=u"Llindar del winwin 2"),
        description=_(u"help_llindar_winwin2",
                default=u"Aquest és el llindar del winwin #2."),
        required=False,
        default=u"100",
    )

    threshold_winwin3 = schema.TextLine(
        title=_(u"llindar_winwin3",
                default=u"Llindar del winwin 3"),
        description=_(u"help_llindar_winwin3",
                default=u"Aquest és el llindar del winwin #3."),
        required=False,
        default=u"500",
    )


class UlearnControlPanelSettingsForm(controlpanel.RegistryEditForm):
    """ Ulearn settings form """

    schema = IUlearnControlPanelSettings
    id = "UlearnControlPanelSettingsForm"
    label = _(u"Ulearn settings")
    description = _(u"help_ulearn_settings_editform",
                    default=u"Configuració de Ulearn")

    def updateFields(self):
        super(UlearnControlPanelSettingsForm, self).updateFields()

    def updateWidgets(self):
        super(UlearnControlPanelSettingsForm, self).updateWidgets()

    @button.buttonAndHandler(_('Save'), name=None)
    def handleSave(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        self.applyChanges(data)
        IStatusMessage(self.request).addStatusMessage(_(u"Changes saved"),
                                                      "info")
        self.context.REQUEST.RESPONSE.redirect("@@ulearn-controlpanel")

    @button.buttonAndHandler(_('Cancel'), name='cancel')
    def handleCancel(self, action):
        IStatusMessage(self.request).addStatusMessage(_(u"Edit cancelled"),
                                                      "info")
        self.request.response.redirect("%s/%s" % (self.context.absolute_url(),
                                                  self.control_panel_view))


class UlearnControlPanel(controlpanel.ControlPanelFormWrapper):
    """ Ulearn settings control panel """
    form = UlearnControlPanelSettingsForm
