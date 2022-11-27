# Tutorial

Welcome to the httpglue tutorial. This tutorial aims to introduce you to the key concepts and features of httpglue, giving you a nice big picture view of the framework. It should be about a 30 minute to 1 hour read for most.

If you're already familiar with the frameowrk and just need an api refresher or api details, [go over to the api docs](https://github.com/joedeveloper55/httpglue/blob/master/API_DOCUMENTATION.md)

The examples here are very trite. This is intentional. Simpler examples make for better illumination of concepts for begginers. However, the examples in this tutorial are *exhaustive*: When you finish this tutorial, you will have seen all framework defined exceptions and every class with every one of its methods; You will know the entire api when done.

If more a realistic example of what an actual httpglue app could look like is what you're looking for, we refer you to:

* [reference project 1]()

Now, let's begin.

## Intro

Excluding the small handful of framework defined exceptions, httpglue has only 5 classes to know: 
* httpglue.Request - an object that represents an http request
* httpglue.Response - an object that represents an http response
* httpglue.Headers - an object representing the http headers in a request or response 
* httpglue.WsgiApp - an object representing your application. It's where you define the code that responds to http requests from clients. It is a valid wsgi application runnable in any [pep-3333](https://peps.python.org/pep-3333/) compliant wsgi server.
* httpglue.AsgiApp - an object representing your application. It's where you define the code that responds to http requests from clients. It is a valid asgi application runnable in any [asgi spec](https://asgi.readthedocs.io/en/latest/index.html)) compliant asgi server.

We'll explore these key classes with an interactive terminal session, so start up your python interpreter session if you'd like to follow along.

Let's start with getting to know the Request, Response, and Headers objects.

## The Request, Response, and Headers objects

Below we can see some simple constructions of Request, Response, and Headers objects, along with some repr strings and str strings of them.

```
>>> from httpglue import Request
>>> from httpglue import Response
>>> request = Request(method='GET', path='/hello_world', headers={}, body=b'')
>>> repr(request)
"Request(method='GET', path='/hello_world', headers={}, body=b'', host=None, port=None, proto='http', http_version=None, path_vars={}, query_str='', start_time=None)"
>>> print(str(request)) # the str of a Request object is in a loosely curl like format
GET /hello_world None


b''
```

```
>>> response = Response(status=200, headers={'Contnt-Type': 'text/plain'}, body=b'Hello World!', reason='OK') 
>>> repr(response)
"Response(status=200, headers={'Contnt-Type': 'text/plain'}, body=b'Hello World!', reason='OK')"
>>> print(str(response)) # the str of a Response object is in a loosely curl like format
HTTP 200 OK
Contnt-Type: text/plain

b'Hello World!'
```

easy access is provided to all key parts of requests and responses:

```
>>> request.method
'GET'
>>> request.path
'/hello_world'
>>> request.headers
{}
>>> request.body
b''
>>> request.query_str
''
>>> request.host  # None by default
>>> request.port  # None by default
>>> request.proto
'http'
>>> request.http_version  # None by default
>>> request.path_vars
{}
>>> request.start_time  # None by default
```

```
>>> response.status
200
>>> response.headers
{'Contnt-Type': 'text/plain'}
>>> response.body
b'Hello World!'
>>> response.reason
''
```

mutation is also allowed:

```
>>> request.query_str = 'exasperated=true'
>>> request
Request(method='GET', path='/hello_world', headers={}, body=b'', host=None, port=None, proto='http', http_version=None, path_vars={}, query_str='exasperated=true', start_time=None)
>>> response.body = b'hello world...'
>>> response
Response(status=200, headers={'Contnt-Type': 'text/plain'}, body=b'hello world...', reason='OK')
```

but the mutation is heavily validated, as is construction, to keep in conformance with the http spec
and avoid simple bugs:

