from httpglue import Request, Response

from models import Widget


def get_widget(app, req):
    app.basic_auth.authenticate(req)

    widget_id = int(req.path_vars['id'])
    try:
        widget = app.widget_store.get_widget(widget_id)
    except LookupError as e:
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
    widget_data = widget.to_ds()
    return app.content_types.make_response(
        status=200,
        headers={
            'Content-Type': 'application/json'
        },
        data=widget_data
    )


def put_widget(app, req):
    app.basic_auth.authenticate(req)

    widget_data = app.content_types.accept(['application/json'], req)

    widget = Widget.from_ds(widget_data)
    if int(req.path_vars['id']) != widget.id:
        return app.content_types.make_response(
            status=400,
            headers={
                'Content-Type': 'application/json'
            },
            body={
                'error': 'bad request',
                'status': 400,
                'details': 'the widget id in the request body conflicted with the one in the request path'
            }
        )
    app.widget_store.put_widget(widget)
    return app.content_types.make_response(
        status=200,
        headers={
            'Content-Type': 'application/json'
        },
        data=widget_data
    )


def del_widget(app, req):
    app.basic_auth.authenticate(req)

    widget_id = int(req.path_vars['id'])
    try:
        widget = app.widget_store.del_widget(widget_id)
    except LookupError as e:
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
    return Response(
        status=204,
        headers={},
        body=b''
    )
