import json

from httpglue import Request
from httpglue import Response


class UnsupportedContentTypeError(Exception):
    def __init__(self, content_type, supported_types):
        message = (
            'cannot deserialize or serialize content of mime type %s, '
            'as it is not one of the supported types: % s'
            % (content_type, supported_types)
        )
        super().__init__(message)
        self.content_type = content_type
        self.supported_content_types = supported_types


class ContentDeserializationError(Exception):
    def __init__(self, content_type, content_bytes, error):
        message = (
            'there was an error deserializing '
            'content as % s' % content_type
        )
        super().__init__(message)
        self.content_type = content_type
        self.content_bytes = content_bytes
        self.error = error


class ContentSerializationError(Exception):
    def __init__(self, content_type, data, error):
        message = (
            'there was an error serializing '
            'content as % s' % content_type
        )
        super().__init__(message)
        self.content_type = content_type
        self.data = data
        self.error = error


class ContentHelper:
    def __init__(self):
        '''
        Initializes a ContentHelper.
        '''
        self.supported_mime_types = {}

    def add_support(self, mime_type, serializer, deserializer):
        '''
        Dynamically add serialization and deserialization
        capabilites for a new mime type to this ContentHelper.

        utf-8 encoding is always expected.

        :param list mime_types: a list of mime type strings
           specifying accepted content types
        :param deserializer: a function that takes an arbitrary
           object argument and returns a bytes object
        :param deserializer: a function that takes a single
           bytes type argument and returns an arbitrary
           object
        '''
        self.supported_mime_types[mime_type] = {
            'serializer': serializer,
            'deserializer': deserializer
        }

    def deserialize_req_body(self, mime_types, request):
        '''
        Attempt to deserialize the body of a request
        using the first matching value in mime_types.

        utf-8 encoding is always expected.

        It will raise an exception if the request's
        content type is not specified or if it doesn't
        match any values in mime_types.

        :param list mime_types: a list of mime type strings
           specifying accepted content types
        :param httpglue.Request request: the request holding
           the body to be deserialized

        :raises UnsupportedContentTypeError: when the request
           doesn't have a matching or supported mime type

        :raises ContentDeserializationError: when an unexpected
           deserialization error occurs

        :rtype: mixed
        '''
        directives = self._parse_directives(
            request.headers.get('Content-Type')
        )

        req_ct = directives.get('mime_type', '')
        if req_ct in mime_types and req_ct in self.supported_mime_types.keys():
            try:
                return self.supported_mime_types[req_ct]['deserializer'](
                    request.body,
                    directives['charset'],
                    directives['boundry'])
            except Exception as e:
                raise ContentDeserializationError(req_ct, request.body, e)
        else:
            supported_types = set(mime_types) & set(self.supported_mime_types)
            raise UnsupportedContentTypeError(req_ct, supported_types)

    def deserialize_res_body(self, mime_types, response):
        '''
        Attempt to deserialize the body of a response
        using the first matching value in mime_types.

        utf-8 encoding is always expected.

        It will raise an exception if the response's
        content type is not specified or if it doesn't
        match any values in mime_types.

        :param list mime_types: a list of mime type strings
           specifying accepted content types
        :param httpglue.Response response: the response holding
           the body to be deserialized

        :raises UnsupportedContentTypeError: when the response
           doesn't have a matching or supported mime type

        :raises ContentDeserializationError: when an unexpected
           deserialization error occurs

        :rtype: mixed
        '''
        directives = self._parse_directives(
            response.headers.get('Content-Type')
        )

        res_ct = directives.get('mime_type', '')
        if res_ct in mime_types and res_ct in self.supported_mime_types.keys():
            try:
                return self.supported_mime_types[res_ct]['deserializer'](
                    response.body,
                    directives['charset'],
                    directives['boundry'])
            except Exception as e:
                raise ContentDeserializationError(res_ct, response.body, e)
        else:
            supported_types = set(mime_types) & set(self.supported_mime_types)
            raise UnsupportedContentTypeError(res_ct, supported_types)

    def create_response(
        self,
        status,
        headers,
        data,
        reason=''
    ):
        '''
        Attempt to create an httpglue.Response object
        where data is serialized into bytes and placed
        in the body attribute according to the specified
        Content-Type header in headers.

        utf-8 encoding is always expected.

        It will raise an exception if the response's
        content type is not specified or if that specific
        content type is not supported by the ContentHelper.

        :param int status: the http status code of the response
           object getting created
        :param headers: a dict or httpglue.Headers object of
           the response object getting created
        :param data: any concievable value that can be deserialized
           to bytes used as the body property of the response
           object getting created
        :param str reason: the http reason of the response object
           getting created, if any

        :raises UnsupportedContentTypeError: when the ContentHelper
           doesn't have any support for serializing the content
           type specified in headers, or when no content type is
           specified

        :raises ContentSerializationError: when an unexpected
           serialization error occurs

        :rtype: httpglue.Response
        '''
        directives = self._parse_directives(
            headers.get('Content-Type')
        )

        res_ct = directives.get('mime_type', '')

        if res_ct in self.supported_mime_types.keys():
            try:
                body = self.supported_mime_types[res_ct]['serializer'](
                    data,
                    directives['charset'],
                    directives['boundry']
                )
                return Response(
                    status,
                    headers,
                    body,
                    reason
                )
            except Exception as e:
                raise ContentSerializationError(res_ct, data, e)
        else:
            supported_types = set(self.supported_mime_types)
            raise UnsupportedContentTypeError(res_ct, supported_types)

    def create_request(
        self,
        method,
        path,
        headers,
        data,
        host=None,
        port=None,
        proto='http',
        http_version=None,
        path_vars={},
        query_str='',
        start_time=None
    ):
        '''
        Attempt to create an httpglue.Request object
        where data is serialized into bytes and placed
        in the body attribute according to the specified
        Content-Type header in headers.

        utf-8 encoding is always expected.

        It will raise an exception if the request's
        content type is not specified or if that specific
        content type is not supported by the ContentHelper.

        :param str method: the http method of the request
           object getting created
        :param str path: the http path of the request
           object getting created
        :param headers: a dict or httpglue.Headers object of
           the request object getting created
        :param data: any concievable value that can be deserialized
           to bytes used as the body property of the request
           object getting created
        :param str host: the host of the request object
           getting created, if any
        :param int port: the port of the request object
           getting created, if any
        :param str proto: the proto of the request object
           getting created, if any
        :param str http_version: the http_version of the request object
           getting created, if any
        :param dict path_vars: the path_vars of the request object
           getting created, if any
        :param str query_str: the query_str of the request object
           getting created, if any
        :param datetime.datetime start_time: the start_time of the
           request object getting created, if any

        :raises UnsupportedContentTypeError: when the ContentHelper
           doesn't have any support for serializing the content
           type specified in headers, or when no content type is
           specified

        :raises ContentSerializationError: when an unexpected
           serialization error occurs

        :rtype: httpglue.Request
        '''
        directives = self._parse_directives(
            headers.get('Content-Type')
        )

        req_ct = directives.get('mime_type', '')

        if req_ct in self.supported_mime_types.keys():
            try:
                body = self.supported_mime_types[req_ct]['serializer'](
                    data,
                    directives['charset'],
                    directives['boundry']
                )
                return Request(
                    method,
                    path,
                    headers,
                    body,
                    host=host,
                    port=port,
                    proto=proto,
                    http_version=http_version,
                    path_vars=path_vars,
                    query_str=query_str,
                    start_time=start_time
                )
            except Exception as e:
                raise ContentSerializationError(req_ct, data, e)
        else:
            supported_types = set(self.supported_mime_types)
            raise UnsupportedContentTypeError(req_ct, supported_types)

    def _parse_directives(self, content_type_header_val):
        directives = {
            'mime_type': None,
            'charset': None,
            'boundry': None
        }

        if content_type_header_val is None:
            return directives

        # extract the ; separated parts
        parts = [
            d.lstrip()
            for d in content_type_header_val.split(';')
        ]

        directives['mime_type'] = parts[0]

        directives.update({
            part.split('=')[0]: part.split('=')[-1]
            for part in parts[1:]
        })

        return directives


def json_serializer(data, charset, boundry):
    charset = charset if charset is not None else 'utf-8'
    return json.dumps(data).encode(charset)


def json_deserializer(serialized_data, charset, boundry):
    charset = charset if charset is not None else 'utf-8'
    return json.loads(serialized_data.decode(charset))