```
>>> request.method = 1
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/home/joe/httpglue_public/httpglue/httpglue/__init__.py", line 42, in method
    'must be of type str, got %s' % type(value)
TypeError: method attribute of httpglue.Request object must be of type str, got <class 'int'>
>>> response.body = [1, 2, 3]
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/home/joe/httpglue_public/httpglue/httpglue/__init__.py", line 297, in body
    'must be of type bytes, got %s' % type(value)
TypeError: body attribute of httpglue.Response object must be of type bytes, got <class 'list'>
>>> Response(status='OK', headers=[], body={})
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/home/joe/httpglue_public/httpglue/httpglue/__init__.py", line 238, in __init__
    self.status = status
  File "/home/joe/httpglue_public/httpglue/httpglue/__init__.py", line 252, in status
    'must be of type int, got %s' % type(value)
TypeError: status attribute of httpglue.Response object must be of type int, got <class 'str'>
```

As you are noticing above, these are all just plain old python objects with some validated properties. There is not really any special magic around them. They just exist to represent http requests and responses.

Moving on from those, let's now move onto talking about the httpglue.wsgi.App.

## The httpglue.WsgiApp Object

The WsgiApp object represents an http app that recieves and responds to http requests. The WsgiApp object revolves around the concepts of 'endpoints' and 'error handlers'. It is in essence a container for and router to 'endpoints' and 'error handlers'. 

To construct an app object, only two parameters are required: logger and default_err_res.

```
>>> from httpglue import WsgiApp
>>> import logging
>>> app = WsgiApp(logger=logging.getLogger(__name__), default_fallback_err_res=Response(status=500, headers={}, body=b'Internal Server Error'))
```

This is a succesfully constructed app.

The logger parameter must be a python standard library logging.Logger object (or a subtype), and it is what the framework will use to log out messages about it's operations. It is also generally what your application code should use to log messages as well.

The default_err_res is a Response object. Whenever your app recieves a request that cannot be routed to an endpoint or handled in an error handler (more on these later), this is the response that will be returned. It should generally always be some sort of 500 response, and application writers should strive to write their applications so that this response is never returned. But despite our best intentions, mistakes will happen, and this parameter exists so that developers think about, know, and control beforehand what response will be returned in such a situation.

The WsgiApp object has a method, 'handle_request' which invokes the routing and handling machinery of an app. It takes a Request object, sends it into the framework, and ultimately returns an appropriate Response object.

```
>>> response = app.handle_request(Request(method='GET', path='/something', headers={}, body=b''))
No err_handler matched exception. returning default_fallback_err_response
Traceback (most recent call last):
  File "/home/joe/httpglue_public/httpglue/httpglue/wsgi.py", line 475, in handle_request
    for endpoint in self.endpoint_table
httpglue.exceptions.NoMatchingPathError: The path /something did not match any of []
>>> response
Response(status=500, headers={}, body=b'Internal Server Error', reason='')
```

Above you see that we just sent a request to our app, and got back the default_err_res, as expected, since no endpoints or err_handlers have been added yet.

> You will generally not be calling this 'handle_req' method in your application code, but you will likely use it in your unit tests, and it is helpful for situations like now where we want to interactively explore an app without starting up an http server. When your httpglue app is deployed to a wsgi server, that server will handle calling 'handle_req' for you and doing something useful with the response. More on this later.

Of course, we want our app to be able to do more than just return the default_err_res, and to do that, we need to start talking about **endpoints**.

When creating/configuring a WsgiApp object, the programmer registers 'endpoints' with it. An endpoint is defined here as some kind of functionality exposed for requests that have certain http methods and paths. For example, we may have an enpoint that simply returns a 200 OK response with the text 'Hello World' for any requests with a method of GET and a path of /hello_world.

To register/create an endpoint, three things are required: a method spec, a path spec, and a request handler.

```
>>> app.register_endpoint(['GET'], '/hello_world', lambda app, req: Response(200, {}, b'Hello World'))
<function <lambda> at 0x7fbb98d35d08>
```

Above, we can see that the form of the method spec is a list of http methods. A given method in a request matches a corresponding method spec if it is in the method_spec's list.

The path spec is a string which is a valid python re module regex, along with the special restriction that it does not start with the ^ symbol or end with the $ symbol (these are implicitly added by the framework). A given path in a request matches it's corresponding path spec string if it fully matches (i.e-- the whole entire string is matched by the spec, not just part of it).

The form of the request handler is a callable object, usually a function, which must have two positional parameters. When httpglue routes a given request to an endpoint, the request is passed as a Request object to that endpoint's request handler as the second argument. The app object itself is the first argument. The request handler must ultimately return a Response object, or raise an exxception which may perhaps be handled by an err handler (More on them later).

