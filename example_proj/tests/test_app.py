import base64
import json

import unittest
from unittest import mock

from httpglue import Request

import app
from helpers import auth
from tests import fakes

class BaseTestCase(unittest.TestCase):

    DUMMY_BASIC_CREDS = base64.b64encode(
        'dummy:dummy'.encode('utf-8')).decode('ascii')

    @classmethod
    def setUpClass(cls):
        cls.conn_pool_patcher = mock.patch(
            'psycopg_pool.ConnectionPool',
        )
        cls.conn_pool_patcher.start()

        cls.widget_store_patcher = mock.patch.object(
            app.dal,
            'WidgetStore',
            new=fakes.FakeWidgetStore)
        cls.widget_store_patcher.start()

        cls.fake_auth_provider = fakes.FakeAuthProvider
        cls.auth_provider_patcher = mock.patch(
            'helpers.auth.DBUserPassCredsAuthProvider',
            new=cls.fake_auth_provider
        )
        cls.auth_provider_patcher.start()

        cls.app = app.make_app()

    @classmethod
    def tearDownClass(cls):
        cls.widget_store_patcher.stop()
        cls.auth_provider_patcher.stop()
        cls.conn_pool_patcher.stop()

class CRUDTests(BaseTestCase):

    def test_widgets_crud(self):
        # empty out all widgets
        req = Request(
            method='DELETE',
            path='/widgets',
            headers={
                'Authorization': f'Basic {self.DUMMY_BASIC_CREDS}'
            },
            body=b''
        )

        res = self.app.handle_request(req)

        self.assertEqual(res.status, 204)
        
        # get all widgets while empty
        req = Request(
            method='GET',
            path='/widgets',
            headers={
                'Authorization': f'Basic {self.DUMMY_BASIC_CREDS}'
            },
            body=b''
        )

        res = self.app.handle_request(req)

        self.assertEqual(res.status, 200)
        self.assertEqual(res.body, b'[]')
        
        # put several widgets
        payload = json.dumps([
            {
                'id': 1,
                'name': 'car',
                'description': 'a car'
            },
            {
                'id': 2,
                'name': 'cdddr',
                'description': 'remember LISP?'
            }
        ]).encode('utf-8')
        req = Request(
            method='PUT',
            path='/widgets',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Basic {self.DUMMY_BASIC_CREDS}'
            },
            body=payload
        )

        res = self.app.handle_request(req)

        self.assertEqual(res.status, 200)
        self.assertEqual(res.body, payload)

        # get all widgets
        req = Request(
            method='GET',
            path='/widgets',
            headers={
                'Authorization': f'Basic {self.DUMMY_BASIC_CREDS}'
            },
            body=b''
        )

        res = self.app.handle_request(req)

        self.assertEqual(res.status, 200)
        self.assertEqual(res.body, payload)

        # delete all widgets
        req = Request(
            method='DELETE',
            path='/widgets',
            headers={
                'Authorization': f'Basic {self.DUMMY_BASIC_CREDS}'
            },
            body=b''
        )

        res = self.app.handle_request(req)

        self.assertEqual(res.status, 204)

        # get all widgets again
        req = Request(
            method='GET',
            path='/widgets',
            headers={
                'Authorization': f'Basic {self.DUMMY_BASIC_CREDS}'
            },
            body=b''
        )

        res = self.app.handle_request(req)

        self.assertEqual(res.status, 200)
        self.assertEqual(res.body, b'[]')

    def test_widget_crud(self):
        # empty out all widgets
        req = Request(
            method='DELETE',
            path='/widgets',
            headers={
                'Authorization': f'Basic {self.DUMMY_BASIC_CREDS}'
            },
            body=b''
        )

        res = self.app.handle_request(req)

        self.assertEqual(res.status, 204)

        # try to get non-existant widget
        req = Request(
            method='GET',
            path='/widgets/1',
            headers={
                'Authorization': f'Basic {self.DUMMY_BASIC_CREDS}'
            },
            body=b''
        )

        res = self.app.handle_request(req)

        self.assertEqual(res.status, 404)

        # put in a new widget

        payload = json.dumps({
            'id': 1,
            'name': 'car',
            'description': 'a car'
        }).encode('utf-8')
        req = Request(
            method='PUT',
            path='/widgets/1',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Basic {self.DUMMY_BASIC_CREDS}'
            },
            body=payload
        )

        res = self.app.handle_request(req)

        self.assertEqual(res.status, 200)
        self.assertEqual(res.body, payload)

        # get said new widget
        req = Request(
            method='GET',
            path='/widgets/1',
            headers={
                'Authorization': f'Basic {self.DUMMY_BASIC_CREDS}'
            },
            body=b''
        )

        res = self.app.handle_request(req)

        self.assertEqual(res.status, 200)
        self.assertEqual(res.body, payload)


        # delete said new widget
        req = Request(
            method='DELETE',
            path='/widgets/1',
            headers={
                'Authorization': f'Basic {self.DUMMY_BASIC_CREDS}'
            },
            body=b''
        )

        res = self.app.handle_request(req)

        self.assertEqual(res.status, 204)

        # try deleting now non-existant widget
        req = Request(
            method='DELETE',
            path='/widgets/1',
            headers={
                'Authorization': f'Basic {self.DUMMY_BASIC_CREDS}'
            },
            body=b''
        )

        res = self.app.handle_request(req)

        self.assertEqual(res.status, 404)

        # try getting the now deleted widget
        req = Request(
            method='GET',
            path='/widgets/1',
            headers={
                'Authorization': f'Basic {self.DUMMY_BASIC_CREDS}'
            },
            body=b''
        )

        res = self.app.handle_request(req)

        self.assertEqual(res.status, 404)


