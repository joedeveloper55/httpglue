# Copyright 2021 Joseph P McAnulty. All rights reserved.
import datetime as _datetime
import inspect as _inspect
import logging as _logging
import re as _re

# TODO
# 2. finish up unit tests, add default reason phrases
#    see if we can optimize some parts, like pre-compiling regexes, sppeding up some checks, beings strategic with func calls
# 3. clean up code formating and style, make sure exception messages are consistent (remove or add httpglue.* stuff in messages)
# 4. complete docs and doctest
# 5. remove asgi parts

_ASCII_CHARS = {
    chr(val)
    for val in range(0, 128)
}

_CTL_CHARS = {  # (octets 0 - 31) and DEL (127)>
    chr(val)
    for val in range(0, 32)
}
_CTL_CHARS.add(chr(127))

_SEP_CHARS = {
    '(', ')', '<', '>', '@',
    ',', ';', ':', '\\', '/',
    '[', ']', '?', '=', '{',
    '}', ' ', '\t'
}
_VALID_RFC_2616_TOKEN_CHARS = \
    _ASCII_CHARS - _CTL_CHARS - _SEP_CHARS

_VALID_RFC_2616_TEXT_CHARS = \
    (_ASCII_CHARS - _CTL_CHARS) | {' ', '\t'}

_DEFAULT_REASON_PHRASE_MAPPING = {
    200: 'OK'
}


class NoMatchingPathError(Exception):
    def __init__(self, path, path_specs):
        message = (
            f'The path \'{path}\' did '
            'not match any of {path_specs}'
        )
        self.path = path
        self.path_specs = path_specs
        super().__init__(message)


class NoMatchingMethodError(Exception):
    def __init__(
        self,
        method,
        path,
        allowed_methods,
        matching_path_specs
    ):
        message = (
            f'The \'{method}\' method is not one '
            'of the allowed methods ({allowed_methods}) '
            f'on \'{path}\' '
            '(matching path specs: {matching_path_specs})'
        )
        super().__init__(message)
        self.method = method
        self.path = path
        self.allowed_methods = allowed_methods
        self.matching_path_specs = matching_path_specs


class NoMatchingPredError(Exception):
    def __init__(
        self,
        method,
        path,
        matching_method_spec_path_spec_pairs,
        failed_predicates
    ):
        message = (
            f'The \'{method} {path}\' request nearly '
            'matched an endpoint, but failed due to predicates'
        )
        super().__init__(message)
        self.method = method
        self.path = path
        self.matching_method_spec_path_spec_pairs = \
            matching_method_spec_path_spec_pairs
        self.failed_predicates = failed_predicates


class WSGIRequestMappingError(Exception):
    def __init__(self):
        message = (
            'An httpglue.Request object could not be made from the '
            'wsgi callable. This is probably a framework bug or a bug '
            'in the wsgi server you\'re running your app in.'
        )
        super().__init__(message)


class WSGIResponseMAppingError(Exception):
    def __init__(self):
        message = (
            'An httpglue.Response object could not be used by the '
            'wsgi callable to make a response to the requester. '
            'This is probably a framework bug or a bug in the wsgi server '
            'you\'re running your app in.'
        )
        super().__init__(message)


