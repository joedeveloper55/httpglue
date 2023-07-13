from httpglue import Response

from models.widgets import Widget


def get_widgets(app, req):
    app.basic_auth.authenticate(req)

    widgets = app.widget_store.get_widgets()

    widgets_data = [w.to_dict() for w in widgets]

    return app.content_types.create_response(
        status=200,
        headers={
            'Content-Type': 'application/json'
        },
        data=widgets_data
    )


def put_widgets(app, req):
    app.basic_auth.authenticate(req)

    widgets_data = app.content_types.deserialize_body(
        ['application/json'],
        req
    )

    widgets = [Widget.from_dict(wd) for wd in widgets_data]

    app.widget_store.put_widgets(widgets)

    return app.content_types.create_response(
        status=200,
        headers={
            'Content-Type': 'application/json'
        },
        data=widgets_data
    )


def del_widgets(app, req):
    app.basic_auth.authenticate(req)

    app.widget_store.del_widgets()

    return Response(
        status=204,
        headers={},
        body=b''
    )
