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

    def deserialize_body(self, mime_types, request):
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
        req_ct = request.headers.get('Content-Type')
        if req_ct in mime_types and req_ct in self.supported_mime_types.keys():
            try:
                return self.supported_mime_types[req_ct]['deserializer'](
                    request.body)
            except Exception as e:
                raise ContentDeserializationError(req_ct, request.body, e)
        else:
            supported_types = set(mime_types) & set(self.supported_mime_types)
            raise UnsupportedContentTypeError(req_ct, supported_types)

    def create_response(
        self,
        status,
        headers,
        data,
        reason=''
    ):
        res_ct = headers.get('Content-Type')
        if res_ct in self.supported_mime_types.keys():
            try:
                body = self.supported_mime_types[res_ct]['serializer'](
                    data)
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
        req_ct = headers.get('Content-Type')
        if req_ct in self.supported_mime_types.keys():
            try:
                body = self.supported_mime_types[req_ct]['serializer'](
                    data)
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
