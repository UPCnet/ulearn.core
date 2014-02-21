# -*- coding: utf-8 -*-
from five import grok
from zope import schema
from zope.component import getUtility
from z3c.form import button
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.interfaces import IVocabularyFactory

from plone.supermodel import model
from plone.directives import dexterity, form
from plone.app.registry.browser import controlpanel

from Products.statusmessages.interfaces import IStatusMessage

from genweb.core.widgets.select2_user_widget import Select2UserInputFieldWidget

from ulearn.core import _
from mrs.max.utilities import IMAXClient


class availableLanguages(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        terms = []
        terms.append(SimpleVocabulary.createTerm(u'Català', 'ca', _(u'Català')))
        terms.append(SimpleVocabulary.createTerm(u'Castellà', 'es', _(u'Castellà')))
        terms.append(SimpleVocabulary.createTerm(u'English', 'en', _(u'English')))

        return SimpleVocabulary(terms)

grok.global_utility(availableLanguages, name=u"ulearn.core.language")


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
                          'background_color',
                          'buttons_color_primary', 'buttons_color_secondary',
                          'maxui_form_bg',
                          'alt_gradient_start_color', 'alt_gradient_end_color'])

    model.fieldset('VIPs',
                  _(u'VIPs'),
                  fields=['vip_users'])

    model.fieldset('UPCnet only',
                  _(u'UPCnet only'),
                  fields=['language'])

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
                default=u"Propietat de fons global"),
        description=_(u"help_background_property",
                default=u"Aquest és la propietat de CSS de background."),
        required=True,
        default=u"transparent",
    )

    background_color = schema.TextLine(
        title=_(u"background_color",
                default=u"Color de fons global"),
        description=_(u"help_background_color",
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

    dexterity.write_permission(language='zope2.ViewManagementScreens')
    language = schema.Choice(
        title=_(u"language",
                default=u"Idioma de l'espai"),
        description=_(u"help_language",
                default=u"Aquest és l'idioma de l'espai, que es configura quan el paquet es reinstala."),
        required=True,
        values=['ca', 'es', 'en'],
        default='es',
    )

    form.widget(vip_users=Select2UserInputFieldWidget)
    vip_users = schema.List(
        title=_(u"vip_users"),
        description=_(u"Llista amb les persones VIPs que no han de sortir a les cerques i estan restringides a les demés."),
        value_type=schema.TextLine(),
        required=False,
        default=[])


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

        if data.get('vip_users', False):
            maxclient, settings = getUtility(IMAXClient)()
            maxclient.setActor(settings.max_restricted_username)
            maxclient.setToken(settings.max_restricted_token)

            current_vips = maxclient.getSecurity()
            current_vips = current_vips[0].get('roles').get('VIP', ['', ])

            un_vip = [a for a in current_vips if a not in data.get('vip_users')]
            for user in un_vip:
                maxclient.revoke_security_role(user, 'VIP')

            make_vip = [vip for vip in data.get('vip_users') if vip not in current_vips]

            for user in make_vip:
                maxclient.grant_security_role(user, 'VIP')

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
