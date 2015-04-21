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

from genweb.core.widgets.select2_maxuser_widget import Select2MAXUserInputFieldWidget

from ulearn.core import _
from mrs.max.utilities import IMAXClient
from plone.namedfile.field import NamedImage
from zope.interface import Interface
from collective.z3cform.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield.registry import DictRow


class availableLanguages(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        terms = []
        terms.append(SimpleVocabulary.createTerm(u'Català', 'ca', _(u'Català')))
        terms.append(SimpleVocabulary.createTerm(u'Castellà', 'es', _(u'Castellà')))
        terms.append(SimpleVocabulary.createTerm(u'English', 'en', _(u'English')))

        return SimpleVocabulary(terms)

grok.global_utility(availableLanguages, name=u'ulearn.core.language')


class communityActivityView(object):
    grok.implements(IVocabularyFactory)

    def __call__(self, context):
        terms = []
        terms.append(SimpleVocabulary.createTerm(u'Darreres activitats', 'darreres_activitats', _(u'Darreres activitats')))
        terms.append(SimpleVocabulary.createTerm(u'Activitats mes valorades', 'activitats_mes_valorades', _(u'Activitats mes valorades')))
        terms.append(SimpleVocabulary.createTerm(u'Activitats destacades', 'activitats_destacades', _(u'Activitats destacades')))

        return SimpleVocabulary(terms)

grok.global_utility(communityActivityView, name=u'ulearn.core.activity_view')


class ILiteralQuickLinks(form.Schema):
    language = schema.Choice(
        title=_(u'Language'),
        required=True,
        vocabulary=u'plone.app.vocabularies.SupportedContentLanguages'
    )
    text = schema.TextLine(title=_(u'Text'), required=True)


class ITableQuickLinks(form.Schema):
    language = schema.Choice(
        title=_(u'Language'),
        required=True,
        vocabulary=u'plone.app.vocabularies.SupportedContentLanguages'
    )
    text = schema.TextLine(title=_(u'Text'), required=True)
    link = schema.TextLine(title=_(u'Link'), required=True)
    icon = schema.TextLine(title=_(u'Font Awesome Icon'), required=False)
    new_window = schema.Bool(title=_(u'New window'), required=True, default=True)


class IUlearnControlPanelSettings(model.Schema):
    """ Global Ulearn settings. This describes records stored in the
    configuration registry and obtainable via plone.registry.
    """

    model.fieldset('General',
                  _(u'General'),
                  fields=['campus_url', 'library_url', 'people_literal', 'threshold_winwin1', 'threshold_winwin2',
                          'threshold_winwin3'])

    model.fieldset('Specific',
                  _(u'Specific'),
                  fields=['main_color', 'secondary_color', 'background_property',
                          'background_color',
                          'buttons_color_primary', 'buttons_color_secondary',
                          'maxui_form_bg',
                          'alt_gradient_start_color', 'alt_gradient_end_color',
                          'color_community_closed', 'color_community_organizative', 'color_community_open'])

    model.fieldset('Visibility',
                  _(u'Visibility'),
                  fields=['nonvisibles'])

    model.fieldset('UPCnet only',
                  _(u'UPCnet only'),
                  fields=['language', 'activity_view','url_forget_password'])

    model.fieldset('Quick Links',
                  _(u'QuickLinks'),
                  fields=['quicklinks_literal', 'quicklinks_icon', 'quicklinks_table'])

    campus_url = schema.TextLine(
        title=_(u'campus_url',
                default=u'URL del campus'),
        description=_(u'help_campus_url',
                default=u'Afegiu la URL del campus associat a aquestes comunitats.'),
        required=False,
        default=u'',
    )

    library_url = schema.TextLine(
        title=_(u'library_url',
                default=u'URL de la biblioteca'),
        description=_(u'help_library_url',
                default=u'Afegiu la URL de la biblioteca associada a aquestes comunitats.'),
        required=False,
        default=u'',
    )

    threshold_winwin1 = schema.TextLine(
        title=_(u'llindar_winwin1',
                default=u'Llindar del winwin 1'),
        description=_(u'help_llindar_winwin1',
                default=u'Aquest és el llindar del winwin #1.'),
        required=False,
        default=u'50',
    )

    threshold_winwin2 = schema.TextLine(
        title=_(u'llindar_winwin2',
                default=u'Llindar del winwin 2'),
        description=_(u'help_llindar_winwin2',
                default=u'Aquest és el llindar del winwin #2.'),
        required=False,
        default=u'100',
    )

    threshold_winwin3 = schema.TextLine(
        title=_(u'llindar_winwin3',
                default=u'Llindar del winwin 3'),
        description=_(u'help_llindar_winwin3',
                default=u'Aquest és el llindar del winwin #3.'),
        required=False,
        default=u'500',
    )

    main_color = schema.TextLine(
        title=_(u'main_color',
                default=u'Color principal'),
        description=_(u'help_main_color',
                default=u'Aquest és el color principal de l\'espai.'),
        required=True,
        default=u'#f58d3d',
    )

    secondary_color = schema.TextLine(
        title=_(u'secondary_color',
                default=u'Color secundari'),
        description=_(u'help_secondary_color',
                default=u'Aquest és el color secundari de l\'espai.'),
        required=True,
        default=u'#f58d3d',
    )

    maxui_form_bg = schema.TextLine(
        title=_(u'maxui_form_bg',
                default=u'Color del fons del widget de MAX.'),
        description=_(u'help_maxui_form_bg',
                default=u'Aquest és el color del fons del widget de MAX.'),
        required=True,
        default=u'#34495c',
    )

    alt_gradient_start_color = schema.TextLine(
        title=_(u'alt_gradient_start_color',
                default=u'Color inicial dels gradients.'),
        description=_(u'help_alt_gradient_start_color',
                default=u'Aquest és el color inicial dels gradients.'),
        required=True,
        default=u'#f58d3d',
    )

    alt_gradient_end_color = schema.TextLine(
        title=_(u'alt_gradient_end_color',
                default=u'Color final dels gradients'),
        description=_(u'help_alt_gradient_end_color',
                default=u'Aquest és el color final dels gradients.'),
        required=True,
        default=u'#f58d3d',
    )

    background_property = schema.TextLine(
        title=_(u'background_property',
                default=u'Propietat de fons global'),
        description=_(u'help_background_property',
                default=u'Aquest és la propietat de CSS de background.'),
        required=True,
        default=u'transparent',
    )

    background_color = schema.TextLine(
        title=_(u'background_color',
                default=u'Color de fons global'),
        description=_(u'help_background_color',
                default=u'Aquest és el color de fons global o la propietat corresponent.'),
        required=True,
        default=u'#eae9e4',
    )

    buttons_color_primary = schema.TextLine(
        title=_(u'buttons_color_primary',
                default=u'Color primari dels botons'),
        description=_(u'help_buttons_color_primary',
                default=u'Aquest és el color primari dels botons.'),
        required=True,
        default=u'#34495E',
    )

    buttons_color_secondary = schema.TextLine(
        title=_(u'buttons_color_secondary',
                default=u'Color secundari dels botons'),
        description=_(u'help_buttons_color_secondary',
                default=u'Aquest és el color secundari dels botons.'),
        required=True,
        default=u'#34495E',
    )

    color_community_closed = schema.TextLine(
        title=_(u"color_community_closed",
                default=u"Color comunitat tancada"),
        description=_(u"help_color_community_closed",
                default=u"Aquest és el color per les comunitats tancades."),
        required=True,
        default=u"#f58d3d",
    )

    color_community_organizative = schema.TextLine(
        title=_(u"color_community_organizative",
                default=u"Color comunitat organitzativa"),
        description=_(u"help_color_community_organizative",
                default=u"Aquest és el color per les comunitats organitzatives."),
        required=True,
        default=u"#b5c035",
    )

    color_community_open = schema.TextLine(
        title=_(u"color_community_open",
                default=u"Color comunitat oberta"),
        description=_(u"help_color_community_open",
                default=u"Aquest és el color per les comunitats obertes."),
        required=True,
        default=u"#888888",
    )

    dexterity.write_permission(language='zope2.ViewManagementScreens')
    language = schema.Choice(
        title=_(u'language',
                default=u'Idioma de l\'espai'),
        description=_(u'help_language',
                default=u'Aquest és l\'idioma de l\'espai, que es configura quan el paquet es reinstala.'),
        required=True,
        values=['ca', 'es', 'en'],
        default='es',
    )

    form.widget(nonvisibles=Select2MAXUserInputFieldWidget)
    nonvisibles = schema.List(
        title=_(u'no_visibles'),
        description=_(u'Llista amb les persones que no han de sortir a les cerques i que tenen accés restringit per les demés persones.'),
        value_type=schema.TextLine(),
        required=False,
        default=[])

    people_literal = schema.Choice(
        title=_(u'people_literal'),
        description=_(u'Literals que identifiquen als usuaris de les comunitats i les seves aportacions.'),
        values=['thinnkers', 'persones', 'participants'],
        required=False,
        default='persones')

    form.widget(quicklinks_literal=DataGridFieldFactory)
    quicklinks_literal = schema.List(title=_(u'Text Quick Links'),
                                     description=_(u'help_quicklinks_literal',
                                     default=u'Add the text quick links by language'),
                                     value_type=DictRow(title=_(u'help_quicklinks_literal'),
                                                        schema=ILiteralQuickLinks))

    quicklinks_icon = schema.TextLine(
        title=_(u'quicklinks_icon',
                default=u'icon-link'),
        description=_(u'help_quicklinks_icon',
                default=u'Afegiu la icona del Font Awesome que voleu que es mostri'),
        required=False,
        default=u'',
    )

    form.widget(quicklinks_table=DataGridFieldFactory)
    quicklinks_table = schema.List(title=_(u'QuickLinks'),
                                   description=_(u'help_quicklinks_table',
                                   default=u'Add the quick links by language'),
                                   value_type=DictRow(title=_(u'help_quicklinks_table'),
                                                      schema=ITableQuickLinks))

    activity_view = schema.Choice(
        title=_(u'activity_view'),
        description=_(u'help_activity_view'),
        vocabulary=u'ulearn.core.activity_view',
        required=True,
        default=u'Darreres activitats')

    url_forget_password = schema.TextLine(
        title=_(u"url_forget_password",
                default=u"URL contrasenya oblidada"),
        description=_(u"help_url_forget_password",
                    default=u"Url per defecte: '/mail_password_form?userid='. Per a dominis externs indiqueu la url completa, 'http://www.domini.cat'"),
        required=True,
        default=u"/mail_password_form?userid=")


class UlearnControlPanelSettingsForm(controlpanel.RegistryEditForm):
    """ Ulearn settings form """

    schema = IUlearnControlPanelSettings
    id = 'UlearnControlPanelSettingsForm'
    label = _(u'Ulearn settings')
    description = _(u'help_ulearn_settings_editform',
                    default=u'uLearn configuration registry.')

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

        if data.get('nonvisibles', False):
            maxclient, settings = getUtility(IMAXClient)()
            maxclient.setActor(settings.max_restricted_username)
            maxclient.setToken(settings.max_restricted_token)

            current_vips = maxclient.admin.security.get()
            current_vips = current_vips[0].get('roles').get('NonVisible', [])

            un_vip = [a for a in current_vips if a not in data.get('nonvisibles')]
            for user in un_vip:
                maxclient.admin.security.roles['NonVisible'].users[user].delete()

            make_vip = [vip for vip in data.get('nonvisibles') if vip not in current_vips]

            for user in make_vip:
                maxclient.admin.security.roles['NonVisible'].users[user].post()

        IStatusMessage(self.request).addStatusMessage(_(u'Changes saved'),
                                                      'info')
        self.context.REQUEST.RESPONSE.redirect('@@ulearn-controlpanel')

    @button.buttonAndHandler(_('Cancel'), name='cancel')
    def handleCancel(self, action):
        IStatusMessage(self.request).addStatusMessage(_(u'Edit cancelled'),
                                                      'info')
        self.request.response.redirect('%s/%s' % (self.context.absolute_url(),
                                                  self.control_panel_view))


class UlearnControlPanel(controlpanel.ControlPanelFormWrapper):
    """ Ulearn settings control panel """
    form = UlearnControlPanelSettingsForm
