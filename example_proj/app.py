import logging

from httpglue.wsgi import App, Req, Res
from httpglue.exceptions import NoMatchingPathError, NoMatchingMethodError

from helpers.json import WithJsonReq, JsonRes
from helpers import dal
from models import Widget


logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

app = App(
    logger=logger,
    default_fallback_err_res=Res(
        status=500,
        headers={},
        body=b''
    )
)

widget_store = dal.WidgetStore()


@app.endpoint({'GET'}, '/widgets')
def get_widgets(req):
    widgets = widget_store.get_widgets()
    widgets_data = [w.to_ds() for w in widgets]
    return JsonRes.from_data(
        status=200,
        headers={},
        data=widgets_data
    )


@app.endpoint({'PUT'}, '/widgets')
@WithJsonReq
def put_widgets(req):
    widgets_data = req.data
    widgets = [Widget.from_ds(wd) for wd in widgets_data]
    widget_store.put_widgets(widgets)
    return JsonRes.from_data(
        status=200,
        headers={},
        data=widgets_data
    )


@app.endpoint({'DELETE'}, '/widgets')
def del_widgets(req):
    widget_store.del_widgets()
    return Res(
        status=204,
        headers={},
        body=b''
    )


@app.endpoint({'GET'}, r'/widgets/(?P<id>\d*)')
def get_widget(req):
    widget_id = int(req.path_vars['id'])
    try:
        widget = widget_store.get_widget(widget_id)
    except LookupError as e:
        return JsonRes.from_data(
        status=404,
        headers={},
        data={
            "error": "not found",
            "status": 404,
            "details": "not found"
        }
    )
    widget_data = widget.to_ds()
    return JsonRes.from_data(
        status=200,
        headers={},
        data=widget_data
    )



@app.endpoint({'PUT'}, r'/widgets/(?P<id>\d*)')
@WithJsonReq
def put_widget(req):
    widget_data = req.data
    widget = Widget.from_ds(widget_data)
    if int(req.path_vars['id']) != widget.id:
        return Res(
            status=400,
            headers={},
            body=b''
        )
    widget_store.put_widget(widget)
    return JsonRes.from_data(
        status=200,
        headers={},
        data=widget_data
    )


@app.endpoint({'DELETE'}, r'/widgets/(?P<id>\d*)')
def del_widget(req):
    widget_id = int(req.path_vars['id'])
    try:
        widget = widget_store.del_widget(widget_id)
    except LookupError as e:
        return JsonRes.from_data(
        status=404,
        headers={},
        data={
            "error": "not found",
            "status": 404,
            "details": "not found"
        }
    )
    return Res(
        status=204,
        headers={},
        body=b''
    )


@app.err_handler([NoMatchingPathError])
def handle_no_matching_path(e, req):
    return Res(
        status=404,
        headers={},
        body=b'{"error": "not found", "status": 404, "details": "not found"}'
    )


@app.err_handler([NoMatchingMethodError])
def handle_no_matching_method(e, req):
    return Res(
        status=405,
        headers={
            'Allow': ','.join(e.allowed_methods)
        },
        body=b'{"error": "method not allowed", "status": 405, "details": "method not allowed"}'
    )


@app.err_handler([Exception])
def handle_unexpected_errors(e, req):
    app.logger.exception(
        'Unexpected server error occured'
    )
    return Res(
        status=500,
        headers={},
        body=b'{"error": "internal server error", "status": 500, "details": "server error"}'
    )
