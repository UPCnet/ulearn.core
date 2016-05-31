# -*- coding: utf-8 -*-
from five import grok
from zope import schema
from zope.component import getUtility, getMultiAdapter
from zope.component.hooks import getSite
from z3c.form import button
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.interfaces import IVocabularyFactory

from plone.portlets.utils import registerPortletType, unregisterPortletType
from plone.supermodel import model
from plone.directives import dexterity, form
from plone.app.registry.browser import controlpanel

from Products.statusmessages.interfaces import IStatusMessage

from genweb.core.widgets.select2_maxuser_widget import Select2MAXUserInputFieldWidget

from ulearn.core import _
from mrs.max.utilities import IMAXClient
from collective.z3cform.datagridfield import DataGridFieldFactory
from collective.z3cform.datagridfield.registry import DictRow

from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import IPortletAssignment
from plone.portlets.interfaces import IPortletAssignmentMapping


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
                           'threshold_winwin3', 'stats_button'])

    model.fieldset('Specific',
                   _(u'Specific'),
                   fields=['main_color', 'secondary_color', 'background_property',
                           'background_color',
                           'buttons_color_primary', 'buttons_color_secondary',
                           'maxui_form_bg',
                           'alt_gradient_start_color', 'alt_gradient_end_color',
                           'color_community_closed', 'color_community_organizative', 'color_community_open'])

    model.fieldset('Portlets',
                   _(u'Portlets'),
                   fields=['genweb_portlets_homepage', 'genweb_portlets_esdeveniments', 'genweb_portlets_news',
                           'genweb_portlets_fullnews', 'genweb_portlets_upcnews', 'genweb_portlets_news_events_listing',
                           'ulearn_portlets_angularrouteview', 'ulearn_portlets_buttonbar', 'ulearn_portlets_communities',
                           'ulearn_portlets_profile', 'ulearn_portlets_thinnkers', 'ulearn_portlets_calendar',
                           'ulearn_portlets_discussion', 'ulearn_portlets_econnect', 'ulearn_portlets_mostvalued',
                           'ulearn_portlets_stats', 'ulearn_portlets_importantnews', 'ulearn_portlets_flashesinformativos',
                           'ulearn_portlets_mycommunities', 'ulearn_portlets_custombuttonbar', 'ulearn_portlets_mysubjects',
                           'ulearn_portlets_subscribednews', 'ulearn_portlets_mytags', 'portlets_Calendar',
                           'plone_portlet_collection_Collection', 'portlets_Events', 'portlets_Login',
                           'portlets_Navigation', 'portlets_rss', 'plone_portlet_static_Static', 'collective_polls_VotePortlet',
                           'portlets_Search', 'portlets_Review', 'portlets_Recent', 'portlets_News', 'mrs_max_widget'])

    model.fieldset('Visibility',
                   _(u'Visibility'),
                   fields=['nonvisibles'])

    model.fieldset('UPCnet only',
                   _(u'UPCnet only'),
                   fields=['language', 'activity_view', 'url_forget_password'])

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

    stats_button = schema.Bool(
        title=_(u'stats_button',
                default=u"Mostrar botó d'accés a estadístiques diàries"),
        description=_(u'help_stats_button',
                      default=u"Mostra o no el botó d'accés a estadístiques diàries a stats/activity i stats/chats"),
        required=False,
        default=False,
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
        title=_(u'color_community_closed',
                default=u'Color comunitat tancada'),
        description=_(u'help_color_community_closed',
                      default=u'Aquest és el color per les comunitats tancades.'),
        required=True,
        default=u'#f58d3d',
    )

    color_community_organizative = schema.TextLine(
        title=_(u'color_community_organizative',
                default=u'Color comunitat organitzativa'),
        description=_(u'help_color_community_organizative',
                      default=u'Aquest és el color per les comunitats organitzatives.'),
        required=True,
        default=u'#b5c035',
    )

    color_community_open = schema.TextLine(
        title=_(u'color_community_open',
                default=u'Color comunitat oberta'),
        description=_(u'help_color_community_open',
                      default=u'Aquest és el color per les comunitats obertes.'),
        required=True,
        default=u'#888888',
    )

    # ==== Portlets ====

    genweb_portlets_news_events_listing = schema.Bool(
        title=_(u'genweb_portlets_news_events_listing',
                default=u"Habilitar portlet genweb_portlets_news_events_listing"),
        description=_(u'help_genweb_portlets_news_events_listing',
                      default=u"Habilita el portlet genweb_portlets_news_events_listing."),
        required=False,
        default=False,
    )

    portlets_Search = schema.Bool(
        title=_(u'portlets_Search',
                default=u"Habilitar portlet portlets_Search"),
        description=_(u'help_portlets_Search',
                      default=u"Habilita el portlet portlets_Search."),
        required=False,
        default=False,
    )

    portlets_Review = schema.Bool(
        title=_(u'portlets_Review',
                default=u"Habilitar portlet portlets_Review"),
        description=_(u'help_portlets_Review',
                      default=u"Habilita el portlet portlets_Review."),
        required=False,
        default=False,
    )

    portlets_Recent = schema.Bool(
        title=_(u'portlets_Recent',
                default=u"Habilitar portlet portlets_Recent"),
        description=_(u'help_portlets_Recent',
                      default=u"Habilita el portlet portlets_Recent."),
        required=False,
        default=False,
    )

    portlets_News = schema.Bool(
        title=_(u'portlets_News',
                default=u"Habilitar portlet portlets_News"),
        description=_(u'help_portlets_News',
                      default=u"Habilita el portlet portlets_News."),
        required=False,
        default=False,
    )

    mrs_max_widget = schema.Bool(
        title=_(u'mrs_max_widget',
                default=u"Habilitar portlet mrs_max_widget"),
        description=_(u'help_mrs_max_widget',
                      default=u"Habilita el portlet mrs_max_widget."),
        required=False,
        default=False,
    )

    portlets_Events = schema.Bool(
        title=_(u'portlets_Events',
                default=u"Habilitar portlet portlets_Events"),
        description=_(u'help_portlets_Events',
                      default=u"Habilita el portlet portlets_Events."),
        required=False,
        default=False,
    )

    portlets_Calendar = schema.Bool(
        title=_(u'portlets_Calendar',
                default=u"Habilitar portlet portlets_Calendar"),
        description=_(u'help_portlets_Calendar',
                      default=u"Habilita el portlet portlets_Calendar."),
        required=False,
        default=False,
    )

    plone_portlet_collection_Collection = schema.Bool(
        title=_(u'plone_portlet_collection_Collection',
                default=u"Habilitar portlet plone_portlet_collection_Collection"),
        description=_(u'help_plone_portlet_collection_Collection',
                      default=u"Habilita el portlet plone_portlet_collection_Collection."),
        required=False,
        default=False,
    )

    portlets_Login = schema.Bool(
        title=_(u'portlets_Login',
                default=u"Habilitar portlet portlets_Login"),
        description=_(u'help_portlets_Login',
                      default=u"Habilita el portlet portlets_Login."),
        required=False,
        default=False,
    )

    portlets_Navigation = schema.Bool(
        title=_(u'portlets_Navigation',
                default=u"Habilitar portlet portlets_Navigation"),
        description=_(u'help_portlets_Navigation',
                      default=u"Habilita el portlet portlets_Navigation."),
        required=False,
        default=False,
    )

    portlets_rss = schema.Bool(
        title=_(u'portlets_rss',
                default=u"Habilitar portlet portlets_rss"),
        description=_(u'help_portlets_rss',
                      default=u"Habilita el portlet portlets_rss."),
        required=False,
        default=False,
    )

    plone_portlet_static_Static = schema.Bool(
        title=_(u'plone_portlet_static_Static',
                default=u"Habilitar portlet plone_portlet_static_Static"),
        description=_(u'help_plone_portlet_static_Static',
                      default=u"Habilita el portlet plone_portlet_static_Static."),
        required=False,
        default=False,
    )

    collective_polls_VotePortlet = schema.Bool(
        title=_(u'collective_polls_VotePortlet',
                default=u"Habilitar portlet collective_polls_VotePortlet"),
        description=_(u'help_collective_polls_VotePortlet',
                      default=u"Habilita el portlet collective_polls_VotePortlet."),
        required=False,
        default=False,
    )

    genweb_portlets_homepage = schema.Bool(
        title=_(u'portlet_homepage_title',
                default=u"Habilitar portlet homepage"),
        description=_(u'help_genweb_portlets_homepage',
                      default=u"Habilita el portlet homepage."),
        required=False,
        default=False,
    )

    genweb_portlets_esdeveniments = schema.Bool(
        title=_(u'AgendaGW',
                default=u"Habilitar portlet esdeveniments"),
        description=_(u'help_genweb_portlets_esdeveniments',
                      default=u"Habilita el portlet esdeveniments."),
        required=False,
        default=False,
    )

    genweb_portlets_news = schema.Bool(
        title=_(u'NoticiesPropi',
                default=u"Habilitar portlet News"),
        description=_(u'help_genweb_portlets_news',
                      default=u"Habilita el portlet News."),
        required=False,
        default=False,
    )

    genweb_portlets_fullnews = schema.Bool(
        title=_(u'FullNews',
                default=u"Habilitar portlet Full News"),
        description=_(u'help_genweb_portlets_fullnews',
                      default=u"Habilita el portlet Full News."),
        required=False,
        default=False,
    )

    genweb_portlets_upcnews = schema.Bool(
        title=_(u'UPCNews',
                default=u"Habilitar portlet Upc News"),
        description=_(u'help_genweb_portlets_upcnews',
                      default=u"Habilita el portlet Upc News."),
        required=False,
        default=False,
    )

    ulearn_portlets_mytags = schema.Bool(
        title=_(u'ulearn_portlets_mytags',
                default=u"Habilitar portlet ulearn_portlets_mytags"),
        description=_(u'help_ulearn_portlets_mytags',
                      default=u"Habilita portlet amb el núvol de tags."),
        required=False,
        default=False,
    )

    ulearn_portlets_mycommunities = schema.Bool(
        title=_(u'ulearn_portlets_mycommunities',
                default=u"Habilitar portlet ulearn_portlets_mycommunities"),
        description=_(u'help_ulearn_portlets_mycommunities',
                      default=u"Habilita el portlet que mostra les comunitats on estic suscrit o puc suscriurem."),
        required=False,
        default=False,
    )

    ulearn_portlets_custombuttonbar = schema.Bool(
        title=_(u'ulearn_portlets_custombuttonbar',
                default=u"Habilitar portlet ulearn_portlets_custombuttonbar"),
        description=_(u'help_ulearn_portlets_custombuttonbar',
                      default=u"Habilita el portlet per a poder customitzar la botonera."),
        required=False,
        default=False,
    )

    ulearn_portlets_subscribednews = schema.Bool(
        title=_(u'ulearn_portlets_subscribednews',
                default=u"Habilitar portlet ulearn_portlets_subscribednews"),
        description=_(u'help_ulearn_portlets_subscribednews',
                      default=u"Habilita el portlet per a veure les notícies les quals contenen un tag que segueixo."),
        required=False,
        default=False,
    )

    ulearn_portlets_mysubjects = schema.Bool(
        title=_(u'ulearn_portlets_mysubjects',
                default=u"Habilitar portlet ulearn_portlets_mysubjects"),
        description=_(u'help_ulearn_portlets_mysubjects',
                      default=u"Habilita el portlet per a poder veure els meus cursos del EVA."),
        required=False,
        default=False,
    )

    ulearn_portlets_angularrouteview = schema.Bool(
        title=_(u'ulearn_angularRouteView',
                default=u"Habilitar portlet angularRouteView"),
        description=_(u'help_ulearn_angularRouteView',
                      default=u"Habilita el portlet angular per a poder fer ús de les rutes angularjs."),
        required=False,
        default=True,
    )

    ulearn_portlets_flashesinformativos = schema.Bool(
        title=_(u'ulearn_portlets_flashesinformativos',
                default=u"Habilitar portlet flashesinformativos"),
        description=_(u'help_ulearn_portlets_flashesinformativos',
                      default=u"Habilita el portlet para mostrar las notícias en el flash informativo."),
        required=False,
        default=False,
    )

    ulearn_portlets_importantnews = schema.Bool(
        title=_(u'ulearn_portlets_importantnews',
                default=u"Habilitar portlet importantnews"),
        description=_(u'help_ulearn_portlets_importantnews',
                      default=u"Habilita el portlet para mostrar las notícias marcadas como destacadas."),
        required=False,
        default=False,
    )

    ulearn_portlets_buttonbar = schema.Bool(
        title=_(u'ulearn_button_bar',
                default=u"Habilitar portlet Ulearn Button Bar"),
        description=_(u'help_ulearn_button_bar',
                      default=u"Habilita el portlet botonera central."),
        required=False,
        default=True,
    )

    ulearn_portlets_communities = schema.Bool(
        title=_(u'ulearn_communities',
                default=u"Habilitar portlet Ulearn Comunnities"),
        description=_(u'help_ulearn_communities',
                      default=u"Habilita el portlet lateral on mostra les comunitats favorites."),
        required=False,
        default=True,
    )

    ulearn_portlets_profile = schema.Bool(
        title=_(u'ulearn_profile',
                default=u"Habilitar portlet Ulearn Profile"),
        description=_(u'help_ulearn_profile',
                      default=u"Habilita el portlet on mostra el perfil usuari, o la comunitat on estem."),
        required=False,
        default=True,
    )

    ulearn_portlets_thinnkers = schema.Bool(
        title=_(u'ulearn_thinkers',
                default=u"Habilitar portlet Ulearn Thinkers"),
        description=_(u'help_ulearn_thinkers',
                      default=u"Habilita el portlet on es mostren els usuaris, amb la cerca ."),
        required=False,
        default=True,
    )

    ulearn_portlets_calendar = schema.Bool(
        title=_(u'ulearn_calendar',
                default=u"Habilitar portlet ulearn Calendar"),
        description=_(u'help_ulearn_calendar',
                      default=u"Habilita el portlet per a mostrar el calendari amb els events."),
        required=False,
        default=True,
    )

    ulearn_portlets_discussion = schema.Bool(
        title=_(u'ulearn_discussion',
                default=u"Habilitar portlet Ulearn Discussion"),
        description=_(u'help_ulearn_discussion',
                      default=u"Habilita el portlet."),
        required=False,
        default=False,
    )

    ulearn_portlets_econnect = schema.Bool(
        title=_(u'ulearn_econnect',
                default=u"Habilitar portlet Ulearn eConnect"),
        description=_(u'help_ulearn_econnect',
                      default=u"Habilita el portlet eConnect."),
        required=False,
        default=False,
    )

    ulearn_portlets_mostvalued = schema.Bool(
        title=_(u'ulearn_most_valued',
                default=u"Habilitar portlet Ulearn Most Valued"),
        description=_(u'help_ulearn_most_valued',
                      default=u"Habilita el portlet ulearn most valued."),
        required=False,
        default=False,
    )

    ulearn_portlets_stats = schema.Bool(
        title=_(u'ulearn_stats',
                default=u"Habilitar portlet Ulearn Stats"),
        description=_(u'help_ulearn_stats',
                      default=u"Habilita el portlet per a veure les estadístiques."),
        required=False,
        default=True,
    )

    # ==== FIN Portlets ====

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
        title=_(u'url_forget_password',
                default=u'URL contrasenya oblidada'),
        description=_(u'help_url_forget_password',
                      default=u'Url per defecte: "/mail_password_form?userid=". Per a dominis externs indiqueu la url completa, "http://www.domini.cat"'),
        required=True,
        default=u'/mail_password_form?userid=')


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

        site = getSite()
        activate_portlets = []
        portlets_slots = ["plone.leftcolumn", "plone.rightcolumn",
                          "genweb.portlets.HomePortletManager1",
                          "genweb.portlets.HomePortletManager2",
                          "genweb.portlets.HomePortletManager3"]

        for manager_name in portlets_slots:
            if 'genweb' in manager_name:
                manager = getUtility(IPortletManager, name=manager_name, context=site['front-page'])
                mapping = getMultiAdapter((site['front-page'], manager), IPortletAssignmentMapping)
                [activate_portlets.append(item[0]) for item in mapping.items()]
            else:
                manager = getUtility(IPortletManager, name=manager_name, context=site)
                mapping = getMultiAdapter((site, manager), IPortletAssignmentMapping)
                [activate_portlets.append(item[0]) for item in mapping.items()]

        portlets = {k: v for k, v in data.iteritems() if 'portlet' in k}
        if portlets:
            for portlet, value in portlets.iteritems():
                idPortlet = portlet.replace('_', '.')
                namePortlet = portlet.replace('_', ' ')

                if portlet == 'genweb_portlets_news_events_listing':
                    idPortlet = 'genweb.portlets.news_events_listing'
                    namePortlet = 'genweb portlets news_events_listing'

                if value is True:
                    registerPortletType(site,
                                        title=namePortlet,
                                        description=namePortlet,
                                        addview=idPortlet)

                if idPortlet.split('.')[-1] in activate_portlets:
                    value = True
                    data[portlet] = True
                    registerPortletType(site,
                                        title=namePortlet,
                                        description=namePortlet,
                                        addview=idPortlet)
                if value is False:
                    unregisterPortletType(site, idPortlet)

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
