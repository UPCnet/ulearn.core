from plone import api
from infrae.rest import REST as REST_BASE
from infrae.rest.interfaces import RESTMethodPublishedEvent
from infrae.rest.components import IRESTComponent
from infrae.rest.interfaces import MethodNotAllowed
from zeam.component import getComponent

from zExceptions import NotFound
from zope.event import notify
from zope.component import queryUtility

from plone.registry.interfaces import IRegistry

from maxclient import MaxClient
from mrs.max.browser.controlpanel import IMAXUISettings
import json


_marker = object()
ALLOWED_REST_METHODS = ('GET', 'POST', 'HEAD', 'PUT', 'DELETE')

import logging
logger = logging.getLogger(__name__)


class MethodNotImplemented(Exception):
    """This method is not implemented in this class
    """
    def __init__(self, klass, method):
        self.args = (klass, method)
        self.message = '{}.{}'.format(klass, method)


def queryRESTComponent(specs, args, name=u'', parent=None, id=_marker, placeholder=None):
    """Query the ZCA for a REST component.
    """
    factory = getComponent(specs, IRESTComponent, name, default=None)
    if factory is not None:
        result = factory(*args)
        if result is not None and IRESTComponent.providedBy(result):
            # Set parenting information / for security
            if id is _marker:
                id = name
            result.__name__ = id
            result.__parent__ = parent
            result.__matchdict__ = {}
            result.__matchdict__.update(getattr(parent, '__matchdict__', {}))
            if placeholder is not None:
                result.__matchdict__.update(placeholder)

            return result
    return None

from five import grok


class REST(REST_BASE):
    grok.baseclass()
    """
        Enchanced version of infrae.rest REST class, that can behave like a
        generic url part. To make use of the generic behaviour, derived classes
        need two attributes:

        placeholder_id
        placeholder_type

        the placeholder_type must be the lowercase name of a class in the same
        nesting pattern defined in infrae.rest. The placeholder_id, is the key
        that will be used to store the url part in the class instance
        __matchdict__ object. This dict will accomulate all generic REST
        components in the way.

        if no placeholder_* attributes found, default behaviour will remain.
        Any nested REST class defined with a name trying to be a placeholder
        will be treated as the nestes class.
    """

    def browserDefault(self, request):
        """Render the component using a method called the same way
        that the HTTP method name.
        """
        if request.method in ALLOWED_REST_METHODS:
            if hasattr(self, request.method):
                return self, (request.method,)
            else:
                raise MethodNotImplemented(str(self.__class__), request.method)
        raise MethodNotAllowed(request.method)

    def get_max_client(self):
        registry = queryUtility(IRegistry)
        maxui_settings = registry.forInterface(IMAXUISettings)

        maxclient = MaxClient(maxui_settings.max_server, maxui_settings.oauth_server)
        maxclient.setActor(maxui_settings.max_restricted_username)
        maxclient.setToken(maxui_settings.max_restricted_token)

        return maxclient

    def validate(self):
        """
            Validates request params

            Returns True if request is correct otherwise returns an error
        """
        if not self.extract_params():
            self.response.setStatus(404)
            return self.json_response(dict(error='Missing parameters',
                                           status_code=404))

        return True

    def check_roles(self, obj=None, roles=[]):
        allowed = False
        if obj:
            user_roles = api.user.get_roles(obj=obj)
        else:
            user_roles = api.user.get_roles()

        for role in roles:
            if role in user_roles:
                allowed = True

        if not allowed:
            self.response.setStatus(401)
            return self.json_response(dict(error='You are not allowed to modify this object',
                                           status_code=401))

        return allowed

    def check_permission(self, obj, permission):
        if not api.user.has_permission(permission, obj):
            self.response.setStatus(401)
            return self.json_response(dict(error='You are not allowed to modify this object',
                                           status_code=401))

        return True

    def extract_params(self):
        """
            Extract parameters from request and stores them ass class attributes
            Returns false if some required parameter is missing
        """
        required = getattr(self, '__required_params__', [])
        required += self.__matchdict__.keys()
        self.params = {}
        self.params.update(self.__matchdict__)
        self.params.update(self.request.form)
        try:
            self.payload = json.loads(self.request['BODY'])
        except:
            pass
        else:
            self.params.update(self.payload)

        # Return False if param not found or empty
        for param_name in required:
            if param_name not in self.params:
                return False
            elif self.params[param_name] in [[], {}, None, '']:
                return False

        return True

    def publishTraverse(self, request, name):
        """You can traverse to a method called the same way that the
        HTTP method name, or a sub view
        """
        overriden_method = request.getHeader('X-HTTP-Method-Override', None)
        is_valid_overriden_method = overriden_method in ['DELETE', 'PUT']
        is_POST_request = request.method.upper() == 'POST'
        is_valid_override = is_valid_overriden_method and is_POST_request
        request_method = overriden_method if is_valid_override else request.method

        if request_method != request.method:
            request.method = request_method

        if name in ALLOWED_REST_METHODS and name == request.method:
            if hasattr(self, request_method):
                notify(RESTMethodPublishedEvent(self, name))
                return getattr(self, request_method)

        view = queryRESTComponent(
            (self, self.context),
            (self.context, request),
            name=name,
            parent=self)

        placeholder = getattr(self, 'placeholder_type', None)

        if view is None and placeholder is not None:
            placeholder_id = getattr(self, 'placeholder_id')
            view = queryRESTComponent(
                (self, self.context),
                (self.context, request),
                name=placeholder,
                parent=self,
                placeholder={placeholder_id: name}
            )
        if view is None:
            raise NotFound(name)
        return view

    def lookup_community(self):
        pc = api.portal.get_tool(name='portal_catalog')
        result = pc.searchResults(community_hash=self.params['community'])

        if not result:
            # Fallback search by gwuuid
            result = pc.searchResults(gwuuid=self.params['community'])

            if not result:
                # Not found either by hash nor by gwuuid
                self.response.setStatus(404)
                error_response = 'Community hash not found: {}'.format(self.params['community'])
                logger.error(error_response)
                return self.json_response(dict(error=error_response, status_code=404))

        self.community = result[0].getObject()
        return True
