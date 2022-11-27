# httpglue

httpglue is an **extremely minimal** wsgi and asgi http application framework.

It is optimized for building small to medium sized rest apis and http microservices.

It pushes simple to its limits while still providing just enough structure and functionality to be useful. It is a kind of *nanoframework* if you will, taking simplicity and minimalism a bit further than the typical 'microframework'.

Excluding exceptions, the entire api only defines only five classes: WsgiApp, AsgiApp, Headers, Request and Response. The WsgiApp object has only 5 public methods; The AsgiApp object has only 9 public methods. The Headers, Request, and Response objects are just plain old python objects for representing http headers, http requests, and http responses, respectively.

There are no dependencies on any third party libraries. The standard library is all that is required.
It is 100% pure python. It will work wherever you have a recent enough (3.6 or greater) python installation without any hassle.

httpglue also pushes explicitness and transparency to their limits. 

It has a philosophy of *no magic*. It puts *configuration over convention*. What you see is what you get. httpglue never sends back a response that has not been specified by the application programmer. The application programmer explicitly codes for all error conditions and specifies a static default error response for cases that were not anticipated or handled. There are no implicit behind the scenes configurational defaults happening.

Becasue transparency is a central concern, the framework was designed to make apps written in httpglue as easily testable as possible from day 1 since sometimes the only way to really know what some code does is to 'test it'. It supports thorough testing of your apps regardless of the type (unit, integration, end to end, etc), testing style (mockisist vs classicist), and frameowrk (unittest, pytest, etc) you choose. It supports all of this not by providing new special test utilities of its own (since that could lock you into specific test frameworks and methedologies), but by ensuring the api itself has a design that guaruntees easy and straightforward testing.

To quickly get the flavor of httpglue, take a look at the below hello_world.py example:

```
import logging
import time

from httpglue import Response
from httpglue import WsgiApp
from httpglue import NoMatchingPathError
from httpglue import NoMatchingMethodError


def make_app():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    app = WsgiApp(
        logger=logger,
        default_fallback_err_res=Response(
            status=500,
            headers={},
            body=b'500 Internal Server Error'
        )
    )

    app.register_endpoint(
        ['GET'], '/hello',
        handle_get_hello
    )

    app.register_err_handler(
        [NoMatchingPathError],
        handle_no_matching_path
    )
    app.register_err_handler(
        [NoMatchingMethodError],
        handle_no_matching_method
    )

    return app


def handle_get_hello(app, req):
    app.logger.info('saying hello in a second.')
    time.sleep(1)
    return Response(
        status=200,
        headers={},
        body=b'Hello world!'
    )


def handle_no_matching_path(app, e, req):
    return Response(
        status=404,
        headers={},
        body=b'404 Not Found'
    )


def handle_no_matching_method(app, e, req):
    return Response(
        status=405,
        headers={
            'Allow': ','.join(e.allowed_methods)
        },
        body=b'405 Method Not Allowed'
    )
```

If you simply copy this to a file named "my_app.py" and run it with 

> pip install httpglue; pip install waitress; waitress-serve --host 127.0.0.1 --call my_app:make_app

you can actually play around with this example with no other steps. An http application is now servicing http requests at localhost:8080.

Since testing is important for this framework, here's an example of a single test case for the above app:

```
import unittest

from httpglue import Request

from my_app import make_app


class TestGetHelloEndpoint(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.app = make_app()

    def test_get_hello_endpoint(self):
        req = Request(
            method='GET',
            path='/hello',
            headers={},
            body=b''
        )

        res = self.app.handle_request(req)

        self.assertEqual(res.status, 200)
        self.assertEqual(res.body, b'Hello world!')
```

If you copy this to a file named test_my_app.py in the same directory as my_app.py you should be able to run this test with:

> PYTHONPATH=. python -m unittest test_my_app

