# -*- coding: utf-8 -*-
from five import grok
from zope import schema
from itertools import chain
from z3c.form import button
from zope.interface import Interface
from zope.component.hooks import getSite
from zope.component import getMultiAdapter
from zope.component import queryUtility

from plone.directives import form
from plone.registry.interfaces import IRegistry

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.statusmessages.interfaces import IStatusMessage

from ulearn.core import _
from ulearn.core.controlpanel import IUlearnControlPanelSettings
from ulearn.theme.browser.interfaces import IUlearnTheme

import json
import requests

BBB_ENDPOINT = 'http://corronco.upc.edu:8088/webservices/addReservationNotification.php'
BBB_SERVER = 'corronco'


class IReservaBBB(form.Schema):
    """ Form for BBB reservation - Paràmetres: Servidor, Data inici, Durada,
        Descripció, Creador, Carrega, Invitats Convidats, Invitats Moderadors
        Retorna: ID Reserva (permesa), 0 (no permesa).

        http://corronco.upc.edu:8088/webservices/addReservationNotification.php?
        servidor =corronco&inici=2013-04-02-13&durada=13&carrega=10&descripcio=D
        escripcio&owner=u suari.creador@upcnet.es&invite_rw=moderator1%40upcnet
        .es%2Cmoderator2%40upcnet.es&invite_ro=invited1%40upcnet.es%2Cinvited2%
        40gmail.com   --> exemple
    """

    nom_reunio = schema.TextLine(
        title=_(u"Nom de la reunió"),
        description=_(u"Indiqueu la descripció de la reunió virtual."),
        required=True
    )

    start_date = schema.Datetime(
        title=_(u"Data d'inici"),
        description=_(u"Indiqueu la data d'inici de la reserva."),
        required=True
    )

    durada = schema.Choice(
        title=_(u"Durada de la reunió"),
        description=_(u"Indiqueu durada de la reunió."),
        values=range(1, 25),
        required=True
    )

    invitats_convidats = schema.TextLine(
        title=_(u"Convidats moderadors"),
        description=_(u"Llista d'emails dels convidats MODERADORS, separats per comes."),
        required=True
    )

    invitats_espectadors = schema.TextLine(
        title=_(u"Invitats espectadors"),
        description=_(u"Llista d'emails dels convidats ESPECTADORS, separats per comes."),
        required=False
    )

    # carrega = schema.Choice(
    #     title=_(u"Nombre de convidats total"),
    #     description=_(u"Indiqueu el nombre total d'assistents previstos."),
    #     values=range(2, 26),
    #     required=True
    # )


class reservaBBB(form.SchemaForm):
    grok.name('addBBBReservation')
    grok.context(IPloneSiteRoot)
    grok.require('genweb.member')

    schema = IReservaBBB
    ignoreContext = True

    label = _(u"Create new meeting space")

    def update(self):
        super(reservaBBB, self).update()
        self.request.set('disable_border', True)
        self.request.set('disable_plone.rightcolumn', True)
        self.actions['save'].addClass('context')
        self.actions['cancel'].addClass('standalone')

    @button.buttonAndHandler(_(u'Save'), name="save")
    def handleApply(self, action):
        portal = getSite()
        pm = getToolByName(portal, 'portal_membership')
        userid = pm.getAuthenticatedMember()

        user_email = userid.getProperty('email', '')

        if not user_email:
            IStatusMessage(self.request).addStatusMessage(
                _(u"La reunió no es pot crear perquè l'usuari no te informat la adreca de correu electrònic."),
                u"error"
            )
            self.request.response.redirect(portal.absolute_url())

        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        str_start_date = data.get('start_date').isoformat().replace('T', '-')[:-6]
        str_invitats_convidats = data.get('invitats_convidats', '').replace(' ', '')
        str_invitats_espectadors = data.get('invitats_espectadors', '').replace(' ', '')

        guests = data.get('invitats_convidats')
        session_load = len(guests.split(','))

        payload = dict(servidor=BBB_SERVER,
                       inici=str_start_date,
                       durada=data.get('durada'),
                       carrega=session_load,
                       descripcio=data.get('nom_reunio'),
                       owner=user_email,
                       invite_rw=str_invitats_convidats,
                       invite_ro=str_invitats_espectadors,)

        req = requests.post(BBB_ENDPOINT, data=payload)

        try:
            # Redirect back to the front page with a status message
            if int(req.text) > 0:
                IStatusMessage(self.request).addStatusMessage(
                    _(u"La reunió virtual ha estat creada."),
                    u"info"
                )
            else:
                IStatusMessage(self.request).addStatusMessage(
                    _(u"Hi ha hagut algun problema i la reunió virtual no ha estat creada."),
                    u"info"
                )
        except:
            IStatusMessage(self.request).addStatusMessage(
                _(u"Hi ha hagut algun problema i la reunió virtual no ha estat creada."),
                u"info"
            )

        self.request.response.redirect(portal.absolute_url())

    @button.buttonAndHandler(_(u"Cancel"), name="cancel")
    def cancel(self, action):
        IStatusMessage(self.request).addStatusMessage(_(u"Edit cancelled."), type="info")
        self.request.response.redirect(self.context.absolute_url())
        return ''


class AjaxUserSearch(grok.View):
    grok.context(Interface)
    grok.name('genweb.ajaxusersearch')
    grok.require('genweb.authenticated')
    grok.layer(IUlearnTheme)

    def render(self):
        self.request.response.setHeader("Content-type", "application/json")
        query = self.request.form.get('q', '')
        results = dict(more=False, results=[])
        registry = queryUtility(IRegistry)
        settings = registry.forInterface(IUlearnControlPanelSettings)

        if query:
            portal = getSite()
            hunter = getMultiAdapter((portal, self.request), name='pas_search')
            fulluserinfo = hunter.merge(chain(*[hunter.searchUsers(**{field: query}) for field in ['fullname', 'name']]), 'userid')
            values = [dict(id=userinfo.get('login'), text=u'{} ({})'.format(userinfo.get('title'), userinfo.get('login'))) for userinfo in fulluserinfo]

            if settings.vip_users:
                if query in settings.vip_users:
                    # Fa falta?
                    pass

            results['results'] = values
            return json.dumps(results)
        else:
            return json.dumps({"error": "No query found"})