When we exercise our endpoint with the handle_req method, we see our expected results:

```
>>> app.handle_request(Request(method='GET', path='/hello_world', headers={}, body=b''))
Response(status=200, headers={}, body=b'Hello World', reason='')
```

Since path specs are a regex like string, it is possible to more flexibly define endpoints. For example, suppose we wanted an endpoint that could respond to more varied paths, like GET /hello/joe, GET /hello/mike, GET /hello/mary, etc. We could define such an endpoint like so:

```
>>> app.register_endpoint(['GET'], '/hello/([a-z]*)', lambda app, req: Response(200, {}, b'Hello ' + req.path_vars[0].encode('utf-8')))
<function <lambda> at 0x7fbb98bd38c8>
>>> app.handle_request(Request(method='GET', path='/hello/joe', headers={}, body=b''))
Response(status=200, headers={}, body=b'Hello joe', reason='')
>>> app.handle_request(Request(method='GET', path='/hello/mary', headers={}, body=b''))
Response(status=200, headers={}, body=b'Hello mary', reason='')
```

Note above that when we used capture groups (either named or unnamed) above in the path spec, you can access the specific captured values from a Request object's path_vars attribute, and we did use this to customize the response body based on the request path.

Sometimes, exceptional cases happen. A user makes a request and we don't have an endpoint with a matching path spec. Or a user makes a request and we have an endpoint with a matching path spec but not a matching method spec. Or a request handler throws an exception instead of returning a Response object. Or a request handler Retuns None. Or something else wierd happens. In all these cases and more, 'err handlers' come to the rescue and allow us to do something appropriate in these situations.

Now, that we know all about the WsgiApp object, endpoints, error handlers, and how things are routed, let's talk about how our WsgiApp is actually deployed to serve real http requests, because while we're sure that you find it cool to work with httpglue on the command line, you actually want to ... well..., make an http app that can actaully respond to real http requests.

## Deploying the httpglue.WsgiApp object to serve real http requests 

A WsgiApp object is a valid wsgi app (obviously...): It is a callable object with the (environ, start_response) -> Iterable[bytes] signature, as laid out in the [wsgi spec](https://peps.python.org/pep-3333/#specification-details). The __call__ method in fact handles building the Request object for representing a request, passing it to the handle_requset method for a Response object, and using that Response object to send a response back to the requester. The __call__ method is the fundamental bridge between this framework and whatever wsgi server you deploy your app to.

```
>>> import inspect
>>> inspect.signature(app.__call__)
<Signature (environ, start_response)>
```

If you know nothing about wsgi, it is well worth your time to get familiar with it and [read the wsgi spec](https://peps.python.org/pep-3333/). While it is possible to build and deploy an httpglue app without much knowledge in this area by just following examples, it will make it much harder for you to understand how to build and configure stable and performant production ready httpglue apps, and to troubleshoot certain issues when they inevitably come up. If you don't grok the spec, you won't even be able to understand how to write and deploy concurrent multi-threaded or multi-process httpglue apps. If you're serious about using httpglue for production apps, you *need* to understand wsgi on at least a basic level.

Interestingly enough, the wsgi spec leaves a lot of potential ambiguity in the deployment of a wsgi app. It does not specify how a given wsgi server must get a given wsgi app. You'll need to read the docs of the specific wsgi server you've decided to use. But to finish our tutorial on the httpglue.WsgiApp object, we'll deploy the simple below app with gunicorn as an example.

```
import logging

from httpglue import Request, Response
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
    app.logger.info('saying hello.')
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

once you copy this into some file (like my_app.py), from your terminal run (you can skip pip installing gnuicorn if you already have it)

```
$ pip install gunicorn; gunicorn my_app:make_app()
```

If you visit http://'127.0.0.1:8000/hello' in your browser. you should see the text 'Hello world!' show up in your browser.

Congrats, thats the end for the quickstart tutorial on making wsgi apps with httpglue. Now, if you're interested, we'll briefly take a look at making an asgi app with httpglue.AsgiApp. Making an asgi app is almost exactly like making a wsgi one, so this part of the tutorial will be condensed.