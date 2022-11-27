# Best practices and idioms for httpglue users

## Best practices for running in production
  
  * Do not enable debug level logs in production. These logs are incredibly verbose, logging all requests in full and all responses in full. This is concerning from a security perspective. Your logs will almost certainly be a goldmine of sensitive information. Additionally though, the sheer volume of logging generated when using debug level logs in production may also be a problem and stress your logging infrastructure. The debug level logs are there to help developers debug locally or in less important deployment regions, but should generally always be avoided in production. Setting your app's logging level to Info level logs will generally strike a good balance between logging enough information to provide sufficient transparency while also not overly stressing a logging infrastructure or logging to much sensitve information.

  * Know your wsgi or asgi server, or find someone who does. httpglue is the application part of either a running wsgi or asgi service. A decent portion of the behavior, reliability, and performance will be dependent on the tuning/configuration of the wsgi/asgi server you're using to run it.

## Put commonly needed resources and config directly on the app object

Since the app object is a python object, you can add as many additional properties to it dynamically as you want after instantiation. Do not be afraid to do so. This is the place to put commonly needed resources such as a pool of database connections, application wide custom config, useful helper functions or objects, a data access layer object, etc when you initially create your app object.

The app object is injected into every request handler and error handler as the first argument, which makes everything you've put on the app object available to your request handlers and error handlers regardless of how you choose to organize your code.

While I admit that this is a rather odd idiom, especially to those coming from other languages without objects that allow you to just stuff new properties on them after creation, It just simply works. 

See [the refenrence example]() for instance: It is possible to test in isoltion easily and to modify basic configuration for tests. It would be possible to change the persitance layer from redis to postgres without modifying anything but the dal module and a few lines in the app module. It is easy enough to understand at a glance. While wierd, this idiom is simple and pragmatic.

You may think the app object becomes a god object in this case, but it is no more of a god object than the typical ioc container, as long as you're just using it as a place to store self contained helpers and utilities that do not directly refer back to the app object itself. Think of it as a simple namespace that happens to be injected into your handlers. [the refenrence example]() highlights this usage well. Note how all the helper's we've added to the app object (x, y, and z) are self contained units of functionaity. They don't themselves refer back to the app object.

## Use the WsgiApp and AsgiApp object's handle_req method for fluent unit tests

Both the httpglue.WsgiApp object and the httpglue.AsgiApp object expose a
'handle_req' method that takes a Request object, routes it thorough your app, invokes handlers, and
returns a Response object.

While you will seldom if ever use the handle_req directly in application code, it is the main
tool at your disposal for writing fluent and idiomatic unit tests with httpglue.

