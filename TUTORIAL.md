# Tutorial

Welcome to the httpglue tutorial. This tutorial aims to introduce you to the key concepts and features of httpglue, giving you a nice big picture view of the framework.

If you're already familiar with the frameowrk and just need an api refresher, [go over to the api docs](https://github.com/joedeveloper55/httpglue/blob/master/API_DOCUMENTATION.md)

The examples here are very trite. This is intentional. Simpler examples make for better illumination of concepts for begginers. If more realistic examples of what actal httpglue apps could look like are what you're looking for, we refer you to:

* a
* b
* c

Now, let's begin.

Excluding the small handful of framework defined exceptions, httpglue has 5 key classes to know: 
* httpglue.Req - an object that represents an incoming http request
* httpglue.Res - an object that represents an outgoing http response sent back to a client
* httpglue.headers - an object representing the http headers in a request or response 
* httpglue.wsgi.App - an object representing your application. It's where you define the code that responds to http requests from clients. It is a valid wsgi application runnable in any pep-3333 compliant wsgi server.
* httpglue.asgi.App - an object representing your application. It's where you define the code that responds to http requests from clients. It is a valid asgi application runnable in any pep-xxxx compliant asgi server.

Let's start with getting to know the Req, Res, and Headers objects.

Below we can see some simple constructions and mutations of Req, Res, and Headers objects, along with some repr strings and str strings of them.

```
```

easy access is provided to key parts of requests and responses:
```
```

mutation is also allowed:
```
```

but the mutation is heavily validated, as is construction, to keep in conformance with the http spec:
```
```

httpglue's Req, Res, and Headers objects were designed to be 'correct by definition'. If it exists, it is valid.

As you are noticing above, these are all just plain old python objects. There is not really any special magic around them. They just exist to represent http requests and responses.

Moving on from those, let's now move onto talking about the httpglue.wsgi.App and httphlue.asgi.App objects. We'll just focus on the httpglue.wsgi.App for now, so all future references to 'App' are refering to the httpglue.wsgi.App object. 

The App object represents an http app that recieves and responds to http requests. The App object revolves around the concepts of 'endpoints' and 'error handlers'. The App object is in essence a container for and router to 'endpoints' and 'error handlers'. 

To construct an app object, two parameters are required: logger and default_err_res.

```
```

This is a succesfully constructed app. This is actually ready to serve requests if this was deployed to a wsgi server, but currently it would only return the default_err_res for every single request made to it.

The logger parameter must be a python standard library logging.Logger object (or a subtype), and it is what the framework will use to log out messages about it's operations. It is also generally what your application code should use to log messages as well.

The default_err_res is a Res object. Whenever your app recieves a request that cannot be routed to an endpoint or handled in an error handler (more on these later), this is the response that will be returned. It should generally always be some sort of 500 response, and application writers should strive to write their applications so that this response is never returned. But despite our best intentions, mistakes will happen, and this parameter exists so that developers think about, know, and control beforehand what response will be returned in such a situation.

The App object has a convenience method, 'handle_req' which invokes the routing and handling machinery of an app. It takes a Req object, sends it into the framework, and ultimately returns an appropriate Res object. You will generally not be calling this in your application code, the __call__ method of the App object will be invoked by a wsgi server, ultimately call this handle_req method, and use the returned response to make a real http response, but this method is very useful when you're unit testing an app or in situations like now, when we want to play with an app without starting a wsgi server.

```
```

Above you see that we just sent a request to our app, and got back the default_err_res, as expected.

Of course, we want out app to be able to do more than just return the default_err_res, and to do that, we need to start talking about *endpoints*.

When creating/configuring an App object, the programmer registers 'endpoints' with it. An endpoint is defined here as some kind of functionality exposed for requests that have certain http methods and paths. For example, we may have an enpoint that simply returns a 200 OK response with the text 'Hello World' for any requests with a method of GET and a path of /hello_world.

To register/create an endpoint, three things are required: a method spec, a path spec, and a request handler.

```
```

Above, we can see that the form of the method spec and the path spec is a string which is a valid python re module regex, along with the special restriction that it does not start with the ^ symbol or end with the $ symbol. A given method or path in a request matches it's corresponding spec string if it is fully matches (i.e-- the whole entire string is matched by the spec, not just part of it) It is an error to not supply a syntactically correct method or path spec when registering an endpoint.

The form of the request handler is a callable object, usually a function, which must have only one positional parameter. It is an error to supply callables that do not meet this criteria, or objects which are not callable. When httpglue routes a given request to an endpoint, the request is passed as a Req object to that endpoint's request handler as the first and only argument. The request handler must ultimately return a Res object, or raise an exxception which may perhaps be handled by an err handler (More on them later).

The syntax above of using the 'endpoint' decorator is an api convenience. endpoints can be alternatively registered using the register_endpoint method of the App object. This alternative syntax becomes increasingly beneficial as your app gets larger and when you start wanting to split request handlers out into different files.

```
```

When we exercise our endpoint with the handle_req method, we see our expected results:

```
```

Since method specs and path specs are a regex like string, it is possible to more flexibly define endpoints. For example, suppose we wanted an endpoint that could respond to more varied paths, like GET /hello/joe, GET /hello/mike, GET /hello/mary, etc. We could define such an endpoint like so:

```
```

Furthermore, note above that when you use capture groups (either named or unnamed) in a path spec, you can access the specific captured values from a Req object's path_vars attribute.

Sometimes, exceptional cases happen. A user makes a request and we don't have an endpoint with a matching path spec. Or a user makes a request and we have an endpoint with a matching path spec but not a matching method spec. Or a request handler throws an exception instead of returning a Res object. Or a request handler Retuns None. Or something else wierd happens. In all these cases and more, 'err handlers' come to the rescue and allow us to do something appropriate in these situations.

Now, that we know all about endpoints and error handlers, and how things are routed, let's talk about how our App is actually deployed to serve real http requests.

An App object is a valid wsgi app:. It is a callable object with the (environ, start_Response) -> Iterable[bytes] signature, as laid out in the (wsgi spec)[___]. The __call__ method in fact handles building the Req object for representing a request, passing it to the handle_req method for a Res object, and using that Res object to send a response back to the requester. THe __call__ method is the fundamental bridge between this framework and whatever wsgi server you deploy your app to.

If you know nothing about wsgi, it is well worth your time to get familiar with it and read the spec. While it is possible to build and deploy an httpglue app without much knowledge in this area, it will make it much harder for you to understand how to build and configure stable and performant production ready httpglue apps, and to troubleshoot certain issues when they come up. If you don't grok the spec, you won't even be able to understand how to write and deploy concurrent multi-threaded or multi-process httpglue apps. If you're serious about using httpglue for production apps, you *need* to understand wsgi.

Interestingly enough, the wsgi spec leaves a lot of potential ambiguity in the deployment of a wsgi app. It does not specify how a given wsgi server must get a given wsgi app. You'll need to read the docs of the specific wsgi server you've decided to deploy. But to finish our tutorial, we'll deploy the simple below app with gunicorn as an example.

```
```

once you compy this into some file, from your terminal run

```
```

And now visit ___ in your browser. you should see __

Congrats, thats the end for the quickstart tutorial on making wsgi apps with httpglue. Now, if interested, we'll briefly take a look at making an asgi app with httpglue.