class Headers:

    def __init__(self, *args, **kwargs):
        if len(args) == 0:
            self._impl_dict = dict()
        elif len(args) == 1 and self._looks_like_a_mapping(args[0]):
            provisional_impl_dict = dict(args[0])
            self._validate_mapping(provisional_impl_dict)
            provisional_impl_dict = {
                self._convert_key_to_camel_dash_form(k): v
                for k, v in provisional_impl_dict.items()
            }
            self._impl_dict = provisional_impl_dict
        elif len(args) == 1:  # assume an iterable of two, tuples
            provisional_impl_dict = dict(args[0])
            self._validate_mapping(provisional_impl_dict)
            provisional_impl_dict = {
                self._convert_key_to_camel_dash_form(k): v
                for k, v in provisional_impl_dict.items()
            }
            self._impl_dict = provisional_impl_dict
        else:
            raise TypeError(
                f'Headers expected at most 1 '
                f'arguments, got {len(args)}'
            )

        # support kwargs
        for k, v in kwargs.items():
            self._validate_key(k)
            k = self._convert_key_to_camel_dash_form(k)
            self._validate_value(v)
            self._impl_dict[k] = v

    @classmethod
    def fromkeys(cls, keys, val=''):
        return cls((k, val) for k in keys)

    def _normalize_header_val(self, val):
        val = val.lstrip().rstrip()
        val = ' '.join(val.split())
        return val

    def _convert_key_to_camel_dash_form(self, key):
        key_parts = key.split('-')
        key_parts = [
            val[0].upper() + val[1:].lower()
            for val in key_parts]
        key = '-'.join(key_parts)
        return key

    def _validate_key(self, key):
        if type(key) != str:
            raise TypeError( # add specific value to message?
                f'Headers key must be of type \'str\', not '
                f'{type(key)}'
            )

        if len(key) < 1:
            raise ValueError(
                'Headers key must be at least one char long'
            )

        inappropriate_chars = set(key) - _VALID_RFC_2616_TOKEN_CHARS

        if len(inappropriate_chars) != 0:
            raise ValueError(
                'Headers key %s is not a valid rfc2616 token. '
                'It had %s chars in it which are not allowed. '
                'Only these chars are allowed: %s.' % (
                    key, inappropriate_chars,
                    _VALID_RFC_2616_TOKEN_CHARS
                )
            )

    def _validate_value(self, val):
        if type(val) != str:
            raise TypeError(
                f'Headers value must be of type \'str\', not '
                f'{type(val)}'
            )

        inappropriate_chars = set(val) - _VALID_RFC_2616_TEXT_CHARS

        if len(inappropriate_chars) != 0:
            raise ValueError(
                'Headers value %s is not a valid rfc2616 text. '
                'It had %s chars in it which are not allowed. '
                'Only these chars are allowed: %s.' % (
                    val, inappropriate_chars,
                    _VALID_RFC_2616_TEXT_CHARS
                )
            ) 

    def _looks_like_a_mapping(self, val):
        # here, we check a bunch of properties/methods
        # to figure out if some object is highly likely
        # to be some kind of 'Mapping'. We opted
        # for this approach instead of just testing for abstract
        # base classes to maximize the flexibility and
        # interoperability of the headers class
        minimum_mapping_methods = {
            '__getitem__', 
            '__iter__', 
            '__len__',
            '__contains__',
            'keys',
            'items',
            'values',
            'get',
            '__eq__',
            '__ne__'
        }
        return set(dir(val)) >= minimum_mapping_methods

    def _validate_mapping(self, mapping):
        for key in mapping:
            self._validate_key(key)
            self._validate_value(mapping[key])

    def __contains__(self, key):
        self._validate_key(key)
        key = self._convert_key_to_camel_dash_form(key)
        return key in self._impl_dict

    def __getitem__(self, key):
        self._validate_key(key)
        key = self._convert_key_to_camel_dash_form(key)
        try:
            return self._impl_dict[key]
        except KeyError:
            raise KeyError(key)

    def __setitem__(self, key, val):
        self._validate_key(key)
        key = self._convert_key_to_camel_dash_form(key)
        self._validate_value(val)
        self._impl_dict[key] = val

    def __delitem__(self, key):
        self._validate_key(key)
        key = self._convert_key_to_camel_dash_form(key)
        try:
            del self._impl_dict[key]
        except KeyError:
            raise KeyError(key)

    def __eq__(self, other):
        if type(other) != Headers:
            return False

        key_diff = set(self.keys()) ^ set(other.keys())
        if key_diff != set():
            return False

        for k in self.keys():
            if (self._normalize_header_val(self[k]) !=
                self._normalize_header_val(other[k])
            ):
                return False

        return True

    def __ne__(self, other):
        return not (self == other)
    
    __hash__ = None
        
    def __iter__(self):
        return iter(self._impl_dict)
        
    def items(self):
        return self._impl_dict.items()
        
    def keys(self):
        return self._impl_dict.keys()

    def values(self):
        return self._impl_dict.values()

    def copy(self):
        return Headers(self)

    def __len__(self):
        return len(self._impl_dict)

    def __repr__(self):
        return ''.join([
            'Headers(',
            repr(self._impl_dict),
            ')'
        ])
    
    def __str__(self):
        return '\r\n'.join([
            ': '.join([name, self._normalize_header_val(value)])
            for name, value in self.items()
        ])

    def get(self, key, default=None):
        self._validate_key(key)
        key = self._convert_key_to_camel_dash_form(key)
        return self._impl_dict.get(key, default)

    def setdefault(self, key, default=''):
        self._validate_key(key)
        self._validate_value(default)
        key = self._convert_key_to_camel_dash_form(key)
        return self._impl_dict.setdefault(key, default)

    def pop(self, key, default=None):
        self._validate_key(key)
        key = self._convert_key_to_camel_dash_form(key)
        return self._impl_dict.pop(key, default)

    def popitem(self):
        try:
            return self._impl_dict.popitem()
        except KeyError:
            raise KeyError('popitem(): Headers is empty')

    def clear(self):
        self._impl_dict.clear()

    def update(self, other):
        self._validate_mapping(other)
        self._impl_dict.update(other)


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
        path_vars=None,
        query_str='',
        start_time=None
    ):
        self.http_version = http_version
        self.method = method
        self.path = path
        self.path_vars = \
            {} if path_vars is None else path_vars
        self.query_str = query_str
        self.headers = headers
        self.body = body
        self.start_time = start_time
        self.host = host
        self.port = port
        self.proto = proto

    @property
    def http_version(self):
        return self._http_version

    @http_version.setter
    def http_version(self, value):
        if type(value) not in (type(None), str):
            raise TypeError(
                'http_version attribute of httpglue.Request object '
                'must be of type str or NoneType, got %s' % type(value)
            )

        self._http_version = value

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

        if len(value) < 1:
            raise ValueError(
                'method attribute of httpglue.Request object '
                'must be at least one character long.'
            )

        inappropriate_chars = set(value) - _VALID_RFC_2616_TOKEN_CHARS

        if len(inappropriate_chars) != 0:
            raise ValueError(
                'httpglue.Request.method \'%s\' is not a valid rfc2616 token. '
                'It had %s chars in it which are not allowed. '
                'Only these chars are allowed: %s.' % (
                    value, inappropriate_chars,
                    _VALID_RFC_2616_TOKEN_CHARS
                ))

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
        if '?' in value:
            raise ValueError(
                '? was in the query_Str: %s. It is implicit, '
                'don\'t include it. Do not ' % value
            )
        self._query_str = value

    @property
    def headers(self):
        return self._headers

    @headers.setter
    def headers(self, value):
        if type(value) not in (dict, Headers):
            raise TypeError(
                'headers attribute of httpglue.Response object '
                'must be of type dict or httpglue.Headers, '
                'got %s' % type(value)
            )
        self._headers = Headers(value) if type(value) else value

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
        if type(value) not in (type(None), _datetime.datetime):
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
        headers_part = str(self.headers)

        return f'{request_line_part}\r\n{headers_part}\r\n\r\n{self.body}'
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
                'status attribute of Response object '
                'must be of type \'int\', got \'%s\'' % type(value)
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
                'reason attribute of Response object '
                'must be of type \'str\', got \'%s\'' % type(value)
            )

        inappropriate_chars = set(value) - _VALID_RFC_2616_TOKEN_CHARS

        if len(inappropriate_chars) != 0:
            raise ValueError(
                'Response.reason \'%s\' is not a valid rfc2616 token. '
                'It had %s chars in it which are not allowed. '
                'Only these chars are allowed: %s.' % (
                    value, inappropriate_chars,
                    _VALID_RFC_2616_TOKEN_CHARS
                ))

        self._reason = value

    @property
    def headers(self):
        return self._headers

    @headers.setter
    def headers(self, value):
        if type(value) not in (dict, Headers):
            raise TypeError(
                'headers attribute of Response object '
                'must be of type \'dict\' or \'Headers\', '
                'got \'%s\'' % type(value)
            )
        
        self._headers = Headers(value) if type(value) == dict else value

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
        headers_part = str(self.headers)

        return f'{status_part}\r\n{headers_part}\r\n\r\n{self.body}'


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
        if not isinstance(logger, _logging.Logger):
            raise TypeError(
             'expected logger to be of type '
             '%s. got %s' % (_logging.Logger, type(logger)))

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
                    'characters %s were found in %s' %
                    (str(set(header_val) & set('\t\r\n\0\a\b\v\f')),
                    header_val))

        self.default_fallback_err_res = default_fallback_err_res

        """
        The _endpoint_table attribute below will have a stucture like this:

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
        The err_routing_table attribute below will have a stucture
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
                self._extract_header_name(key): str(val)
                for (key, val) in environ.items()
                if key.startswith('HTTP_')
            }
            if 'CONTENT_TYPE' in environ:
                req_headers['Content-Type'] = str(environ['CONTENT_TYPE'])
            if 'CONTENT_LENGTH' in environ:
                req_headers['Content-Length'] = str(environ['CONTENT_LENGTH'])

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
                start_time=_datetime.datetime.now()
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
                if not set(header_val) & set('\t\r\n\0\a\b\v\f') == set():
                    raise ValueError(
                        'wsgi has a special stipulation that header '
                        'values must not contain control characters. '
                        'Control characters %s were found in %s' %
                        (str(set(header_val) & set('\t\r\n\0\a\b\v\f')),
                        header_val))
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
        path_vars.update(enumerate(_re.match(pattern, path).groups()))
        path_vars.update(_re.match(pattern, path).groupdict())
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
        call_signature = _inspect.signature(f)

        params_right_length = len(call_signature.parameters) == 2

        params_right_kind = all(
            param.kind == _inspect.Parameter.POSITIONAL_OR_KEYWORD
            and param.default == _inspect.Parameter.empty
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
        call_signature = _inspect.signature(f)

        params_right_length = len(call_signature.parameters) == 1

        param = list(call_signature.parameters.values())[0]
        param_right_kind = (
            param.kind == _inspect.Parameter.POSITIONAL_OR_KEYWORD
            and param.default == _inspect.Parameter.empty
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
        call_signature = _inspect.signature(f)

        params_right_length = len(call_signature.parameters) == 3

        params_right_kind = all(
            param.kind == _inspect.Parameter.POSITIONAL_OR_KEYWORD
            and param.default == _inspect.Parameter.empty
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

            if _re.match(f"^{endpoint['path_spec']}$", req.path):
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

    def register_err_handler(
        self,
        excs_list,
        f
    ):
        pass

    async def startup(self):
        pass

    async def shutdown(self):
        pass

    async def handle_request(self, req):
        pass
