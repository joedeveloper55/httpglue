# httpglue

httpglue is a *very* minimal, *very* explicit, and *very* transparent python http application framework optimized for building small http microservices deployable as wsgi or asgi apps.

It is an exercise in pushing simple to its limits while still providing enough structure and functionality to be useful. It is a kind of 'nanoframework' if you will, taking simplicity and minimalism a bit further than the typical 'microframework'.

The api only defines four classes: App, Headers, Req and Res (technically there's one more, an App-like object for defining an asgi app, but the interface is more or less exactly like the wsgi one)

There are no dependencies on any third party libraries. The standard library is all that is required.
It is 100% pure python. It will work wherever you have a recent enough (3.6 or greater) python installation.

httpglue is also an exercise in pushing explicitness and transparency to it's limits. httpglue never sends back a response that has not been specified by the application programmer. The application programmer explicitly codes for all error conditions and specifies a static default error response for cases that were not anticipated or handled.

To quickly get the flavor of httpglue, take a look at the below hello_world.py example:

```
import logging

from httpglue import Req, Res
from httpglue.wsgi import App
from httpglue.exceptions import NoMatchingPathError
from httpglue.exceptions import NoMatchingMethodError


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = App(
    logger=logger,
    default_fallback_err_res=Res(
        status=500,
        headers={},
        body=b'500 Internal Server Error'
    )
)

@app.endpoint({'GET'}, '/hello')
def get_hello_handler(req):
    return Res(
        status=200,
        headers={},
        body=b'Hello world!'
    )

@app.err_handler([NoMatchingPathError])
def handle_no_matching_path(e, req):
    return Res(
        status=404,
        headers={},
        body=b'404 Not Found'
    )


@app.err_handler([NoMatchingMethodError])
def handle_no_matching_method(e, req):
    return Res(
        status=405,
        headers={
            'Allow': ','.join(e.allowed_methods)
        },
        body=b'405 Method Not Allowed'
    )
```

If you simply copy this to a file named "my_app.py" and run it with 

> pip install httpglue; pip install gunicorn; gunicorn my_app:app

you can actually play around with this example with no other steps. An http application is now servicing http requests at localhost:8000.

As mentioned above, httpglue supports asgi as well as wsgi. Here's a simple eqivalent asgi app:
```
import logging

from httpglue import Req, Res
from httpglue.asgi import App
from httpglue.exceptions import NoMatchingPathError
from httpglue.exceptions import NoMatchingMethodError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = App(
    logger=logger,
    default_fallback_err_res=Res(
        status=500,
        headers={},
        body=b'500 Internal Server Error'
    )
)

@app.endpoint({'GET'}, '/hello')
async def get_hello_handler(req):
    return Res(
        status=200,
        headers={},
        body=b'Hello world!'
    )

@app.err_handler([NoMatchingPathError])
async def handle_no_matching_path(e, req):
    return Res(
        status=404,
        headers={},
        body=b'404 Not Found'
    )


@app.err_handler([NoMatchingMethodError])
async def handle_no_matching_method(e, req):
    return Res(
        status=405,
        headers={
            'Allow': ','.join(e.allowed_methods)
        },
        body=b'405 Method Not Allowed'
    )
```

This asgi example is almost an exact copy of the wsgi example, the only differences being that we imported the App class out of httpglue.asgi rather than httpglue.wsgi and that we register async functions to endpoints and err_handlers rather than regular functions.

you can copy this into a file named "my_async_app.py" and simply run it with:

> pip install httpglue; pip install uvicorn; uvicorn my_async_app:app

If you want to know more, check out [our documentation](https://github.com/joedeveloper55/httpglue/DOCUMENTATION.md).

Also, For more robust examples that showcase how you can leverage httpglue to build more serious http applications, check out:

* [a rapid prototype of a simple json api for performing CRUD with one resource, single threaded and with no backing services]()
* [the same simple json api for performing CRUD with one resource, but as an async app, with dynamodb and sns as backing services]()
* [the same api as above, but this time it's an xml api, multi-threaded and with postgres as a backing service, and with some auth logic]()

## Author

* Joseph P McAnulty
