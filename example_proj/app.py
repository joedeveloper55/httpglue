import logging
import json

from httpglue import Request, Response
from httpglue import WsgiApp
from httpglue import NoMatchingPathError, NoMatchingMethodError

from handlers import widget_handlers
from handlers import widgets_handlers
from helpers import auth
from helpers import content_types
from helpers import dal


def make_app():

    # create app object
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    app = WsgiApp(
        logger=logger,
        default_fallback_err_res=Response(
            status=500,
            headers={},
            body=b''
        )
    )

    # set up and initialize needed resources and helpers
    app.content_types = content_types.ContentHelper()
    app.content_types.add_support(
        mime_type='application/json',
        serializer=(lambda data: json.dumps(data).encode('utf-8')),
        deserializer=(lambda data: json.loads(data.decode('utf-8')))
    )

    app.basic_auth = auth.DummyBasicAuthHelper(
        trust=True
    )

    app.widget_store = dal.WidgetStore()

    # register endpoints
    app.register_endpoint(
        ['GET'], '/widgets',
        widgets_handlers.get_widgets
    )
    app.register_endpoint(
        ['PUT'], '/widgets',
        widgets_handlers.put_widgets
    )
    app.register_endpoint(
        ['DELETE'], '/widgets',
        widgets_handlers.del_widgets
    )
    app.register_endpoint(
        ['GET'], r'/widgets/(?P<id>\d*)',
        widget_handlers.get_widget
    )
    app.register_endpoint(
        ['PUT'], r'/widgets/(?P<id>\d*)',
        widget_handlers.put_widget
    )
    app.register_endpoint(
        ['DELETE'], r'/widgets/(?P<id>\d*)',
        widget_handlers.del_widget
    )

    # register err_handlers
    app.register_err_handler(
        [NoMatchingPathError],
        handle_no_matching_path
    )
    app.register_err_handler(
        [NoMatchingMethodError],
        handle_no_matching_method
    )
    app.register_err_handler(
        [content_types.UnsupportedContentTypeError],
        handle_unsupported_content_type_errors
    )
    app.register_err_handler(
        [auth.AuthenticationError],
        handle_unauthenticated_errors
    )
    app.register_err_handler(
        [Exception],
        handle_unexpected_errors
    )

    return app


def handle_no_matching_path(app, e, req):
    return app.content_types.make_response(
        status=404,
        headers={
            'Content-Type': 'application/json'
        },
        data={
            "error": "not found",
            "status": 404,
            "details": "not found"
        }
    )


def handle_no_matching_method(app, e, req):
    return app.content_types.make_response(
        status=405,
        headers={
            'Content-Type': 'application/json',
            'Allow': ','.join(e.allowed_methods)
        },
        data={
            "error": "method not allowed",
            "status": 405,
            "details": "method not allowed"
        }
    )


def handle_unauthenticated_errors(app, e, req):
    print(e.details)
    return app.content_types.make_response(
        status=401,
        headers={
            'Content-Type': 'application/json',
            'WWW-Authenticate': 'Basic realm="User Visible Realm", charset="UTF-8"'
        },
        data={
            "error": "unauthenticated",
            "status": 401,
            "details": "unauthenticated"
        }
    )


def handle_unsupported_content_type_errors(app, e, req):
    details = (
        f"the request's content type of '{e.req_ct_type}' "
        f"was not one of {e.supported_content_types}"
    )

    return app.content_types.make_response(
        status=415,
        headers={
            'Content-Type': 'application/json'
        },
        data={
            "error": "unsupported content type",
            "status": 415,
            "details": details
        }
    )


def handle_unexpected_errors(app, e, req):
    app.logger.exception(
        'Unexpected server error occured'
    )

    return app.content_types.make_response(
        status=500,
        headers={
            'Content-Type': 'application/json'
        },
        data={
            "error": "internal server error",
            "status": 500,
            "details": "server error"
        }
    )
