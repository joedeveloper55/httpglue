# Copyright 2021, Joseph P McAnulty
import datetime
import inspect
import logging
import re


class NoMatchingPathError(Exception):
    def __init__(self, path, path_specs):
        message = f'The path \'{path}\' did not match any of {path_specs}'
        super().__init__(message)


class NoMatchingMethodError(Exception):
    def __init__(self, method, path, allowed_methods, matching_path_specs):
        message = (
            f'The \'{method}\' method is not one of the allowed methods {allowed_methods} '
            f'on \'{path}\' (matching path specs: {matching_path_specs})'
        )
        super().__init__(message)
        self.method = method
        self.path = path
        self.allowed_methods = allowed_methods
        self.matching_path_specs = matching_path_specs


class NoMatchingPredError(Exception):
    def __init__(self, method, path, matching_method_spec_path_spec_pairs, failed_predicates):
        message = (
            f'The \'{method} {path}\' request nearly matched some endpoints, but failed due to predicates'
        )
        super().__init__(message)
        self.method = method
        self.path = path
        self.matching_method_spec_path_spec_pairs = matching_method_spec_path_spec_pairs
        self.failed_predicates = failed_predicates


class WSGIRequestMappingError(Exception):
    def __init__(self):
        message = (
            'an httpglue.Request object could not be made from the '
            'wsgi callable. this is probably a framework bug, a bug '
            'in the wsgi server you\'re running your app in, or some '
            'system error'
        )
        super().__init__(message)


class WSGIResponseMAppingError(Exception):
    def __init__(self):
        message = (
            'an httpglue.Response object could not be used by the '
            'wsgi callable to make a response to the requester. '
            'this is probably a framework bug, a bug in the wsgi server '
            'you\'re running your app in, or some system error'
        )
        super().__init__(message)


class Request:
    def __init__(
        self,
        method,
        path,
        headers,
        body,
        host=None,
        port=None,
        proto='http',
        http_version=None,
        path_vars={},
        query_str='',
        start_time=None
    ):
        self.http_version = http_version
        self.method = method
        self.path = path
        self.path_vars = path_vars
        self.query_str = query_str
        self.headers = headers
        self.body = body
        self.start_time = start_time
        self.host = host
        self.port = port
        self.proto = proto

    @property
    def method(self):
        return self._method

    @method.setter
    def method(self, value):
        if type(value) is not str:
            raise TypeError(
                'method attribute of httpglue.Request object '
                'must be of type str, got %s' % type(value)
            )
        self._method = value

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        if type(value) is not str:
            raise TypeError(
                'path attribute of httpglue.Request object '
                'must be of type str, got %s' % type(value)
            )
        if '?' in value:
            raise ValueError(
                '? was in the path: %s. This means you '
                'have a query string in here. Do not '
                'supply the query string here, supply it '
                'in the query_args property of the '
                'httpglue.Request object instead' % value
            )
        self._path = value

    @property
    def path_vars(self):
        return self._path_vars

    @path_vars.setter
    def path_vars(self, value):
        if type(value) is not dict:
            raise TypeError(
                'path_vars attribute of httpglue.Request object '
                'must be of type dict, got %s' % type(value)
            )
        self._path_vars = value

    @property
    def query_str(self):
        return self._query_str

    @query_str.setter
    def query_str(self, value):
        if type(value) is not str:
            raise TypeError(
                'query_str attribute of httpglue.Request object '
                'must be of type str, got %s' % type(value)
            )
        self._query_str = value

    @property
    def headers(self):
        return self._headers

    @headers.setter
    def headers(self, value):
        if type(value) is not dict:
            raise TypeError(
                'headers attribute of httpglue.Response object '
                'must be of type dict, got %s' % type(value)
            )
        self._headers = value

    @property
    def body(self):
        return self._body

    @body.setter
    def body(self, value):
        if type(value) is not bytes:
            raise TypeError(
                'body attribute of httpglue.Response object '
                'must be of type bytes, got %s' % type(value)
            )
        self._body = value

    @property
    def start_time(self):
        return self._start_time

    @start_time.setter
    def start_time(self, value):
        if type(value) not in (type(None), datetime.datetime):
            raise TypeError(
                'start_time attribute of httpglue.Response object '
                'must be of type datetime.datetime or NoneType, got %s' % type(value)
            )
        self._start_time = value

    @property
    def host(self):
        return self._host

    @host.setter
    def host(self, value):
        if type(value) not in (type(None), str):
            raise TypeError(
                'host attribute of httpglue.Response object '
                'must be of type str or NoneType, got %s' % type(value)
            )
        self._host = value

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, value):
        if type(value) not in (type(None), int):
            raise TypeError(
                'port attribute of httpglue.Response object '
                'must be of type int or NoneType, got %s' % type(value)
            )
        self._port = value

    @property
    def proto(self):
        return self._proto

    @proto.setter
    def proto(self, value):
        if type(value) not in (type(None), str):
            raise TypeError(
                'proto attribute of httpglue.Response object '
                'must be of type str or NoneType, got %s' % type(value)
            )
        self._proto = value

    @property
    def full_url(self):
        if None in (self.proto, self.host, self.port):
            raise ValueError(
                'The Request object\'s proto, host, and port properties'
                ' must all be not None to use the full_url property.')

        return (
            f'{self.proto}://'
            f'{self.host}:{self.port}'
            f'{self.path}'
            f'?{self.query_str}'
        )

    def deep_validate(self):
        raise NotImplementedError()

    def __repr__(self):
        args_part = ', '.join([
            f'method={repr(self.method)}',
            f'path={repr(self.path)}',
            f'headers={repr(self.headers)}',
            f'body={repr(self.body)}',
            f'host={repr(self.host)}',
            f'port={repr(self.port)}',
            f'proto={repr(self.proto)}',
            f'http_version={repr(self.http_version)}',
            f'path_vars={repr(self.path_vars)}',
            f'query_str={repr(self.query_str)}',
            f'start_time={repr(self.start_time)}'
        ])
        return f'Request({args_part})'

    def __str__(self):
        query_str_part = f'?{self.query_str}' if self.query_str else ''
        request_line_part = (
            f'{self.method} '
            f'{self.path}{query_str_part} '
            f'{self.http_version}'
        )
        headers_part = '\n'.join(
            f'{key}: {value}'
            for key, value in self.headers.items()
        )

        return f'{request_line_part}\n{headers_part}\n\n{self.body}'
        return super().__str__()


