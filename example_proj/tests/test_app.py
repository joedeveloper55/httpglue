import json

import unittest
from unittest import mock

from httpglue.wsgi import Req

from app import app


class CRUDTests(unittest.TestCase):

    def test_widgets_crud(self):
        # empty out all widgets
        req = Req(
            method='DELETE',
            path='/widgets',
            headers={},
            body=b''
        )

        res = app.handle_request(req)

        self.assertEqual(res.status, 204)
        
        # get all widgest while empty
        req = Req(
            method='GET',
            path='/widgets',
            headers={},
            body=b''
        )

        res = app.handle_request(req)

        self.assertEqual(res.status, 200)
        self.assertEqual(res.body, b'[]')
        
        # put several widgets
        payload = json.dumps([
            {
                'id': 1,
                'name': 'car',
                'num_of_parts': 1
            },
            {
                'id': 2,
                'name': 'cdddr',
                'num_of_parts': 3
            }
        ]).encode('utf-8')
        req = Req(
            method='PUT',
            path='/widgets',
            headers={},
            body=payload
        )

        res = app.handle_request(req)

        self.assertEqual(res.status, 200)
        self.assertEqual(res.body, payload)

        # get all widgets
        req = Req(
            method='GET',
            path='/widgets',
            headers={},
            body=b''
        )

        res = app.handle_request(req)

        self.assertEqual(res.status, 200)
        self.assertEqual(res.body, payload)

        # delete all widgets
        req = Req(
            method='DELETE',
            path='/widgets',
            headers={},
            body=b''
        )

        res = app.handle_request(req)

        self.assertEqual(res.status, 204)

        # get all widgets again
        req = Req(
            method='GET',
            path='/widgets',
            headers={},
            body=b''
        )

        res = app.handle_request(req)

        self.assertEqual(res.status, 200)
        self.assertEqual(res.body, b'[]')

    def test_widget_crud(self):
        # empty out all widgets
        req = Req(
            method='DELETE',
            path='/widgets',
            headers={},
            body=b''
        )

        res = app.handle_request(req)

        self.assertEqual(res.status, 204)

        # try to get non-existant widget
        req = Req(
            method='GET',
            path='/widgets/1',
            headers={},
            body=b''
        )

        res = app.handle_request(req)

        self.assertEqual(res.status, 404)

        # put in a new widget

        payload = json.dumps({
            'id': 1,
            'name': 'car',
            'num_of_parts': 1
        }).encode('utf-8')
        req = Req(
            method='PUT',
            path='/widgets/1',
            headers={},
            body=payload
        )

        res = app.handle_request(req)

        self.assertEqual(res.status, 200)
        self.assertEqual(res.body, payload)

        # get said new widget
        req = Req(
            method='GET',
            path='/widgets/1',
            headers={},
            body=b''
        )

        res = app.handle_request(req)

        self.assertEqual(res.status, 200)
        self.assertEqual(res.body, payload)


        # delete said new widget
        req = Req(
            method='DELETE',
            path='/widgets/1',
            headers={},
            body=b''
        )

        res = app.handle_request(req)

        self.assertEqual(res.status, 204)

        # try deleting now non-existant widget
        req = Req(
            method='DELETE',
            path='/widgets/1',
            headers={},
            body=b''
        )

        res = app.handle_request(req)

        self.assertEqual(res.status, 404)

        # try getting the now deleted widget
        req = Req(
            method='GET',
            path='/widgets/1',
            headers={},
            body=b''
        )

        res = app.handle_request(req)

        self.assertEqual(res.status, 404)


    def test_bad_widgets_put(self):
        pass

    def test_bad_widget_put(self):
        pass

class BadRequestTests(unittest.TestCase):
    def test_no_matching_path(self):
        req = Req(
            method='GET',
            path='/waaaaaaaaaaaaaaa',
            headers={},
            body=b''
        )

        res = app.handle_request(req)

        self.assertEqual(res.status, 404)

    def test_bad_method(self):
        req = Req(
            method='PATCH',
            path='/widgets',
            headers={},
            body=b'fjhfjfh'
        )

        res = app.handle_request(req)

        self.assertEqual(res.status, 405)

    @mock.patch('helpers.dal.WidgetStore.get_widgets')
    def test_unexpected_server_error(self, mock_get_widget):
        mock_get_widget.side_effect = [Exception]

        req = Req(
            method='GET',
            path='/widgets',
            headers={},
            body=b''
        )

        res = app.handle_request(req)

        self.assertEqual(res.status, 500)
