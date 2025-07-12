# Copyright 2021, Joseph P McAnulty
import unittest

from httpglue import Response, Headers


class TestResponseInstantiation(unittest.TestCase):
    def test_successful_instantiation(self):
        res = Response(
            status=200,
            reason='OK',
            headers=Headers(),
            body=b'some text'
        )
        
        self.assertEqual(res.status, 200)
        self.assertEqual(res.reason, 'OK')
        self.assertEqual(res.headers, Headers())
        self.assertEqual(res.body, b'some text')

    def test_successful_instantiation_with_implicit_headers_coercion(self):
        res = Response(
            status=200,
            reason='OK',
            headers={},
            body=b'some text'
        )
        
        self.assertEqual(res.status, 200)
        self.assertEqual(res.reason, 'OK')
        self.assertEqual(res.headers, Headers())
        self.assertEqual(res.body, b'some text')

    def test_successful_instantiation_with_ommited_reason(self):
        res = Response(
            status=200,
            headers={},
            body=b'some text'
        )
        
        self.assertEqual(res.status, 200)
        self.assertEqual(res.reason, '')
        self.assertEqual(res.headers, Headers())
        self.assertEqual(res.body, b'some text')

    def test_failed_instantiation_due_to_bad_status_arg(self):
        with self.assertRaises(TypeError):
            Response('200', {}, b'', 'OK')

        with self.assertRaises(ValueError):
            Response(700, {}, b'', 'SOMETHING')

        with self.assertRaises(ValueError):
            Response(99, {}, b'', 'SOMETHING')

    def test_failed_instantiation_due_to_bad_reason_arg(self):
        with self.assertRaises(TypeError):
            Response(200, {}, b'', 1)

        with self.assertRaises(ValueError):
            Response(200, {}, b'', 'Bad Chars \n\t')

    def test_failed_instantiation_due_to_bad_headers_arg(self):
        with self.assertRaises(TypeError):
            Response(200, 1, b'', 'OK',)

        with self.assertRaises(TypeError):
            Response(200, {1: None}, b'', 'OK')

        with self.assertRaises(ValueError):
            Response(200, {'Bad-Header': 'Bad Chars \n\t'}, b'', 'OK')

    def test_failed_instantiation_due_to_bad_body_arg(self):
        with self.assertRaises(TypeError):
            Response(200, {}, None, 'OK')


class TestResponseMutation(unittest.TestCase):
    def setUp(self):
        self.res = res = Response(200, {}, b'some text', 'OK')

    def test_succesfuly_mutating_response_status(self):
        self.res.status = 404

        self.assertEqual(self.res.status, 404)
        self.assertEqual(self.res.reason, 'OK')
        self.assertEqual(self.res.headers, Headers())
        self.assertEqual(self.res.body, b'some text')

    def test_failed_mutating_of_response_status_due_to_bad_value(self):
        with self.assertRaises(TypeError):
            self.res.status = '200'

        with self.assertRaises(ValueError):
            self.res.status = 700

    def test_that_deleting_status_attr_fails(self):
        with self.assertRaises(AttributeError):
            del self.res.status

    def test_succesfuly_mutating_response_reason(self):
        self.res.reason = 'FEELINFINE'

        self.assertEqual(self.res.status, 200)
        self.assertEqual(self.res.reason, 'FEELINFINE')
        self.assertEqual(self.res.headers, Headers())
        self.assertEqual(self.res.body, b'some text')

    def test_failed_mutating_of_response_reason_due_to_bad_value(self):
        with self.assertRaises(TypeError):
            self.res.reason = 1

        with self.assertRaises(ValueError):
            # bad chars and form
            self.res.reason = '  \t\n'

    def test_that_deleting_reason_attr_fails(self):
        with self.assertRaises(AttributeError):
            del self.res.reason

    def test_succesfuly_mutating_response_headers(self):
        self.res.headers = {'Content-Type': 'text/plain'}

        self.assertEqual(self.res.status, 200)
        self.assertEqual(self.res.reason, 'OK')
        self.assertEqual(self.res.headers,
            Headers({'Content-Type': 'text/plain'}))
        self.assertEqual(self.res.body, b'some text')

    def test_failed_mutating_of_response_headers_due_to_bad_value(self):
        with self.assertRaises(TypeError):
            self.res.headers = None

        with self.assertRaises(TypeError):
            self.res.headers[5] = ''

        with self.assertRaises(TypeError):
            self.res.headers['Content-Type'] = 1

        with self.assertRaises(ValueError):
            # bad chars and form
            self.res.headers['  \t\n'] = '  \t\n'

    def test_that_deleting_headers_attr_fails(self):
        with self.assertRaises(AttributeError):
            del self.res.headers

    def test_succesfuly_mutating_response_body(self):
        self.res.body = b'some other text'

        self.assertEqual(self.res.status, 200)
        self.assertEqual(self.res.reason, 'OK')
        self.assertEqual(self.res.headers, Headers())
        self.assertEqual(self.res.body, b'some other text')

    def test_failed_mutating_of_response_body_due_to_bad_value(self):
        with self.assertRaises(TypeError):
            # body must always be bytes
            self.res.body = {'data': 1}

    def test_that_deleting_body_attr_fails(self):
        with self.assertRaises(AttributeError):
            del self.res.body

    def test_response_str(self):
        self.assertEqual(
            str(self.res),
            "HTTP 200 OK\r\n\r\n\r\nb'some text'")

    def test_response_repr(self):
        self.assertEqual(
            repr(self.res),
            "Response(status=200, headers=Headers({}), body=b'some text', reason='OK')")  # noqa

    def test_response_repr_valid_python(self):
        # repr should print valid python if possible,
        # such that if it is fed into an interpreter it
        # produces an equivalent value. we use 'eval'
        # here, but if you're looking at this test thinking
        # you might want to do this in your app code, dont. :)
        # eval is evil.
        serialized_then_deserialized_res = eval(repr(self.res))  # noqa

        self.assertEqual(
            self.res.status,
            serialized_then_deserialized_res.status)
        self.assertEqual(
            self.res.reason,
            serialized_then_deserialized_res.reason)
        self.assertEqual(
            self.res.headers,
            serialized_then_deserialized_res.headers)
        self.assertEqual(
            self.res.body,
            serialized_then_deserialized_res.body)
