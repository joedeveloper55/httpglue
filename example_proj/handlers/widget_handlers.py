from httpglue import Response

from models.widgets import Widget


def get_widget(app, req):
    app.basic_auth.authenticate(req)

    widget_id = int(req.path_vars['id'])
    try:
        widget = app.widget_store.get_widget(widget_id)
    except LookupError:
        return app.content_types.create_response(
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
    widget_data = widget.to_dict()
    return app.content_types.create_response(
        status=200,
        headers={
            'Content-Type': 'application/json'
        },
        data=widget_data
    )


def put_widget(app, req):
    app.basic_auth.authenticate(req)

    widget_data = app.content_types.deserialize_body(
        ['application/json'],
        req
    )

    widget = Widget.from_dict(widget_data)
    if int(req.path_vars['id']) != widget.id:
        return app.content_types.create_response(
            status=400,
            headers={
                'Content-Type': 'application/json'
            },
            body={
                'error': 'bad request',
                'status': 400,
                'details': 'widget id in body conflicted with request path'
            }
        )
    app.widget_store.put_widget(widget)
    return app.content_types.create_response(
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
        app.widget_store.del_widget(widget_id)
    except LookupError:
        return app.content_types.create_response(
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