class BadRequestTests(BaseTestCase):
    def test_no_matching_path(self):
        req = Request(
            method='GET',
            path='/waaaaaaaaaaaaaaa',
            headers={
                'Authorization': f'Basic {self.DUMMY_BASIC_CREDS}'
            },
            body=b''
        )

        res = self.app.handle_request(req)

        self.assertEqual(res.status, 404)

    def test_bad_method(self):
        req = Request(
            method='PATCH',
            path='/widgets',
            headers={
                'Authorization': f'Basic {self.DUMMY_BASIC_CREDS}',
                'Content-Type': 'application/json'
            },
            body=b'fjhfjfh'
        )

        res = self.app.handle_request(req)

        self.assertEqual(res.status, 405)

    def test_missing_auth_credentials(self):
        req = Request(
            method='GET',
            path='/widgets',
            headers={},
            body=b''
        )

        res = self.app.handle_request(req)

        self.assertEqual(res.status, 401)

    def test_unauthentication_failure(self):
        req = Request(
            method='GET',
            path='/widgets',
            headers={
                'Authorization': f'Basic {self.DUMMY_BASIC_CREDS}'
            },
            body=b''
        )

        with self.app.basic_auth.auth_provider.triggered_failure():
            res = self.app.handle_request(req)

        self.assertEqual(res.status, 401)

    def test_bad_content_type(self):
        payload = json.dumps({
            'id': 1,
            'name': 'car',
            'description': 'a car'
        }).encode('utf-8')
        req = Request(
            method='PUT',
            path='/widgets/1',
            headers={
                'Authorization': f'Basic {self.DUMMY_BASIC_CREDS}',
                'Content-Type': 'application/xml'
            },
            body=payload
        )

        res = self.app.handle_request(req)

        self.assertEqual(res.status, 415)

    @mock.patch('helpers.dal.WidgetStore.get_widgets')
    def test_unexpected_server_error(self, mock_get_widget):
        mock_get_widget.side_effect = [Exception]

        req = Request(
            method='GET',
            path='/widgets',
            headers={
                'Authorization': f'Basic {self.DUMMY_BASIC_CREDS}'
            },
            body=b''
        )

        res = self.app.handle_request(req)

        self.assertEqual(res.status, 500)