class Response:
    def __init__(
        self,
        status,
        headers,
        body,
        reason='',
    ):
        self.status = status
        self.reason = reason
        self.headers = headers
        self.body = body

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        if type(value) is not int:
            raise TypeError(
                'status attribute of httpglue.Response object '
                'must be of type int, got %s' % type(value)
            )
        if value < 100 or value > 599:
            raise ValueError(
                'valid http status codes must be '
                'between 100 and 599, got %s' % value
            )
        self._status = value

    @property
    def reason(self):
        return self._reason

    @reason.setter
    def reason(self, value):
        if type(value) is not str:
            raise TypeError(
                'reason attribute of httpglue.Response object '
                'must be of type str, got %s' % type(value)
            )

        self._reason = value

    @property
    def headers(self):
        return self._headers

    @headers.setter
    def headers(self, value):
        if type(value) is not dict:
            raise TypeError(
                'headers attribute of httpglue.Response object '
                'must be of type dict, got %s' % type(value)
            )
        self._headers = value

    @property
    def body(self):
        return self._body

    @body.setter
    def body(self, value):
        if type(value) is not bytes:
            raise TypeError(
                'body attribute of httpglue.Response object '
                'must be of type bytes, got %s' % type(value)
            )
        self._body = value

    def __repr__(self):
        args_part = ', '.join([
            f'status={repr(self.status)}',
            f'headers={repr(self.headers)}',
            f'body={repr(self.body)}',
            f'reason={repr(self.reason)}'
        ])
        return f'Response({args_part})'

    def __str__(self):
        status_part = f'HTTP {self.status} {self.reason}'
        headers_part = '\n'.join(
            f'{key}: {value}'
            for key, value in self.headers.items()
        )

        return f'{status_part}\n{headers_part}\n\n{self.body}'


