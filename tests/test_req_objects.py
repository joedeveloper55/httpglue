# Copyright 2021, Joseph P McAnulty
import datetime
import unittest

from httpglue import Request, Headers


class TestRequestInstantiation(unittest.TestCase):
    def test_successful_instantiation(self):
        start_time = datetime.datetime.now()

        req = Request(
            method='GET',
            path='/something',
            headers=Headers(),
            body=b'',
            host='localhost',
            port=80,
            proto='http',
            http_version='1.1',
            path_vars={},
            query_str='some_key=some_val',
            start_time=start_time
        )

        self.assertEqual(req.method, 'GET')
        self.assertEqual(req.path, '/something')
        self.assertEqual(req.headers, Headers())
        self.assertEqual(req.body, b'')
        self.assertEqual(req.host, 'localhost')
        self.assertEqual(req.port, 80)
        self.assertEqual(req.proto, 'http')
        self.assertEqual(req.http_version, '1.1')
        self.assertEqual(req.path_vars, {})
        self.assertEqual(req.query_str, 'some_key=some_val')
        self.assertEqual(req.start_time, start_time)

    def test_successful_instantiation_with_implicit_headers_coercion(self):
        start_time = datetime.datetime.now()

        req = Request(
            method='GET',
            path='/something',
            headers={},
            body=b'',
            host='localhost',
            port=80,
            proto='http',
            http_version='1.1',
            path_vars={},
            query_str='some_key=some_val',
            start_time=start_time
        )

        self.assertEqual(req.method, 'GET')
        self.assertEqual(req.path, '/something')
        self.assertEqual(req.headers, Headers())
        self.assertEqual(req.body, b'')
        self.assertEqual(req.host, 'localhost')
        self.assertEqual(req.port, 80)
        self.assertEqual(req.proto, 'http')
        self.assertEqual(req.http_version, '1.1')
        self.assertEqual(req.path_vars, {})
        self.assertEqual(req.query_str, 'some_key=some_val')
        self.assertEqual(req.start_time, start_time)

    def test_successful_instantiation_with_ommitted_optionals(self):
        req = Request(
            method='GET',
            path='/something',
            headers=Headers(),
            body=b'')

        self.assertEqual(req.method, 'GET')
        self.assertEqual(req.path, '/something')
        self.assertEqual(req.headers, Headers())
        self.assertEqual(req.body, b'')
        self.assertEqual(req.host, None)
        self.assertEqual(req.port, None)
        self.assertEqual(req.proto, 'http')
        self.assertEqual(req.http_version, None)
        self.assertEqual(req.path_vars, {})
        self.assertEqual(req.query_str, '')
        self.assertEqual(req.start_time, None)

    def test_failed_instantiation_due_to_bad_method_arg(self):
        start_time = datetime.datetime.now()

        with self.assertRaises(TypeError):
            req = Request(
                method=5,
                path='/something',
                headers=Headers(),
                body=b'',
                host='localhost',
                port=80,
                proto='http',
                http_version='1.1',
                path_vars={},
                query_str='some_key=some_val',
                start_time=start_time
            )

        with self.assertRaises(ValueError):
            req = Request(
                method='',  # empty str
                path='/something',
                headers=Headers(),
                body=b'',
                host='localhost',
                port=80,
                proto='http',
                http_version='1.1',
                path_vars={},
                query_str='some_key=some_val',
                start_time=start_time
            )

        with self.assertRaises(ValueError):
            req = Request(
                method='\r\n',  # bad chars
                path='/something',
                headers=Headers(),
                body=b'',
                host='localhost',
                port=80,
                proto='http',
                http_version='1.1',
                path_vars={},
                query_str='some_key=some_val',
                start_time=start_time
            )

    def test_failed_instantiation_due_to_bad_path_arg(self):
        start_time = datetime.datetime.now()

        with self.assertRaises(TypeError):
            req = Request(
                method='GET',
                path=None,
                headers=Headers(),
                body=b'',
                host='localhost',
                port=80,
                proto='http',
                http_version='1.1',
                path_vars={},
                query_str='some_key=some_val',
                start_time=start_time
            )

        with self.assertRaises(ValueError):
            req = Request(
                method='GET',
                path='/x?y=z',
                headers=Headers(),
                body=b'',
                host='localhost',
                port=80,
                proto='http',
                http_version='1.1',
                path_vars={},
                query_str='some_key=some_val',
                start_time=start_time
            )

    def test_failed_instantiation_due_to_bad_headers_arg(self):
        start_time = datetime.datetime.now()

        with self.assertRaises(TypeError):
            req = Request(
                method='GET',
                path='/something',
                headers=1,
                body=b'',
                host='localhost',
                port=80,
                proto='http',
                http_version='1.1',
                path_vars={},
                query_str='some_key=some_val',
                start_time=start_time
            )

        with self.assertRaises(TypeError):
            req = Request(
                method='GET',
                path='/something',
                headers={1: None},
                body=b'',
                host='localhost',
                port=80,
                proto='http',
                http_version='1.1',
                path_vars={},
                query_str='some_key=some_val',
                start_time=start_time
            )

        with self.assertRaises(ValueError):
            req = Request(
                method='GET',
                path='/something',
                headers={'Bad-Header': 'Bad Chars \n\t'},
                body=b'',
                host='localhost',
                port=80,
                proto='http',
                http_version='1.1',
                path_vars={},
                query_str='some_key=some_val',
                start_time=start_time
            )

    def test_failed_instantiation_due_to_bad_body_arg(self):
        start_time = datetime.datetime.now()

        with self.assertRaises(TypeError):
            req = Request(
                method='GET',
                path='/something',
                headers=Headers(),
                body=None,
                host='localhost',
                port=80,
                proto='http',
                http_version='1.1',
                path_vars={},
                query_str='some_key=some_val',
                start_time=start_time
            )

    def test_failed_instantiation_due_to_bad_host_arg(self):
        start_time = datetime.datetime.now()

        with self.assertRaises(TypeError):
            req = Request(
                method='GET',
                path='/something',
                headers=Headers(),
                body=b'',
                host=5,
                port=80,
                proto='http',
                http_version='1.1',
                path_vars={},
                query_str='some_key=some_val',
                start_time=start_time
            )

    def test_failed_instantiation_due_to_bad_port_arg(self):
        start_time = datetime.datetime.now()

        with self.assertRaises(TypeError):
            req = Request(
                method='GET',
                path='/something',
                headers=Headers(),
                body=b'',
                host='localhost',
                port='some_str',
                proto='http',
                http_version='1.1',
                path_vars={},
                query_str='some_key=some_val',
                start_time=start_time
            )

    def test_failed_instantiation_due_to_bad_proto_arg(self):
        start_time = datetime.datetime.now()

        with self.assertRaises(TypeError):
            req = Request(
                method='GET',
                path='/something',
                headers=Headers(),
                body=b'',
                host='localhost',
                port=80,
                proto=True,
                http_version='1.1',
                path_vars={},
                query_str='some_key=some_val',
                start_time=start_time
            )

    def test_failed_instantiation_due_to_bad_http_version_arg(self):
        start_time = datetime.datetime.now()

        with self.assertRaises(TypeError):
            req = Request(
                method='GET',
                path='/something',
                headers=Headers(),
                body=b'',
                host='localhost',
                port=80,
                proto='http',
                http_version=5,
                path_vars={},
                query_str='some_key=some_val',
                start_time=start_time
            )

    def test_failed_instantiation_due_to_bad_path_vars_arg(self):
        start_time = datetime.datetime.now()

        with self.assertRaises(TypeError):
            req = Request(
                method='GET',
                path='/something',
                headers=Headers(),
                body=b'',
                host='localhost',
                port=80,
                proto='http',
                http_version='1.1',
                path_vars='BAD',
                query_str='some_key=some_val',
                start_time=start_time
            )

    def test_failed_instantiation_due_to_bad_query_str_arg(self):
        start_time = datetime.datetime.now()

        with self.assertRaises(TypeError):
            req = Request(
                method='GET',
                path='/something',
                headers=Headers(),
                body=b'',
                host='localhost',
                port=80,
                proto='http',
                http_version='1.1',
                path_vars={},
                query_str=5,
                start_time=start_time
            )

        with self.assertRaises(ValueError):
            req = Request(
                method='GET',
                path='/something',
                headers=Headers(),
                body=b'',
                host='localhost',
                port=80,
                proto='http',
                http_version='1.1',
                path_vars={},
                query_str='?some_key=some_val',
                start_time=start_time
            )

    def test_failed_instantiation_due_to_bad_start_time_arg(self):
        with self.assertRaises(TypeError):
            req = Request(
                method='GET',
                path='/something',
                headers=Headers(),
                body=b'',
                host='localhost',
                port=80,
                proto='http',
                http_version='1.1',
                path_vars={},
                query_str='some_key=some_val',
                start_time='Tuesday'
            )