Basically, to write your unit tests, you construct the app object representing
your application (possibly with some things in it mocked, stubbed, or faked out), and then in your unit tests you construct Request objects, pass them into this handle_req method, and then validate the returned Response object. No wsgi or asgi setup or specific logic is required when unit testing this way. See [an example of httpglue unit testing here](https://github.com/joedeveloper55/httpglue/blob/master/example_proj/tests/test_app.py)

Thanks to the handle_req method, you can chose whatever unit testing framework, and even style, you prefer (unittest, pytest, etc). httpglue forces nothing on you with regards to testing frameworks or testing methodologies.

## Use application factories
An application factory is ___.

You can see [an example of an application factory here](). The make_app function is the application factory. In fact, every official example app you see in this project uses the application factory pattern.

Not using an application factory generally means instantiating and initializing your app at module import time. If you have a non trivial app that is making database connections at startup, that means the ability to even import the app may now be dependent on connecting to a database. Merely importing the app now both causes and depends on side effects from a system outside of itself.

Side effects from importing modules beyond having some functions or classes defined is a generally bad practice. You can read about why in many other places on the internet. I'll just briefly mention  two reasons why you don't want to cause side effects during module import time here.

1. Your application's functioning may start to depend on import order. This will make your code brittle and harder to change, re-organize, and refactor.

2. Mocking out dependencies for testing will become very hard. Generally a module needs to be imported before you can start mocking out entities in it, even with the power of monkeypatching. What if you want to mock out database behaviors, because it's too much trouble to actually run the database locally? You won't be able to do this in a sensible and simple way if you didn't use an application factory, even with python's phenomenal utilities in the unittest.mock library.

## Avoid using predicate routing. If you can't, follow these tips:

Modern apis should generally have their endpoints be defined based on http method and path structure (this is often called a RESTful design). We believe this is the case at least 99% of the time, and maybe more. That means predicate routing will not be needed for most apps, especially new ones.

predicate routing is powerful; with it you can route off of absolutely anything you would like: an http header, a query string param, something in the request body, or even a random number generator. But it is crude and primitive. It is easy to make mistakes and introduce bugs with it. It is a feature which can very easily be abused without discipline and foresight on the part of the programmer using it.

It was a compromise between keeping the framework powerful and flexible but still very simple in nature for the average use case (simple rest apis). A more elegant routing primitive could have been included but we deemed the extra complexity introduced not worth it, especially since the overwhelming majority of apps would not require such flexible routing in the first place.

Unless you really need it, do not use this feature.

But what if you run into one of the few rare cases where you can't really seperate your http service's behavior into multiple endpoints based off of http method and path?

For instance, let's say you're rewriting a legacy bash and c cgi script with python to keep up with new company standards, and you want to use httpglue. Let's say that as part of this re-write, strict backwards compatibility is required. You can't change the existing api exposed by the cgi script as part of your re-write. Let's also say that this existing api exposes all the functionality at POST /execute, and which type of thing executes depends entirely on supplied query parameters (we've seen such apis in the wild, so don't laugh). In this case you would want to define enpoints based on query parameters.

The predicate routing feature would enable you to do this. You can see a detailed example and explanation of predicate routing in our [predicate routing how-to doc]()

If you must use the feature, such as in a use case like this, follow these tips:

* use pred functions only for routing. since a pred is a just a function that takes a Request object and returns a bool, you can do many clever things with them. You could modify the req object, raise exceptions, maybe try to do authentication and authorization in these. Do not do any of this. You will regret it. Those sorts of things belong in your handlers. You have been warned...

* don't ever do IO (read/write from a database or file) in a pred function. These need to be deterministic, simple and reliable. IO is none of those things. You have been warned...

* these should not throw exceptions. They may throw an expection, and an exception thrown by these can even be routed to an error handler, but just because they can does not mean they should. Try very hard to write pred functions that 'cannot' throw an exception, otherwise your app's routing flow will be much harder to understand.

* test request routing harder than normal if you use these. They can be tricky to get right.

## FAQs

### why is it called httpglue?

When discussing code, some code gets classified as 'glue code': code who's primary responsibility is functioning as a layer of 'glue' between different pieces of code and functionality, integrating things together.

Microservices, generally by definition, are meant to be self contained units of functionality that have to be 'integrated' or 'glued together' to accomplish substantial functionality or build a product. http is often a common choice for enabling microservices to communicate with each other or have their functionalites integrated into other systems.

Since httpglue exists to handle the http part of an http microservice, and nothing else, it kind of functions as a sort of 'glue code', hence the name 'httpglue'.

### how do I write concurrent threaded wsgi apps with httpglue?

the httpglue.wsgi.App object is just code to route some requests to handlers, represent http requests and responses, provide some basic code organization, and abstract away wsgi stuff. It doesn't have any features related to concurrency. Actually, the wsgi spec iteslf explicitly does not have any specifications as to how concurrency is handled in a wsgi application:

https://peps.python.org/pep-3333/#thread-support

According to the wsgi spec, this is entirely left up to the wsgi server running the wsgi app.

This does not mean you can't write httpglue apps that use threads (indeed, see [one of our reference examples]() for code that actually uses threads and connection pooling), It just means that all of that depends on the wsgi server you choose and how it's configured.

### How can I make https apis with httpglue?

In short, you can't; At least not directly. Only http is supported. You can however put a reverse proxy like nginx or an api gateway like kong in front of your httpglue applications. This is in fact a common and beneficial practice, keeping your applications simple and centralizing the management of security an other concerns in a single place.

### why doesn't httpglue have feature X? Can we have it added in?

httpglue is a 'nanoframework', a framework intended to be even smaller than most popular microframeworks. Each additional feature takes it further and further away from this concept, which is the key idea that the entire framework was designed around. In this sense, each feature is as much a liability as it is an asset.

The simplicity of the framework enables developer flexibility, freedom, and creativity, and the chance to keep an app simple when that's all it needs to be. The minimalism and explicitness of the framework gives developers as much room as possible to customize their app to be exactly as they'd like it. The simplicity and smallness of the framework enables full learning of framework behavior at a rapid pace for even moderately experienced Python programmers.

Every individual and team will not have the needs or desires that this framework satisifies, and that is okay, but they should choose a different framework in that case. The designers of httpglue do not believe that we can achieve both a framework this small and simple that also caters to every need. Our stance is very strong on this point, and additional features will almost never be added in.

### Looking for contributers?

We doubt the core of httpglue (this repo) will ever grow and aquire new features (The only one we're considering is adding websockets support). While we do try to keep an open mind, it is our top priority to keep the featureset and api of this framework as small as is possible, so new feature contributions are generally not a consideration. There is a strong bias for less rather than more. This all means that ultimately, We're not looking for additional contributers at this time.

However, if you wish to contribute to httpglue, there is another, better way to contribute to httplglue without being a contributer to the core project. The best way to contribute is not to work on this core project but to actually create your own projects that are built to work nicely with or extend httpglue. In this fasion, you're contributing to the 'httpglue ecosystem'. If you want to associate them with the project feel free to add the "Framework :: httpglue" classifier. See [httpglue_content_types]() as a prime example of what one of the extensions may look like and [the reference project]() for an example of how it is used.

These kinds of contributions are of incredible value to the project. httpglue does so little on it's own; As much as this is its primary strength, it is also its primary weakness. A strong ecosystem where people can handpick out the specific extensions and tools they need will go a long way towards making httpglue more productive and enjoyable to use.

This is 'horizontally scaled' open source, using more brains to make and manage more projects rather than more brains to grow and manage one project.

### Okay, so how do I write an extension?

xxx there's nothing special, just use python. the python language itself is the extesion method. there's no special extension api or mechanisms. however see the content_Types_helper, or the basic_auth helper to get a feel for how we envision extensions will/should look. Note how they don't even interact or hook into httpglue itself at all: they're just a useful object we instantiated at app startup time and plopped on the app object. That's all extensions should be, useful, generic python objects.