As mentioned above, httpglue supports asgi as well as wsgi. Here's a simple eqivalent asgi app:
```
import asyncio
import logging

from httpglue import Response
from httpglue import AsgiApp
from httpglue import NoMatchingPathError
from httpglue import NoMatchingMethodError


def make_app():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    app = AsgiApp(
        logger=logger,
        default_fallback_err_res=Response(
            status=500,
            headers={},
            body=b'500 Internal Server Error'
        )
    )

    async def startup_routine(app):
        app.logger.info('ready to serve requests in 2 seconds.')
        await asyncio.sleep(2)
        app.logger.info('ready now.')

    app.register_startup_routine(startup_routine)

    async def shutdown_routine(app):
        app.logger.info('shutting down in 2 seconds.')
        await asyncio.sleep(2)
        app.logger.info('shutdown successful.')

    app.register_shutdown_routune(shutdown_routne)

    app.register_endpoint(
        ['GET'], '/hello',
        handle_get_hello
    )

    app.register_err_handler(
        [NoMatchingPathError],
        handle_no_matching_path
    )
    app.register_err_handler(
        [NoMatchingMethodError],
        handle_no_matching_method
    )

    return app


async def handle_get_hello(app, req):
    app.logger.info('saying hello in a second.')
    await asyncio.sleep(1)
    return Response(
        status=200,
        headers={},
        body=b'Hello world!'
    )


async def handle_no_matching_path(app, e, req):
    return Response(
        status=404,
        headers={},
        body=b'404 Not Found'
    )


async def handle_no_matching_method(app, e, req):
    return Response(
        status=405,
        headers={
            'Allow': ','.join(e.allowed_methods)
        },
        body=b'405 Method Not Allowed'
    )
```

you can copy this into a file named "my_async_app.py" and run it with:

> pip install httpglue; pip install uvicorn; uvicorn my_async_app:make_app()

And here's a sample test case for your asgi app:

```
import asyncio
import unittest

from httpglue import Request

from my_async_app import make_app


class TestGetHelloEndpoint(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.event_loop = asyncio.new_event_loop()

        self.app = make_app()

        self.event_loop.run_until_complete(
            self.app.startup()
        )

    @classmethod
    def tearDownClass(self):
        self.event_loop.run_until_complete(
            self.app.shutdown()
        )

        self.event_loop.close()

    def test_get_hello_endpoint(self):
        req = Request(
            method='GET',
            path='/hello',
            headers={},
            body=b''
        )

        res = self.event_loop.run_until_complete(
            self.app.handle_request(req)
        )

        self.assertEqual(res.status, 200)
        self.assertEqual(res.body, b'Hello world!')
```

Assuming you placed this in a file named test_my_async_app.py in the same directory as my_async_App, you can run this with:

> PYTHONPATH=. python -m unittest test_my_async_app

As you can see above, this asgi example is almost an exact copy of the wsgi example, the only differences being that:

  1. we registered async functions to endpoints and err_handlers rather than regular functions.

  2. we registered a "startup_routine" async function and a "shutdown_routine" async function with the app (generally, this is needed for initializing and shutting down async helpers in asgi applications, such as an async pool of database connections)

  3. the "startup" and "shutdown" async methods are exposed for running the startup and shutdown code in your unit tests, and the handle_request method is now async

If you want to know more, check out [our comprehensve documentation](https://github.com/joedeveloper55/httpglue/blob/master/API_DOCUMENTATION.md).

Also, For more robust examples that showcase how you can leverage httpglue to build more serious http applications, check out:

* [The official httpglue wsgi exemplar project]() - An exemplar halfway between a trite "hello world" exemplar and a real application. It is a simple CRUD-type json rest api for a single resource that persists data to postgres, authenticates users via basic auth, and leverages a thread pool for its database connections. It also comes with thorough unit tests. This is the best place to go to learn the idiomatic structure of an httpglue wsgi application and idiomatic patterns for testing such an application.   

* [The official httpglue asgi exemplar project]() - An exemplar just like the above wsgi one, except it leverages python's async features. This is the best place to go to learn the idiomatic structure of an httpglue asgi apllication and idiomatic patterns for testing such an application.   

## Authors

* Joseph P McAnulty
