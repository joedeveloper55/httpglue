# Copyright 2021, Joseph P McAnulty

import datetime
import inspect            
import logging
import re
from functools import partial

from . import Req
from . import Res
from .exceptions import NoMatchingMethodError
from .exceptions import NoMatchingPathError
from .exceptions import NoMatchingPredError


class App:

    def __init__(
        self,
        logger,
        default_fallback_err_res
    ):
        """
        Creates the httglue.wsgi.App object. The App
        object is a valid wsgi application object that can
        be directly used by wsgi servers as soon as it is
        instantiated.

        A logger must be supplied, which will be used by
        the framework to log out details about its operations.

        A default fallback error response must also be suppled,
        which is what the framework will use as its response when
        unhandled errors occur.

        The created App object can then begin to have endpoints and
        error handlers registered to it to define application behavior.
        """
        if not isinstance(logger, logging.Logger):
            raise TypeError(
             'expected logger to be of type '
             '%s. got %s' % (logging.Logger, type(logger)))
        
        self.logger = logger

        if not isinstance(default_fallback_err_res, Res):
            raise TypeError(
             'expected default_fallback_err_res to be of type '
             '%s. got %s' % (Res, type(default_fallback_err_res)))

        # this logic here is needed to enfore a special rule that wsgi
        # itself (not the http spec) enforces with regards to header
        # values. Since the default_fallback_err_res must always be
        # able to be sent without error, we must ensure this here
        for header_val in default_fallback_err_res.headers.values():
            if not set(header_val) & set('\t\r\n\0\a\b\v\f') == {}:
                raise ValueError(
                    'wsgi has a special stipulation that header values '
                    'must not contain control characters. Control characters'
                    '%s were found in %s',
                    str(set(header_val) & set('\t\r\n\0\a\b\v\f')),
                    header_val) 
        
        self.default_fallback_err_res = default_fallback_err_res

        """
        [
            {
                'path_spec': r'/widgets/(\d*)',
                'method_spec': {'GET', 'POST'},
                'pred': None,
                'req_handler': f
            }
        ]
        """
        self.endpoint_table = []

        """
        [
            {
                exceptions_list: (CustomError1, CustomError2),
                err_handler: f1

            }
        ]
        """
        self.err_routing_table = []

    def __call__(self, environ, start_response):
        """
        Implements the wsgi application entrypoint. The presence
        of this method makes the httpglue.wsgi.App object a 
        valid wsgi app usableby wsgi servers.

        :param dict environ: the wsgi environ dict containing
           the request information from the wsgi server for an
           incoming request

        :param start_response: the wsgi start_response callable
           used to set the status code, reason, and headers of the
           response

        :rtype list: a list of bytes
        """
        try:
            req_headers = {
                self._extract_header_name(key): val
                for (key, val) in environ.items()
                if key.startswith('HTTP_')
            }
            if 'CONTENT_TYPE' in environ:
                req_headers['Content-Type'] = environ['CONTENT_TYPE']
            if 'CONTENT_LENGTH' in environ:
                req_headers['Content-Length'] = environ['CONTENT_LENGTH']

            # The usage of the .get(VAR, '') idiom below is due
            # to the stipulations in the wsgi spec stating that
            # some of these keys must be present, but may be absent
            # if their value is the empty str. Leave this idiom alone
            # for maximum portability amongst wsgi servers.
            req = Req(
                method=environ['REQUEST_METHOD'],
                path=environ.get('PATH_INFO', ''),
                query_str=environ.get('QUERY_STRING', ''),
                headers=req_headers,
                body=environ['wsgi.input'].read(),
                host=environ['SERVER_NAME'],
                port=int(environ['SERVER_PORT']),
                proto=environ['wsgi.url_scheme'],
                http_version=environ.get('SERVER_PROTOCOL', ''),
                start_time=datetime.datetime.now()
            )

        except Exception as e:
            self.logger.exception(
                'an httpglue.Req object could not be made from the wsgi callable. '
                'this is probably a framework bug, a bug in the wsgi server '
                'you\'re running your app in, or some system error'
            )
            res = self.default_fallback_err_res

        else:
            res = self.handle_request(req)

        try:
            # there are a number of constraints around the
            # reson phrase in the wsgi spec and http spec. it must have
            # a three character numeric status code, followed by a space,
            # followed by a reason phrase, which may be empty. the reason
            # phrase must contain no control characters and must not have
            # following whitespace. This code helps ensure that form in all
            # cases
            wsgi_res_status_str = (
                str(res.status) + ' '
                if not res.reason
                else ' '.join([res.status, res.reason])
            )

            for header_val in res.headers.values():
                if not set(header_val) & set('\t\r\n\0\a\b\v\f') == {}:
                    raise ValueError(
                        'wsgi has a special stipulation that header values '
                        'must not contain control characters. Control characters'
                        '%s were found in %s',
                        str(set(header_val) & set('\t\r\n\0\a\b\v\f')),
                        header_val)
            wsgi_res_headers = list(res.headers.items())
            
            wsgi_res_body = res.body

            start_response(wsgi_res_status_str, wsgi_res_headers)
            return [wsgi_res_body]
        
        except Exception as e:
            self.logger.exception(
                'an httpglue.Res object could not be used by the wsgi callable '
                'to make a response to the requester. '
                'this is probably a framework bug, a bug in the wsgi server '
                'you\'re running your app in, or some system error'
            )
            res = self.default_fallback_err_res
            # this is okay because on app instantiation we made sure
            # that the default fallback err res is always okay. This code
            # SHOULD NEVER FAIL. 
            wsgi_res_status_str = (
                str(res.status) + ' '
                if not res.reason
                else ' '.join([res.status, res.reason])
            )
            wsgi_res_headers = list(res.headers.items())
            wsgi_res_body = res.body

            start_response(wsgi_res_status_str, wsgi_res_headers)
            return [wsgi_res_body]

    def _extract_header_name(self, wsgi_environ_key):
        if not wsgi_environ_key.startswith('HTTP_'):
            raise ValueError('only HTTP_ Vars should be passed in')

        # remove HTTP_ prefix
        wsgi_environ_key = wsgi_environ_key[5:]
        # lowecase the whole thing
        wsgi_environ_key = wsgi_environ_key.lower()
        # replace _ with -
        wsgi_environ_key = wsgi_environ_key.replace('_', '-')
        # uppercase first letter of each part
        wsgi_environ_key = '-'.join(
            f'{x[0].upper()}{x[1:]}'
            for x in wsgi_environ_key.split('-'))

        return wsgi_environ_key

    def _extract_path_vars(self, path_spec, path):
        pattern = f'^{path_spec}$'
        path_vars = {}
        path_vars.update(enumerate(re.match(pattern, path).groups()))
        path_vars.update(re.match(pattern, path).groupdict())
        return path_vars

    def _validate_path_spec(self, spec):
        is_str_type = isinstance(spec, str)
        if not is_str_type:
            raise TypeError(
                'The path spec must be of type str, '
                'got %s' % type(spec)
            )
        starts_with_carrot = spec.startswith('^')
        if starts_with_carrot:
            raise ValueError(
                'The path spec regex must not start with '
                '^, it is implicitly added by the framework'
            )

        ends_with_dollar_sign = spec.endswith('$')
        if ends_with_dollar_sign:
            raise ValueError(
                'The path spec regex must not end with '
                '$, it is implicitly added by the framework'
            )

    def _validate_method_spec(self, spec):
        is_set_type = isinstance(spec, set)
        if not is_set_type:
            raise TypeError(
                'The method spec must be of type \'set\', '
                'got %s' % type(spec))

        has_only_str_type_items = all(type(e) is str for e in spec)
        if not has_only_str_type_items:
            raise TypeError(
                'all types in the method spec must be str, '
                'got types %s' % list(type(e) for e in spec))

    def _validate_excs_list(self, excs_list):
        if type(excs_list) != list:
            raise TypeError(
                f'The exception list for your error handler must '
                'be of type list, got type %s' % str(type(excs_list)))

        if any(not issubclass(e_type, Exception)for e_type in excs_list):
            raise TypeError(
                'every type in the excs_list must be a subclass of '
                'Exception for your error handler. '
                'got types %s' % list(type(e) for e in excs_list))

    def _validate_req_handler(self, f):
        call_signature = inspect.signature(f)

        params_right_length = len(call_signature.parameters) == 1

        param = list(call_signature.parameters.values())[0]
        param_right_kind = (
            param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
            and param.default == inspect.Parameter.empty
        )
        
        if not (params_right_length and param_right_kind):
            raise ValueError(
                'a valid request handler must be a callable '
                'that takes in a single positional argument, but '
                'the passed %s callable  had a signature of '
                '%s' % (
                    getattr(f, '__name__', 'Unnamed'),
                    call_signature
                )
            )

    def _validate_pred(self, f):
        call_signature = inspect.signature(f)

        params_right_length = len(call_signature.parameters) == 1

        param = list(call_signature.parameters.values())[0]
        param_right_kind = (
            param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
            and param.default == inspect.Parameter.empty
        )
        
        if not (params_right_length and param_right_kind):
            raise ValueError(
                'a valid predicate function must be a callable '
                'that takes in a single positional argument, but '
                'the passed %s callable had a signature of '
                '%s' % (
                    getattr(f, '__name__', 'Unnamed'),
                    call_signature
                )
            )

    def _validate_err_handler(self, f):
        call_signature = inspect.signature(f)

        params_right_length = len(call_signature.parameters) == 2

        params_right_kind = all(
            param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
            and param.default == inspect.Parameter.empty
            for param in call_signature.parameters.values() 
        )
        
        if not (params_right_length and params_right_kind):
            raise ValueError(
                'a valid error handler must be a callable '
                'that takes in two positional arguments, but '
                'the passed %s callable  had a signature of '
                '%s' % (
                    getattr(f, '__name__', 'Unnamed'),
                    call_signature
                )
            )

    def endpoint(self, method_spec, path_spec, pred=None):
        """
        A convenience method that returns a decorator capable
        of regisering an endpoint with the httpglue.App object
        when applied to a valid request handler.

        An endpoint is a unit of functionality receiving a request
        and retuning a response exposed for requests with given methods,
        path structure, and/or that satisfy certain predicates (pred).

        :param set method_spec: a set of http methods as str types
           that qualify for this endpoint. The special '*' value
           is a wildcard that allows any method at all to qualify.

        :param str path_spec: a regex without a leading ^ or trailing
           $ (these are impicitly added by the framework) that
           specifies the structure of paths qualifying for this endpoint.
           Capture groups define parts of the path that will be available
           in the path_vars property of httpglue.Req object passed into
           the endpoint's request handler

        :param pred: an optional callable object with the signature
           (req: httpglue.Req) -> bool. If present, when this evaluates
           to false, even if the request method and path of the incoming
           request qualifies for an endpoint, the request will not qualify
           for and be routed to that endpoint 
        """
        return partial(self.register_endpoint, method_spec, path_spec, pred=pred)

    def register_endpoint(self, method_spec, path_spec, request_handler, pred=None):
        """
        Register an endpoint with the httpglue.App object.

        An endpoint is a unit of functionality receiving a request
        and retuning a response exposed for requests with given methods,
        path structure, and/or that satisfy certain predicates (pred).

        It returns the request handler of the registered endpoint

        :param set method_spec: a set of http methods as str types
           that qualify for this endpoint. The special '*' value
           is a wildcard that allows any method at all to qualify.

        :param str path_spec: a regex without a leading ^ or trailing
           $ (these are impicitly added by the framework) that
           specifies the structure of paths qualifying for this endpoint.
           Capture groups define parts of the path that will be available
           in the path_vars property of httpglue.Req object passed into
           the endpoint's request handler

        :param request_handler: a callable object with the signature
           (req: httpglue.Req) -> httpglue.Res which is responsible
           for representing the functionality of the endpoint and returning
           a response

        :param pred: an optional callable object with the signature
           (req: httpglue.Req) -> bool. If present, when this evaluates
           to false, even if the request method and path of the incoming
           request qualifies for an endpoint, the request will not qualify
           for and be routed to that endpoint 
        """
        self._validate_method_spec(method_spec)
        self._validate_path_spec(path_spec)
        self._validate_req_handler(request_handler)
        if pred is not None:
            self._validate_pred(pred)
        self.endpoint_table.append({
            'path_spec': path_spec,
            'method_spec': method_spec,
            'pred': pred,
            'req_handler': request_handler

        })
        return request_handler

    def err_handler(self, excs_list):
        """
        an err_handler function should have a signature
        of (exc, req: Req) -> Res
        """
        return partial(self.register_err_handler, excs_list)

    def register_err_handler(self, excs_list, f):
        """
        x
        """
        self._validate_excs_list(excs_list)
        self._validate_err_handler(f)
        self.err_routing_table.append({
            'exceptions_list': tuple(excs_list),
            'err_handler': f
        })
        return f

    def handle_request(self, req):
        """
        Handle a Req object in this App, routing it to the right
        endpoint and/or error handlers as
        neccesary and getting and returning a Res object.
        
        After the App object's __call__method is invoked by a wsgi
        server, the __call__ method constructs a Req object and
        passes it to this method to get a Res object. In general,
        your application code should seldom if ever call this directly;
        The wsgi server will invoke __call__ which will invoke this method.
        
        It was made public rather than private to help you with unit testing
        and interactive exploration/debugging of an httpglue application.
        In your test code, you can use it to completely bypass
        all wsgi logic, enabling more simple and stable
        unit tests of your app.

        :param httpglue.Req req: an httpglue.Req object

        :rtype: httpglue.Res
        """

        if not isinstance(req, Req):
            raise TypeError(f'expected type {type(Req)}, got {type(req)}')

        # these are defensive copies we need for later logging purposes,
        # since the req object may be mutated during the course of
        # being handled
        incoming_req_method = req.method
        incoming_req_path = req.path

        self.logger.debug(
            'Request recieved (%s %s):\n%s',
            incoming_req_method,
            incoming_req_path,
            str(req)
        )

        try:
            # attempt to map req to appropriate endpoint
            matching_path_spec_found = False
            matching_method_spec_found = False
            matching_pred_found = False
            matching_path_specs = set()
            unmatched_methods = set()
            matching_method_spec_path_spec_pairs = list()
            failed_predicates = list()
            
            for endpoint in self.endpoint_table:
                
                if re.match(f"^{endpoint['path_spec']}$", req.path):
                    matching_path_spec_found = True
                    matching_path_specs.add(endpoint['path_spec'])
                else:
                    continue
                    
                if req.method in endpoint['method_spec'] or '*' in endpoint['method_spec']:
                    matching_method_spec_found = True
                else:
                    unmatched_methods.update(endpoint['method_spec'])
                    continue

                if endpoint['pred'] is None:
                    # we've successfully routed to a chosen endpoint, so break out of the loop
                    chosen_endpoint = endpoint
                    break
                elif endpoint['pred'](req):
                    matching_pred_found = True
                    # we've successfully routed to a chosen endpoint, so break out of the loop
                    chosen_endpoint = endpoint
                    break
                else:
                    matching_method_spec_path_spec_pairs.append(
                        (endpoint['method_spec'], endpoint['path_spec'])
                    )
                    failed_predicates.append(endpoint['pred'])
                    continue

            else:  # we failed to route to any endpoint
                if not matching_path_spec_found:
                    raise NoMatchingPathError(
                        req.path,
                        [
                            endpoint['path_spec']
                            for endpoint in self.endpoint_table
                        ]
                    )
                elif not matching_method_spec_found:
                    raise NoMatchingMethodError(
                        req.method,
                        req.path,
                        unmatched_methods,
                        matching_path_specs
                    )
                elif not matching_pred_found:
                    raise NoMatchingPredError(
                        req.method,
                        req.path,
                        matching_method_spec_path_spec_pairs,
                        failed_predicates
                    )

            self.logger.debug(
                'Request "%s %s" routed to endpoint '
                '%s %s%s',
                incoming_req_method,
                incoming_req_path,
                chosen_endpoint['method_spec'],
                chosen_endpoint['path_spec'],
                f' (pred={chosen_endpoint["pred"].__name__})' if matching_pred_found else ''
            )
            
            # populate the path vars
            req.path_vars= self._extract_path_vars(chosen_endpoint['path_spec'], incoming_req_path)

            # attempt to actually handle the req, getting a res
            req_handler = chosen_endpoint['req_handler']
            res = req_handler(req)

            # attempt to validate and return the res
            # it is an unrecoverable error for the handler to not return
            # a httpglue.Res object; that results in the default_fallback_err_res
            # being returned
            if isinstance(res, Res): 
                self.logger.debug(
                    'Response for (%s %s):\n%s',
                    incoming_req_method,
                    incoming_req_path,
                    str(res)
                )
                self.logger.info(
                    '%s %s %s',
                    incoming_req_method,
                    incoming_req_path,
                    res.status
                )
                return res
            else:
                self.logger.error(
                    'request handler must return an object of type httpglue.Res, '
                    'not %s, returning default_fallback_err_res' % type(res)
                )
                return self.default_fallback_err_res
        
        except Exception as e:
            # an exception happened in the course of routing or handling a request,
            # so give an err_handler a chance to 'do something about it' if one
            # matches.

            # attempt to map exception to appropriate err handler
            for error_handler in self.err_routing_table:
                if any(isinstance(e, handled_exc) for handled_exc in error_handler['exceptions_list']):
                    chosen_error_handler = error_handler
                    break
            else:  # we failed to route to any err handler
                self.logger.exception(
                    'No err_handler matched exception. '
                    'returning default_fallback_err_response'
                )
                self.logger.debug(
                    'Response for (%s %s):\n%s',
                    incoming_req_method,
                    incoming_req_path,
                    str(self.default_fallback_err_res)
                )
                self.logger.info(
                    '%s %s %s',
                    incoming_req_method,
                    incoming_req_path,
                    self.default_fallback_err_res.status
                )
                return self.default_fallback_err_res
            try:
                self.logger.debug(
                    'Request "%s %s" routed to err_handler '
                    '%s for exeption %s',
                    incoming_req_method,
                    incoming_req_path,
                    list(chosen_error_handler['exceptions_list']),
                    type(e)
                )

                res = chosen_error_handler['err_handler'](e, req)

                # attempt to validate and return the res
                # it is an unrecoverable error for the handler to not return
                # a httpglue.Res object; that results in the default_fallback_err_res
                # being returned
                if isinstance(res, Res):
                    self.logger.debug(
                        'Response for (%s %s):\n%s',
                        incoming_req_method,
                        incoming_req_path,
                        str(res)
                    )
                    self.logger.info(
                        '%s %s %s',
                        incoming_req_method,
                        incoming_req_path,
                        res.status
                    )
                    return res
                else:
                    self.logger.error(
                        'err handler must return an object of type Res, '
                        'not %s, returning default_fallback_err_Res' % type(res)
                    )
                    self.logger.debug(
                        'Response for (%s %s):\n%s',
                        incoming_req_method,
                        incoming_req_path,
                        str(self.default_fallback_err_res)
                    )
                    self.logger.info(
                        '%s %s %s',
                        incoming_req_method,
                        incoming_req_path,
                        self.default_fallback_err_res.status
                    )
                    return self.default_fallback_err_res
            
            except Exception as e:
                # it is an unrecoverable error for the handler to
                # raise any exceptions; that results in the default_fallback_err_res
                # being returned
                self.logger.exception(
                    'An exception was thrown inside an err_handler. '
                    'returning default_fallback_err_response'
                )
                self.logger.debug(
                    'Response for (%s %s):\n%s',
                    incoming_req_method,
                    incoming_req_path,
                    str(self.default_fallback_err_res)
                )
                self.logger.info(
                    '%s %s %s',
                    incoming_req_method,
                    incoming_req_path,
                    self.default_fallback_err_res.status
                )
                return self.default_fallback_err_res
