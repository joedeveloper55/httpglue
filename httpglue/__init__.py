# Copyright 2021, Joseph P McAnulty

import datetime


class Req:
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
                'method attribute of httpglue.Req object '
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
                'path attribute of httpglue.Req object '
                'must be of type str, got %s' % type(value)
            )
        if '?' in value:
            raise ValueError(
                '? was in the path: %s. This means you '
                'have a query string in here. Do not '
                'supply the query string here, supply it '
                'in the query_args property of the '
                'httpglue.Req object instead' % value
            )
        self._path = value

    @property
    def path_vars(self):
        return self._path_vars

    @path_vars.setter
    def path_vars(self, value):
        if type(value) is not dict:
            raise TypeError(
                'path_vars attribute of httpglue.Req object '
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
                'query_str attribute of httpglue.Req object '
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
                'headers attribute of httpglue.Res object '
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
                'body attribute of httpglue.Res object '
                'must be of type bytes, got %s' % type(value)
            )
        self._body = value

    @property
    def start_time(self):
        return self._start_time

    @start_time.setter
    def start_time(self, value):
        if type(value) not in (type(None), datetime.datetime) :
            raise TypeError(
                'start_time attribute of httpglue.Res object '
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
                'host attribute of httpglue.Res object '
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
                'port attribute of httpglue.Res object '
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
                'proto attribute of httpglue.Res object '
                'must be of type str or NoneType, got %s' % type(value)
            )
        self._proto = value
    
    @property
    def full_url(self):
        if None in (self.proto, self.host, self.port):
            raise ValueError()

        return f'{self.proto}://{self.host}:{self.port}{self.path}?{self.query_str}'

    def copy(self):
        return Req(
            method=self.method,
            path=self.path,
            headers=dict(self.headers),
            body=self.body,
            host=self.host,
            port=self.port,
            proto=self.proto,
            http_version=self.http_version,
            path_vars=dict(self.path_vars),
            query_str=self.query_str,
            start_time=self.start_time
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
        return f'Req({args_part})'

    def __str__(self):
        query_str_part = f'?{self.query_str}' if self.query_str else ''
        request_line_part = f'{self.method} {self.path}{query_str_part} {self.http_version}'
        headers_part = '\n'.join(
            f'{key}: {value}'
            for key, value in self.headers.items()
        )

        return f'{request_line_part}\n{headers_part}\n\n{self.body}'
        return super().__str__()


class Res:
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
                'status attribute of httpglue.Res object '
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
                'reason attribute of httpglue.Res object '
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
                'headers attribute of httpglue.Res object '
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
                'body attribute of httpglue.Res object '
                'must be of type bytes, got %s' % type(value)
            )
        self._body = value

    def copy(self):
        return Res(
            status=self.status,
            headers=self.headers_part,
            body=self.body,
            reason=self.reason
        )

    def deep_validate(self):
        raise NotImplementedError()

    def __repr__(self):
        args_part = ', '.join([
            f'status={repr(self.status)}',
            f'headers={repr(self.headers)}',
            f'body={repr(self.body)}',
            f'reason={repr(self.reason)}'
        ])
        return f'Res({args_part})'

    def __str__(self):
        status_part = f'HTTP {self.status} {self.reason}'
        headers_part = '\n'.join(
            f'{key}: {value}'
            for key, value in self.headers.items()
        )

        return f'{status_part}\n{headers_part}\n\n{self.body}'
