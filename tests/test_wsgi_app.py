# Copyright 2021, Joseph P McAnulty

import datetime
import io
import logging
import unittest
from unittest import mock

from httpglue import Req
from httpglue import Res
from httpglue.wsgi import App


class TestBasicAppInstantiation(unittest.TestCase):
    
    def test_successful_instantiation_of_app(self):
        app = App(
            logger=logging.getLogger('simple_example'),
            default_fallback_err_res=Res(
                status=500,
                headers={},
                body=b''
            )
        )

        self.assertEqual(type(app), App)

    def test_instatiation_fails_with_missing_parameters(self):
        with self.assertRaises(TypeError):
            app = App()

    def test_instantiation_fails_with_bad_param_types(self):
        with self.assertRaises(TypeError):
            App(
                logger=logging.getLogger('simple_example'),
                default_fallback_err_res=500
            )

        with self.assertRaises(TypeError):
            App(
                logger=None,
                default_fallback_err_res=Res(
                    status=500,
                    headers={},
                    body=b''
                )
            )

        with self.assertRaises(TypeError):
            App(
                logger=None,
                default_fallback_err_res=500
            )

    def test_instantiation_fails_due_to_bad_default_err_res(self):
        # wsgi itself (not the http spec) enforces some special
        # rules with regards to header values. The main rule
        # is that header values must not contain control characters.
        # Since the default_fallback_err_res must always be
        # able to be sent without error, we must ensure this here
        with self.assertRaises(ValueError):
            App(
                logger=logging.getLogger('simple_example'),
                default_fallback_err_res=Res(
                    status=500,
                    headers={
                        'X-Bad-Header': '\tbad\b\0'
                    },
                    body=b''
                )
            )   


class TestAppEndpointAndErrHandlerRegistry(unittest.TestCase):

    def setUp(self):
        dummy_logger = logging.getLogger('dummy')
        dummy_logger.addHandler(logging.NullHandler())
        
        def dummy_req_handler(req):
            return Res(200, {}, b'')

        def dummy_pred(req):
            return True 

        def dummy_err_handler(exc, req):
            return Res(500, {}, b'')

        self.dummy_req_handler = dummy_req_handler
        self.dummy_pred = dummy_pred
        self.dummy_err_handler = dummy_err_handler

        self.app = App(
            logger=dummy_logger,
            default_fallback_err_res=Res(
                status=500,
                headers={},
                body=b''
            )
        )

    def test_valid_endpoint_registry(self):
        self.app.register_endpoint(
            {'GET'},
            '/dummy_path',
            self.dummy_req_handler
        )

    def test_valid_endpoint_registry_with_decorator(self):        
        @self.app.endpoint({'POST', 'PUT'}, '/dummy_path')
        def dummy_req_handler(req):
            return Res(200, {}, b'') 

    def test_valid_endpoint_registry_with_pred(self):        
        self.app.register_endpoint(
            {'GET'},
            '/dummy_path',
            self.dummy_req_handler,
            pred=self.dummy_pred
        )

    def test_endpoint_registry_fails_with_bad_method_spec(self):
        with self.assertRaises(TypeError): 
            self.app.register_endpoint(
                'GET',  # not a set, must be a set
                '/dummy_path',
                self.dummy_req_handler
            )

        with self.assertRaises(TypeError):
            # set contains non string characters
            self.app.register_endpoint(
                {'GET', 200, None},
                '/dummy_path',
                self.dummy_req_handler
            )

    def test_endpoint_registry_fails_with_bad_path_spec(self):
        with self.assertRaises(TypeError): 
            self.app.register_endpoint(
                {'GET'},
                None,  # not a str
                self.dummy_req_handler
            )

        with self.assertRaises(ValueError): 
            self.app.register_endpoint(
                {'GET'},
                '^/dummy_path',  # must not start with ^
                self.dummy_req_handler
            )

        with self.assertRaises(ValueError): 
            self.app.register_endpoint(
                {'GET'},
                '/dummy_path$',  # must not end with $
                self.dummy_req_handler
            )
        

    def test_endpoint_registry_fails_with_bad_req_handler(self):
        def dummy_req_handler_w_bad_signature(x, y, z=None):
            return Req(200, {}, b'')

        with self.assertRaises(ValueError): 
            self.app.register_endpoint(
                {'GET'},
                '/dummy_path',
                dummy_req_handler_w_bad_signature
            )

    def test_endpoint_registry_fails_with_bad_pred(self):
        def dummy_pred_w_bad_signature(x, y, z=None):
            return True
        
        with self.assertRaises(ValueError): 
            self.app.register_endpoint(
                {'GET'},
                '/dummy_path',
                self.dummy_req_handler,
                pred=dummy_pred_w_bad_signature
            )

    def test_valid_err_handler_registry(self):
        self.app.register_err_handler(
            [IndexError, KeyError],
            self.dummy_err_handler
        )

    def test_valid_err_handler_registry_with_decorator(self):
        @self.app.err_handler([Exception])
        def dummy_err_handler(exc, req):
            return Res(500, {}, b'')

    def test_err_handler_registry_fails_with_bad_excs_list(self):
        with self.assertRaises(TypeError):
            self.app.register_err_handler(
                Exception,  # non list type
                self.dummy_err_handler
            )

        with self.assertRaises(TypeError):
            self.app.register_err_handler(
                [IndexError, 'x'],  # non exception type in list
                self.dummy_err_handler
            )

    def test_err_handler_registry_fails_with_bad_handler(self):
        def dummy_err_handler_w_bad_signature(x, y, z=None):
            return Res(500, {}, b'')
        
        with self.assertRaises(ValueError):
            self.app.register_err_handler(
                [Exception],
                dummy_err_handler_w_bad_signature
            )