class WsgiApp:

    def __init__(
        self,
        logger,
        default_fallback_err_res
    ):
        """
        Creates the WsgiApp object. The WsgiApp
        object is a valid wsgi application object that can
        be directly used by wsgi servers as soon as it is
        instantiated with no extra steps.

        A logger must be supplied, which will be used by
        the framework to log out details about its operations.

        A default fallback error response must also be suppled,
        which is what the framework will use as its response when
        unhandled errors occur.

        The created WsgiApp object can have endpoints and
        error handlers registered to it to define application behavior
        via its register_endpoint and register_err_handler methods.

        :param logging.Logger logger: the logger to use for logging
           out what's going on in this framework

        :param httpglue.Response default_fallback_err_res: the response
           to send back in the case of unhandled errors

        :rtype httpglue.WsgiApp: the newly constructed httpglue WsgiApp
        """
        if not isinstance(logger, logging.Logger):
            raise TypeError(
             'expected logger to be of type '
             '%s. got %s' % (logging.Logger, type(logger)))

        self.logger = logger

        if not isinstance(default_fallback_err_res, Response):
            raise TypeError(
             'expected default_fallback_err_res to be of type '
             '%s. got %s' % (Response, type(default_fallback_err_res)))

        # this logic here is needed to enfore a special rule that wsgi
        # itself (not the http spec) enforces with regards to header
        # values. Since the default_fallback_err_res should always be
        # able to be sent without error, we must ensure this here
        for header_val in default_fallback_err_res.headers.values():
            if not set(header_val) & set('\t\r\n\0\a\b\v\f') == set():
                raise ValueError(
                    'wsgi has a special stipulation that header values '
                    'must not contain control characters. Control '
                    'characters %s were found in %s',
                    str(set(header_val) & set('\t\r\n\0\a\b\v\f')),
                    header_val)

        self.default_fallback_err_res = default_fallback_err_res

        """
        The _endpoint_table property below will have a stucture like this:

        [
            {
                'path_spec': '/widgets/(\\d*)',
                'method_spec': ['GET', 'POST'],
                'pred': None,
                'req_handler': f
            },
            ...
        ]
        """
        self._endpoint_table = []

        """
        The err_routing_table property below will have a stucture
        like this:

        [
            {
                exceptions_list: (CustomError1, CustomError2),
                err_handler: f1

            }
        ]
        """
        self._err_handler_table = []

    def __call__(self, environ, start_response):
        """
        Implements the wsgi application entrypoint. The presence
        of this method makes the WsgiApp object a
        valid wsgi app usable by wsgi servers.

        Application developers should generallly not need to call
        this method, as that will usually be done by the wsgi
        server their app is running in.

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
            req = Request(
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

        except Exception:
            self.logger.exception(
                'an httpglue.Request object could not be made from '
                'the wsgi callable. This is probably a framework '
                'bug or a bug in the wsgi server you\'re running your '
                'app in.'
            )
            res = self.default_fallback_err_res

        else:
            res = self.handle_request(req)

        try:
            # there are a number of constraints around the
            # reson phrase in the wsgi spec and http spec.
            # It must have a three character numeric status code,
            # followed by a space, followed by a reason phrase, which
            # may be empty. the reason phrase must contain no control
            # characters and must not have following whitespace. This
            # code helps ensure that form in all cases
            wsgi_res_status_str = (
                str(res.status) + ' '
                if not res.reason
                else ' '.join([res.status, res.reason])
            )

            for header_val in res.headers.values():
                if not set(header_val) & set('\t\r\n\0\a\b\v\f') == {}:
                    raise ValueError(
                        'wsgi has a special stipulation that header '
                        'values must not contain control characters. '
                        'Control characters %s were found in %s',
                        str(set(header_val) & set('\t\r\n\0\a\b\v\f')),
                        header_val)
            wsgi_res_headers = list(res.headers.items())

            wsgi_res_body = res.body

            start_response(wsgi_res_status_str, wsgi_res_headers)
            return [wsgi_res_body]

        except Exception:
            self.logger.exception(
                'an httpglue.Response object could not be used by the wsgi '
                'callable to make a response to the requester. '
                'this is probably a framework bug or a bug in the wsgi '
                'server you\'re running your app in.'
            )
            res = self.default_fallback_err_res

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

    def _validate_path_spec(self, path_spec):
        is_str_type = isinstance(path_spec, str)
        if not is_str_type:
            raise TypeError(
                'expected path_spec to be of type str. '
                'got %s' % type(path_spec)
            )
        starts_with_carrot = path_spec.startswith('^')
        if starts_with_carrot:
            raise ValueError(
                'The path_spec regex must not start with '
                '^, it is implicitly added by the framework'
            )

        ends_with_dollar_sign = path_spec.endswith('$')
        if ends_with_dollar_sign:
            raise ValueError(
                'The path_spec regex must not end with '
                '$, it is implicitly added by the framework'
            )

    def _validate_method_spec(self, method_spec):
        is_list_type = isinstance(method_spec, list)
        if not is_list_type:
            raise TypeError(
                'expected method_spec to be of type list, '
                'got %s' % type(method_spec))

        has_only_str_type_items = all(type(e) is str for e in method_spec)
        if not has_only_str_type_items:
            raise TypeError(
                'every item in the method_spec list must be of type str, '
                'got types %s' % list(type(e) for e in method_spec))

    def _validate_excs_list(self, excs_list):
        if type(excs_list) != list:
            raise TypeError(
                'expected excs_list to be of type list. '
                'got type %s' % str(type(excs_list)))

        if any(not issubclass(e_type, Exception)for e_type in excs_list):
            raise TypeError(
                'every item in the excs_list list must be a subclass of '
                'Exception. '
                'got types %s' % list(e_type for e_type in excs_list))

    def _validate_req_handler(self, f):
        call_signature = inspect.signature(f)

        params_right_length = len(call_signature.parameters) == 2

        params_right_kind = all(
            param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
            and param.default == inspect.Parameter.empty
            for param in call_signature.parameters.values()
        )

        if not (params_right_length and params_right_kind):
            raise ValueError(
                'a valid request handler must be a callable '
                'that takes in 2 positional arguments, but '
                'the passed %s callable had a signature of '
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

        params_right_length = len(call_signature.parameters) == 3

        params_right_kind = all(
            param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
            and param.default == inspect.Parameter.empty
            for param in call_signature.parameters.values()
        )

        if not (params_right_length and params_right_kind):
            raise ValueError(
                'a valid error handler must be a callable '
                'that takes in three positional arguments, but '
                'the passed %s callable  had a signature of '
                '%s' % (
                    getattr(f, '__name__', 'Unnamed'),
                    call_signature
                )
            )

    def _choose_endpoint(self, req):
        chosen_endpoint = None

        # keep track of what is going on during routing
        # so we can correctly report the cause of routing
        # failure along with appropriate detials of the failure
        matching_path_spec_found = False
        matching_method_spec_found = False
        matching_pred_found = False
        matching_path_specs = set()
        unmatched_methods = set()
        matching_method_spec_path_spec_pairs = list()
        failed_predicates = list()

        for endpoint in self._endpoint_table:

            if re.match(f"^{endpoint['path_spec']}$", req.path):
                matching_path_spec_found = True
                matching_path_specs.add(endpoint['path_spec'])
            else:
                continue

            if (req.method in endpoint['method_spec']
                or '*' in endpoint['method_spec']
            ):
                matching_method_spec_found = True
            else:
                unmatched_methods.update(endpoint['method_spec'])
                continue

            if endpoint['pred'] is None:
                # we've successfully routed to a chosen endpoint,
                # so break out of the loop
                chosen_endpoint = endpoint
                break
            elif endpoint['pred'](req):
                matching_pred_found = True
                # we've successfully routed to a chosen endpoint,
                # so break out of the loop
                chosen_endpoint = endpoint
                break
            else:
                matching_method_spec_path_spec_pairs.append(
                    (endpoint['method_spec'], endpoint['path_spec'])
                )
                failed_predicates.append(endpoint['pred'])
                continue

        if chosen_endpoint is None:
            if not matching_path_spec_found:
                raise NoMatchingPathError(
                    req.path,
                    [
                        endpoint['path_spec']
                        for endpoint in self._endpoint_table
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

        return chosen_endpoint

    def _choose_err_handler(self, e):
        chosen_error_handler = None
        for error_handler in self._err_handler_table:
            if any(
                isinstance(e, handled_exc)
                for handled_exc in error_handler['exceptions_list']
            ):
                chosen_error_handler = error_handler
                break

        return chosen_error_handler

    def register_endpoint(
        self,
        method_spec,
        path_spec,
        request_handler,
        pred=None
    ):
        """
        Register an endpoint with the WsgiApp object.

        An endpoint is a unit of functionality that can recieve a request,
        do some things, and return a response when the incoming request
        'matches' with it.

        An incoming request 'matches' an endpoint if both its method is in
        the method_spec list and if its path is matched by the path_spec
        regex. If pred is defined, then for the request to match that
        endpoint pred must evaluate to True when invoked on the incoming
        request even if the endpoint matches otherwise.

        When the incoming request matches an endpoint, that endpoint's
        request handler will be invoked and no more endpoints will be
        tried for a match. Endpoints are tried for matches in the order
        that they were registered.

        This method returns the request_handler arg passed into it.

        :param list method_spec: a list of http methods as str types
           that match for this endpoint. The special '*' value
           is a wildcard that allows any method at all to match.

        :param str path_spec: a regex without a leading ^ or trailing
           $ (these are impicitly added by the framework) that
           specifies the structure of paths matching for this endpoint.
           Capture groups define parts of the path that will be available
           in the path_vars property of httpglue.Request object passed into
           the endpoint's request handler

        :param request_handler: a callable object with the signature
           (app: httpglue.WsgiApp, req: httpglue.Request) -> httpglue.Response
           which is responsible for representing the functionality of the
           endpoint and returning a response. It is an error for one of
           these callables to return anything other than a Response object;
           They can however raise an exception, which may get a chance to be
           handled in an error handler.

        :param pred: an optional callable object with the signature
           (req: httpglue.Request) -> bool. If present, when this evaluates
           to False, even if the request method and path of the incoming
           request matches for an endpoint, the request will not match
           that endpoint. If True, the request will match that endpoint.
           It is an error for the pred function to return anything other
           than True or False or to raise an exception.
        """
        self._validate_method_spec(method_spec)
        self._validate_path_spec(path_spec)
        self._validate_req_handler(request_handler)
        if pred is not None:
            self._validate_pred(pred)
        self._endpoint_table.append({
            'path_spec': path_spec,
            'method_spec': method_spec,
            'pred': pred,
            'req_handler': request_handler

        })
        return request_handler

    def register_err_handler(self, excs_list, f):
        """
        Register an error handler with the WsgiApp object.

        An error handler is a unit of functionality that can intercept
        an error raised during request routing or handling a request in
        a request handler. It cannot intercept an error raised in itself
        or another error handler.

        A raised error 'matches' a given error handler if that error's
        type is a subtype of one of the types in that error handler's
        excs_list. All value's in an error handler's excs_list must be
        type objects that are subtypes of Exception.

        When the raised error matches an error handler, that handler's
        function will be invoked and no more error handlers will be
        tried for a match. Error handlers are tried for matches in the
        order that they were registered.

        This method returns the f arg passed into it.

        :param list excs_list: a list of exception types
           that match for this endpoint. Subtypes will match.

        :param f: a callable object with the signature
           (app: httpglue.WsgiApp, e: Exception, req: httpglue.Request) ->
           httpglue.Response which is responsible for representing the
           functionality of the error handler and returning a response
        """
        self._validate_excs_list(excs_list)
        self._validate_err_handler(f)
        self._err_handler_table.append({
            'exceptions_list': tuple(excs_list),
            'err_handler': f
        })
        return f

    def handle_request(self, req):
        """
        Handle a Request object in the WsgiApp, routing it to the right
        endpoint and/or error handlers as
        neccesary and getting and returning a Response object.

        After the WsgiApp object's __call__method is invoked by a wsgi
        server, the __call__ method constructs a Request object and
        passes it to this method to get a Response object. In general,
        your application code should seldom if ever call this directly;
        The wsgi server will invoke __call__ which will invoke this method.

        It was made public rather than private to help you with unit testing
        and interactive exploration/debugging of an httpglue application.
        In your test code, you can use it to completely bypass
        all wsgi logic, enabling more simple and stable
        unit tests of your app.

        :param httpglue.Request req: an httpglue.Request object

        :rtype: httpglue.Response
        """

        if not isinstance(req, Request):
            raise TypeError(
                f'expected req to be of type {type(Request)}. got {type(req)}')

        # these are defensive copies we need for later logging purposes,
        # since the req object may be mutated during the course of
        # being handled
        incoming_req_method = req.method
        incoming_req_path = req.path

        self.logger.debug(
            'Request recieved (%s %s): %s',
            incoming_req_method,
            incoming_req_path,
            repr(req)
        )

        try:

            chosen_endpoint = self._choose_endpoint(req)

            # populate the path vars
            req.path_vars = self._extract_path_vars(
                chosen_endpoint['path_spec'],
                incoming_req_path)

            self.logger.debug(
                'Request "%s %s" routed to endpoint '
                '%s %s%s',
                incoming_req_method,
                incoming_req_path,
                chosen_endpoint['method_spec'],
                chosen_endpoint['path_spec'],
                (
                    f' (pred={chosen_endpoint["pred"].__name__})'
                    if chosen_endpoint['pred'] is not None
                    else ''
                )
            )

            # attempt to actually handle the req, getting a res
            req_handler = chosen_endpoint['req_handler']
            res = req_handler(self, req)

            # attempt to validate and return the res
            # it is an unrecoverable error for the handler to not return
            # a httpglue.Response object; that results in the
            # default_fallback_err_res being returned
            if isinstance(res, Response):
                self.logger.debug(
                    'Response for (%s %s): %s',
                    incoming_req_method,
                    incoming_req_path,
                    repr(res)
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
                    'request handler must return an object of type '
                    'httpglue.Response, not %s. returning '
                    'default_fallback_err_res', type(res)
                )
                self.logger.info(
                    '%s %s %s',
                    incoming_req_method,
                    incoming_req_path,
                    self.default_fallback_err_res.status
                )
                return self.default_fallback_err_res

        except Exception as e:
            # an exception happened in the course of routing or handling
            # a request, so give an err_handler a chance to 'do something
            # about it' if one matches.

            try:

                chosen_error_handler = self._choose_err_handler(e)

                if chosen_error_handler is None:
                    self.logger.exception(
                        'No err_handler matched the exception. '
                        'returning default_fallback_err_response'
                    )
                    self.logger.debug(
                        'Response for (%s %s): %s',
                        incoming_req_method,
                        incoming_req_path,
                        repr(self.default_fallback_err_res)
                    )
                    self.logger.info(
                        '%s %s %s',
                        incoming_req_method,
                        incoming_req_path,
                        self.default_fallback_err_res.status
                    )
                    return self.default_fallback_err_res

                self.logger.debug(
                    'Request "%s %s" routed to err_handler '
                    '%s for exeption %s',
                    incoming_req_method,
                    incoming_req_path,
                    list(chosen_error_handler['exceptions_list']),
                    type(e)
                )

                res = chosen_error_handler['err_handler'](self, e, req)

                # attempt to validate and return the res
                # it is an unrecoverable error for the handler to not
                # return a httpglue.Response object; that results in the
                # default_fallback_err_res being returned
                if isinstance(res, Response):
                    self.logger.debug(
                        'Response for (%s %s): %s',
                        incoming_req_method,
                        incoming_req_path,
                        repr(res)
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
                        'err handler must return an object of type Response, '
                        'not %s, returning '
                        'default_fallback_err_res', type(res)
                    )
                    self.logger.debug(
                        'Response for (%s %s): %s',
                        incoming_req_method,
                        incoming_req_path,
                        repr(self.default_fallback_err_res)
                    )
                    self.logger.info(
                        '%s %s %s',
                        incoming_req_method,
                        incoming_req_path,
                        self.default_fallback_err_res.status
                    )
                    return self.default_fallback_err_res

            except Exception:
                # it is an unrecoverable error for an err handler to
                # raise any exceptions; that results in the
                # default_fallback_err_res being returned
                self.logger.exception(
                    'An exception was thrown inside an err_handler. '
                    'returning default_fallback_err_response'
                )
                self.logger.debug(
                    'Response for (%s %s): %s',
                    incoming_req_method,
                    incoming_req_path,
                    repr(self.default_fallback_err_res)
                )
                self.logger.info(
                    '%s %s %s',
                    incoming_req_method,
                    incoming_req_path,
                    self.default_fallback_err_res.status
                )
                return self.default_fallback_err_res


class AsgiApp:

    def __init__(self, logger, default_fallback_err_res):
        pass

    async def __call__(self, scope, recieve, send):
        pass

    def register_startup_routine(self, f):
        pass

    def register_shutdown_routine(self, f):
        pass

    def register_endpoint(
        self,
        method_spec,
        path_spec,
        request_handler,
        pred=None
    ):
        pass

    def register_err_handler(self, excs_list, f):
        pass

    async def startup(self):
        pass

    async def shutdown(self):
        pass

    async def handle_request(self, req):
        pass
