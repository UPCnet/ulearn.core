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

    model.fieldset('General',
                  _(u'General'),
                  fields=['campus_url', 'threshold_winwin1', 'threshold_winwin2',
                          'threshold_winwin3'])

    model.fieldset('Specific',
                  _(u'Specific'),
                  fields=['main_color', 'secondary_color', 'background_property',
                          'buttons_color_primary', 'buttons_color_secondary',
                          'maxui_form_bg',
                          'alt_gradient_start_color', 'alt_gradient_end_color'])

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

    main_color = schema.TextLine(
        title=_(u"main_color",
                default=u"Color principal"),
        description=_(u"help_main_color",
                default=u"Aquest és el color principal de l'espai."),
        required=True,
        default=u"#f58d3d",
    )

    secondary_color = schema.TextLine(
        title=_(u"secondary_color",
                default=u"Color secundari"),
        description=_(u"help_secondary_color",
                default=u"Aquest és el color secundari de l'espai."),
        required=True,
        default=u"#f58d3d",
    )

    maxui_form_bg = schema.TextLine(
        title=_(u"maxui_form_bg",
                default=u"Color del fons del widget de MAX."),
        description=_(u"help_maxui_form_bg",
                default=u"Aquest és el color del fons del widget de MAX."),
        required=True,
        default=u"#34495c",
    )

    alt_gradient_start_color = schema.TextLine(
        title=_(u"alt_gradient_start_color",
                default=u"Color inicial dels gradients."),
        description=_(u"help_alt_gradient_start_color",
                default=u"Aquest és el color inicial dels gradients."),
        required=True,
        default=u"#f58d3d",
    )

    alt_gradient_end_color = schema.TextLine(
        title=_(u"alt_gradient_end_color",
                default=u"Color final dels gradients"),
        description=_(u"help_alt_gradient_end_color",
                default=u"Aquest és el color final dels gradients."),
        required=True,
        default=u"#f58d3d",
    )

    background_property = schema.TextLine(
        title=_(u"background_property",
                default=u"Color de fons global"),
        description=_(u"help_background_property",
                default=u"Aquest és el color de fons global o la propietat corresponent."),
        required=True,
        default=u"#eae9e4",
    )

    buttons_color_primary = schema.TextLine(
        title=_(u"buttons_color_primary",
                default=u"Color primari dels botons"),
        description=_(u"help_buttons_color_primary",
                default=u"Aquest és el color primari dels botons."),
        required=True,
        default=u"#34495E",
    )

    buttons_color_secondary = schema.TextLine(
        title=_(u"buttons_color_secondary",
                default=u"Color secundari dels botons"),
        description=_(u"help_buttons_color_secondary",
                default=u"Aquest és el color secundari dels botons."),
        required=True,
        default=u"#34495E",
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
