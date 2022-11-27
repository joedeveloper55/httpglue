from httpglue import Response


class UnsupportedContentTypeError(Exception):
    def __init__(self, mime_type, supported_types):
        self.req_ct_type = mime_type
        self.supported_content_types = supported_types


class ContentHelper:
    def __init__(self):
        self.supported_mime_types = {}

    def add_support(self, mime_type, serializer, deserializer):
        self.supported_mime_types[mime_type] = {
            'serializer': serializer,
            'deserializer': deserializer
        }

    def accept(self, mime_types, request):
        req_ct = request.headers.get('Content-Type')
        if req_ct in mime_types and req_ct in self.supported_mime_types.keys():
            try:
                return self.supported_mime_types[req_ct]['deserializer'](
                    request.body)
            except Exception:
                pass
        else:
            supported_types = set(mime_types) & set(self.supported_mime_types)
            raise UnsupportedContentTypeError(req_ct, supported_types)

    def make_response(
        self,
        status,
        headers,
        data,
        reason=''
    ):  # x is all the Request properties with body replaced by data
        req_ct = headers.get('Content-Type')
        if req_ct in self.supported_mime_types.keys():
            try:
                body = self.supported_mime_types[req_ct]['serializer'](
                    data)
                return Response(
                    status,
                    headers,
                    body,
                    reason
                )
            except Exception:
                raise ValueError('seriliazationError')
        else:
            supported_types = set(self.supported_mime_types)
            raise ValueError('can\'t serialize unknown type')