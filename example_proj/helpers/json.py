import json

from httpglue.wsgi import Req, Res


class JsonReq(Req):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # decoding could be more flexible based on request headers
        self.data = json.loads(self.body.decode('utf-8'))

    @classmethod
    def from_req(cls, req):
        return cls(
            method=req.method,
            path=req.path,
            headers=req.headers,
            body=req.body,
            path_vars=req.path_vars
        )


class JsonRes(Res):
    @classmethod
    def from_data(cls, status, headers, data):
        body = json.dumps(data).encode('utf-8')
        
        headers = {
            'Content-Type': 'application/json; utf-8',
            'Content-Length': str(len(body)),
            **headers
        }

        return cls(
            status=status,
            headers=headers,
            body=body
        )


def WithJsonReq(f):
    def augmented_f(req):
        req = JsonReq.from_req(req)
        return f(req)
    return augmented_f