class TestRequestMutation(unittest.TestCase):
    def setUp(self):
        self.start_time = datetime.datetime.now()

        self.req = Request(
            method='GET',
            path='/something',
            headers=Headers(),
            body=b'',
            host='localhost',
            port=80,
            proto='http',
            http_version='1.1',
            path_vars={},
            query_str='some_key=some_val',
            start_time=self.start_time
        )

    def test_succesfuly_mutating_request_method(self):
        self.req.method = 'POST'

        self.assertEqual(self.req.method, 'POST')
        self.assertEqual(self.req.path, '/something')
        self.assertEqual(self.req.headers, Headers())
        self.assertEqual(self.req.body, b'')
        self.assertEqual(self.req.host, 'localhost')
        self.assertEqual(self.req.port, 80)
        self.assertEqual(self.req.proto, 'http')
        self.assertEqual(self.req.http_version, '1.1')
        self.assertEqual(self.req.path_vars, {})
        self.assertEqual(self.req.query_str, 'some_key=some_val')
        self.assertEqual(self.req.start_time, self.start_time)

    def test_failed_mutating_of_request_method_due_to_bad_value(self):
        with self.assertRaises(TypeError):
            self.req.method = 1

        with self.assertRaises(ValueError):
            self.req.method = '\t\n'

    def test_that_deleting_method_attr_fails(self):
        with self.assertRaises(AttributeError):
            del self.req.method

    def test_succesfuly_mutating_request_path(self):
        self.req.path = '/something_else'

        self.assertEqual(self.req.method, 'GET')
        self.assertEqual(self.req.path, '/something_else')
        self.assertEqual(self.req.headers, Headers())
        self.assertEqual(self.req.body, b'')
        self.assertEqual(self.req.host, 'localhost')
        self.assertEqual(self.req.port, 80)
        self.assertEqual(self.req.proto, 'http')
        self.assertEqual(self.req.http_version, '1.1')
        self.assertEqual(self.req.path_vars, {})
        self.assertEqual(self.req.query_str, 'some_key=some_val')
        self.assertEqual(self.req.start_time, self.start_time)

    def test_failed_mutating_of_request_path_due_to_bad_value(self):
        with self.assertRaises(TypeError):
            self.req.path = 1

        with self.assertRaises(ValueError):
            self.req.path = 'something?q=1'

    def test_that_deleting_path_attr_fails(self):
        with self.assertRaises(AttributeError):
            del self.req.path

    def test_succesfuly_mutating_request_headers(self):
        self.req.headers = Headers({'Some-Header': 'x'})

        self.assertEqual(self.req.method, 'GET')
        self.assertEqual(self.req.path, '/something')
        self.assertEqual(self.req.headers, Headers({'Some-Header': 'x'}))  # noqa
        self.assertEqual(self.req.body, b'')
        self.assertEqual(self.req.host, 'localhost')
        self.assertEqual(self.req.port, 80)
        self.assertEqual(self.req.proto, 'http')
        self.assertEqual(self.req.http_version, '1.1')
        self.assertEqual(self.req.path_vars, {})
        self.assertEqual(self.req.query_str, 'some_key=some_val')
        self.assertEqual(self.req.start_time, self.start_time)

    def test_failed_mutating_of_request_headers_due_to_bad_value(self):
        with self.assertRaises(TypeError):
            self.req.headers = 1

    def test_that_deleting_headers_attr_fails(self):
        with self.assertRaises(AttributeError):
            del self.req.headers

    def test_succesfuly_mutating_request_body(self):
        self.req.body = b'content'

        self.assertEqual(self.req.method, 'GET')
        self.assertEqual(self.req.path, '/something')
        self.assertEqual(self.req.headers, Headers())
        self.assertEqual(self.req.body, b'content')
        self.assertEqual(self.req.host, 'localhost')
        self.assertEqual(self.req.port, 80)
        self.assertEqual(self.req.proto, 'http')
        self.assertEqual(self.req.http_version, '1.1')
        self.assertEqual(self.req.path_vars, {})
        self.assertEqual(self.req.query_str, 'some_key=some_val')
        self.assertEqual(self.req.start_time, self.start_time)

    def test_failed_mutating_of_request_body_due_to_bad_value(self):
        with self.assertRaises(TypeError):
            self.req.body = 1

    def test_that_deleting_body_attr_fails(self):
        with self.assertRaises(AttributeError):
            del self.req.body

    def test_succesfuly_mutating_request_host(self):
        self.req.host = 'example.com'

        self.assertEqual(self.req.method, 'GET')
        self.assertEqual(self.req.path, '/something')
        self.assertEqual(self.req.headers, Headers())
        self.assertEqual(self.req.body, b'')
        self.assertEqual(self.req.host, 'example.com')
        self.assertEqual(self.req.port, 80)
        self.assertEqual(self.req.proto, 'http')
        self.assertEqual(self.req.http_version, '1.1')
        self.assertEqual(self.req.path_vars, {})
        self.assertEqual(self.req.query_str, 'some_key=some_val')
        self.assertEqual(self.req.start_time, self.start_time)

    def test_failed_mutating_of_request_host_due_to_bad_value(self):
        with self.assertRaises(TypeError):
            self.req.host = 1

    def test_that_deleting_host_attr_fails(self):
        with self.assertRaises(AttributeError):
            del self.req.host

    def test_succesfuly_mutating_request_port(self):
        self.req.port = 8080

        self.assertEqual(self.req.method, 'GET')
        self.assertEqual(self.req.path, '/something')
        self.assertEqual(self.req.headers, Headers())
        self.assertEqual(self.req.body, b'')
        self.assertEqual(self.req.host, 'localhost')
        self.assertEqual(self.req.port, 8080)
        self.assertEqual(self.req.proto, 'http')
        self.assertEqual(self.req.http_version, '1.1')
        self.assertEqual(self.req.path_vars, {})
        self.assertEqual(self.req.query_str, 'some_key=some_val')
        self.assertEqual(self.req.start_time, self.start_time)

    def test_failed_mutating_of_request_port_due_to_bad_value(self):
        with self.assertRaises(TypeError):
            self.req.port = '8080'

    def test_that_deleting_port_attr_fails(self):
        with self.assertRaises(AttributeError):
            del self.req.port

    def test_succesfuly_mutating_request_proto(self):
        self.req.proto = 'https'

        self.assertEqual(self.req.method, 'GET')
        self.assertEqual(self.req.path, '/something')
        self.assertEqual(self.req.headers, Headers())
        self.assertEqual(self.req.body, b'')
        self.assertEqual(self.req.host, 'localhost')
        self.assertEqual(self.req.port, 80)
        self.assertEqual(self.req.proto, 'https')
        self.assertEqual(self.req.http_version, '1.1')
        self.assertEqual(self.req.path_vars, {})
        self.assertEqual(self.req.query_str, 'some_key=some_val')
        self.assertEqual(self.req.start_time, self.start_time)

    def test_failed_mutating_of_request_proto_due_to_bad_value(self):
        with self.assertRaises(TypeError):
            self.req.proto = 1

    def test_that_deleting_proto_attr_fails(self):
        with self.assertRaises(AttributeError):
            del self.req.proto

    def test_succesfuly_mutating_request_http_version(self):
        self.req.http_version = '2'

        self.assertEqual(self.req.method, 'GET')
        self.assertEqual(self.req.path, '/something')
        self.assertEqual(self.req.headers, Headers())
        self.assertEqual(self.req.body, b'')
        self.assertEqual(self.req.host, 'localhost')
        self.assertEqual(self.req.port, 80)
        self.assertEqual(self.req.proto, 'http')
        self.assertEqual(self.req.http_version, '2')
        self.assertEqual(self.req.path_vars, {})
        self.assertEqual(self.req.query_str, 'some_key=some_val')
        self.assertEqual(self.req.start_time, self.start_time)

    def test_failed_mutating_of_request_http_version_due_to_bad_value(self):
        with self.assertRaises(TypeError):
            self.req.http_version = 1

    def test_that_deleting_http_version_attr_fails(self):
        with self.assertRaises(AttributeError):
            del self.req.http_version

    def test_succesfuly_mutating_request_path_vars(self):
        self.req.path_vars = {'x': '123'}

        self.assertEqual(self.req.method, 'GET')
        self.assertEqual(self.req.path, '/something')
        self.assertEqual(self.req.headers, Headers())
        self.assertEqual(self.req.body, b'')
        self.assertEqual(self.req.host, 'localhost')
        self.assertEqual(self.req.port, 80)
        self.assertEqual(self.req.proto, 'http')
        self.assertEqual(self.req.http_version, '1.1')
        self.assertEqual(self.req.path_vars, {'x': '123'})
        self.assertEqual(self.req.query_str, 'some_key=some_val')
        self.assertEqual(self.req.start_time, self.start_time)

    def test_failed_mutating_of_request_path_vars_due_to_bad_value(self):
        with self.assertRaises(TypeError):
            self.req.path_vars = ''

    def test_that_deleting_path_vars_attr_fails(self):
        with self.assertRaises(AttributeError):
            del self.req.path_vars

    def test_succesfuly_mutating_request_query_str(self):
        self.req.query_str = ''

        self.assertEqual(self.req.method, 'GET')
        self.assertEqual(self.req.path, '/something')
        self.assertEqual(self.req.headers, Headers())
        self.assertEqual(self.req.body, b'')
        self.assertEqual(self.req.host, 'localhost')
        self.assertEqual(self.req.port, 80)
        self.assertEqual(self.req.proto, 'http')
        self.assertEqual(self.req.http_version, '1.1')
        self.assertEqual(self.req.path_vars, {})
        self.assertEqual(self.req.query_str, '')
        self.assertEqual(self.req.start_time, self.start_time)

    def test_failed_mutating_of_request_query_str_due_to_bad_value(self):
        with self.assertRaises(TypeError):
            self.req.query_str = 1

        with self.assertRaises(ValueError):
            self.req.query_str = '?bad=true'

    def test_that_deleting_query_str_attr_fails(self):
        with self.assertRaises(AttributeError):
            del self.req.query_str

    def test_succesfuly_mutating_request_start_time(self):
        new_start_time = datetime.datetime.now()
        self.req.start_time = new_start_time

        self.assertEqual(self.req.method, 'GET')
        self.assertEqual(self.req.path, '/something')
        self.assertEqual(self.req.headers, Headers())
        self.assertEqual(self.req.body, b'')
        self.assertEqual(self.req.host, 'localhost')
        self.assertEqual(self.req.port, 80)
        self.assertEqual(self.req.proto, 'http')
        self.assertEqual(self.req.http_version, '1.1')
        self.assertEqual(self.req.path_vars, {})
        self.assertEqual(self.req.query_str, 'some_key=some_val')
        self.assertEqual(self.req.start_time, new_start_time)

    def test_failed_mutating_of_request_start_time_due_to_bad_value(self):
        with self.assertRaises(TypeError):
            self.req.start_time = 0

    def test_that_deleting_start_time_attr_fails(self):
        with self.assertRaises(AttributeError):
            del self.req.start_time      

    def test_response_str(self):
        self.assertEqual(
            str(self.req),
            "GET /something?some_key=some_val 1.1\r\n\r\n\r\nb''")

    def test_request_repr(self):
        self.maxDiff = None
        self.assertIn(
            "Request(method='GET', path='/something', headers=Headers({}), body=b'', host='localhost', port=80, proto='http', http_version='1.1', path_vars={}, query_str='some_key=some_val',",  # noqa
            repr(self.req)
        )
    def test_request_repr_valid_python(self):
        # repr should print valid python if possible,
        # such that if it is fed into an interpreter it
        # produces an equivalent value
        serialized_then_deserialized_req = eval(repr(self.req))  # noqa

        self.assertEqual(
            self.req.method,
            serialized_then_deserialized_req.method)
        self.assertEqual(
            self.req.path,
            serialized_then_deserialized_req.path)
        self.assertEqual(
            self.req.headers,
            serialized_then_deserialized_req.headers)
        self.assertEqual(
            self.req.body,
            serialized_then_deserialized_req.body)
        self.assertEqual(
            self.req.host,
            serialized_then_deserialized_req.host)
        self.assertEqual(
            self.req.port,
            serialized_then_deserialized_req.port)
        self.assertEqual(
            self.req.proto,
            serialized_then_deserialized_req.proto)
        self.assertEqual(
            self.req.http_version,
            serialized_then_deserialized_req.http_version)
        self.assertEqual(
            self.req.path_vars,
            serialized_then_deserialized_req.path_vars)
        self.assertEqual(
            self.req.query_str,
            serialized_then_deserialized_req.query_str)
        self.assertEqual(
            self.req.start_time,
            serialized_then_deserialized_req.start_time)