class TestAppRouting:
    pass  # TODO


class TestAppPathVarExtractionIntoReqObject(unittest.TestCase):
    def test_req_ojects_correctly_get_path_vars_populated(self):
        # define a simple app
        dummy_logger = logging.getLogger('dummy')
        dummy_logger.addHandler(logging.NullHandler())
        app = App(
            logger=dummy_logger,
            default_fallback_err_res=Res(
                status=500,
                headers={},
                body=b''
            )
        )
        
        processed_req_object = None
        def req_handler(req):
            nonlocal processed_req_object
            # get the processed Req object for
            # later inspection. This should have
            # the path_vars property correctly populated,
            # which we'll verify later
            processed_req_object = req
            # now jus return a dummy response
            return Res()

        app.register_endpoint(
            {'GET'},
            r'/(?P<id>\d*)/(.*)',
            req_handler
        )
        # send in a req to handle_req, and ignore the dummy resp
        app.handle_request(Req(
            method='GET',
            path='/12345/ejorivj0439g4',
            headers={},
            body=b''
        ))
        # the check the req object passed into our mock handler
        self.assertEqual(processed_req_object.path_vars, {
            0: '12345',
            1: 'ejorivj0439g4',
            'id':'12345'
        })

class TestAppWSGIMappingToReqObject(unittest.TestCase):
    def setUp(self):
        dummy_logger = logging.getLogger('dummy')
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        dummy_logger.addHandler(ch)
        # dummy_logger.addHandler(logging.NullHandler())

        self.app = App(
            logger=dummy_logger,
            default_fallback_err_res=Res(
                status=500,
                headers={},
                body=b''
            )
        )

        self.app.handle_request = mock.Mock()
        # make the mock just return a valid dummy value
        self.app.handle_request.return_value = Res(200, {}, b'')

    def test_appropriate_req_object_built_in_wsgi_entrypoint(self):
        environ = {
            'REQUEST_METHOD': 'GET',
            'PATH_INFO': '/dummy_path',
            'QUERY_STRING': '',
            'HTTP_X-Dummy-Header': 'dummy_content',
            'CONTENT_TYPE': 'text/plain',
            'CONTENT_LENGTH': 13,
            'wsgi.input': io.BytesIO(b'dummy content'),
            'SERVER_NAME': 'dummy_host',
            'SERVER_PORT': 8000,
            'wsgi.url_scheme': 'http',
            'SERVER_PROTOCOL': '1.1'
        }
        start_response = mock.Mock()
        
        res = self.app(environ, start_response)

        # inspect the framework generated Req object,
        # making sure it looks like we'd expect
        self.assertEqual(len(self.app.handle_request.call_args_list), 1)
        req = self.app.handle_request.call_args_list[0][0][0]

        self.assertEqual(req.method, 'GET')
        self.assertEqual(req.path, '/dummy_path')
        self.assertEqual(req.headers, {
            'Content-Length': 13,
            'Content-Type': 'text/plain',
            'X-Dummy-Header': 'dummy_content'
        })
        self.assertEqual(req.body, b'dummy content')
        self.assertEqual(req.query_str, '')
        self.assertEqual(req.host, 'dummy_host')
        self.assertEqual(req.port, 8000),
        self.assertEqual(req.proto, 'http')
        self.assertEqual(req.http_version, '1.1')
        self.assertEqual(type(req.start_time), datetime.datetime)

        # expect the dummy value to come through
        self.assertEqual(len(start_response.call_args_list), 1)
        start_response_args = start_response.call_args_list[0][0]
        self.assertEqual(
            start_response_args[0],
            str(self.app.handle_request.return_value.status) + ' ')
        self.assertEqual(
            start_response_args[1],
            list(self.app.handle_request.return_value.headers.items()))
        self.assertEqual(
            res[0],
            self.app.handle_request.return_value.body)

    def test_req_object_built_in_wsgi_entrypoint_minimal_req(self):
        # this test case is about passing the bare minumum of
        # stuff acceptable per te wsgi spec in environ 
        environ = {
            'REQUEST_METHOD': 'GET',
            'wsgi.input': io.BytesIO(b''),
            'SERVER_NAME': 'dummy_host',
            'SERVER_PORT': 8000,
            'wsgi.url_scheme': 'http',
        }
        start_response = mock.Mock()
        
        res = self.app(environ, start_response)

        # inspect the framework generated Req object,
        # making sure it looks like we'd expect
        self.assertEqual(len(self.app.handle_request.call_args_list), 1)
        req = self.app.handle_request.call_args_list[0][0][0]

        self.assertEqual(req.method, 'GET')
        self.assertEqual(req.path, '')
        self.assertEqual(req.headers, {})
        self.assertEqual(req.body, b'')
        self.assertEqual(req.query_str, '')
        self.assertEqual(req.host, 'dummy_host')
        self.assertEqual(req.port, 8000),
        self.assertEqual(req.proto, 'http')
        self.assertEqual(req.http_version, '')
        self.assertEqual(type(req.start_time), datetime.datetime)

        # expect the dummy value to come through
        self.assertEqual(len(start_response.call_args_list), 1)
        start_response_args = start_response.call_args_list[0][0]
        self.assertEqual(
            start_response_args[0],
            str(self.app.handle_request.return_value.status) + ' ')
        self.assertEqual(
            start_response_args[1],
            list(self.app.handle_request.return_value.headers.items()))
        self.assertEqual(
            res[0],
            self.app.handle_request.return_value.body)

    def test_default_fallback_err_res_returned_when_req_object_cant_be_made(self):
        # notice below that in environ we've omitted
        # REQUEST_METHOD, which is required as per the
        # wsgi spec, and should expect that something will
        # go wrong and that the default_fallback_err_res
        # is what will be returned 
        environ = {
            'wsgi.input': io.BytesIO(b''),
            'SERVER_NAME': 'dummy_host',
            'SERVER_PORT': 8000,
            'wsgi.url_scheme': 'http',
        }
        start_response = mock.Mock()
        
        res = self.app(environ, start_response)

        # inspect the framework generated Req object,
        # making sure it looks like we'd expect
        self.assertEqual(len(self.app.handle_request.call_args_list), 0)

        # expect the dummy value to come through
        self.assertEqual(len(start_response.call_args_list), 1)
        start_response_args = start_response.call_args_list[0][0]
        self.assertEqual(
            start_response_args[0],
            str(self.app.default_fallback_err_res.status) + ' ')
        self.assertEqual(
            start_response_args[1],
            list(self.app.default_fallback_err_res.headers.items()))
        self.assertEqual(
            res[0],
            self.app.default_fallback_err_res.body)

    def test_default_fallback_err_res_returned_when_res_object_cant_be_used(self):
        # make sure handle_req returns a Res object
        # with headers values that are not valid as
        # per the wsgi spec (header values with control
        # characters are illegal under wsgi)
        self.app.handle_request = mock.Mock()
        self.app.handle_request.return_value = Res(
            status=200,
            headers={
                'X-Dummy-Header': 'v\tn'
            },
            body=b'dummy content'
        )

        environ = {
            'REQUEST_METHOD': 'GET',
            'wsgi.input': io.BytesIO(b''),
            'SERVER_NAME': 'dummy_host',
            'SERVER_PORT': 8000,
            'wsgi.url_scheme': 'http',
        }
        start_response = mock.Mock()
        
        res = self.app(environ, start_response)

        # expect the dummy value to come through
        self.assertEqual(len(start_response.call_args_list), 1)
        start_response_args = start_response.call_args_list[0][0]
        self.assertEqual(
            start_response_args[0],
            str(self.app.default_fallback_err_res.status) + ' ')
        self.assertEqual(
            start_response_args[1],
            list(self.app.default_fallback_err_res.headers.items()))
        self.assertEqual(
            res[0],
            self.app.default_fallback_err_res.body)
